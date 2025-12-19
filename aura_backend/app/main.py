import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import socketio
import logging
from typing import Dict, List

from .orchestrator import Orchestrator
from .audio_modulator import AudioModulator
from pydub import AudioSegment
from .models import GameState, EmotionPayload, AudienceVote

# --- Basic Setup ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- State Management ---
orchestrator = Orchestrator()
audio_modulator = AudioModulator()
PUBLIC_BASE_URL = os.getenv("BACKEND_PUBLIC_BASE_URL", "http://localhost:8000")  # configurable for frontend
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins=[])
socket_app = socketio.ASGIApp(sio)
app.mount('/socket.io', socket_app)

# --- Paths & External Asset Mounts ---
# main.py resides at <project_root>/aura_backend/app/main.py
APP_DIR = Path(__file__).resolve().parent
BACKEND_DIR = APP_DIR.parent            # aura_backend/
PROJECT_ROOT = BACKEND_DIR.parent       # root containing game_client/
GAME_CLIENT_DIR = PROJECT_ROOT / "game_client"
GAME_STATIC_DIR = GAME_CLIENT_DIR / "static"
MUSIC_DNA_DIR = BACKEND_DIR / "music_dna_store"
GAME_TEMPLATE_FILE = GAME_CLIENT_DIR / "templates" / "game.html"

if GAME_STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(GAME_STATIC_DIR)), name="static")
else:
    logger.warning("Game static directory not found at %s - skipping static mount.", GAME_STATIC_DIR)

# Custom route to serve music files with CORS headers
@app.get("/music_dna/{file_path:path}")
async def get_music_dna(file_path: str):
    """Serve music DNA files with proper CORS headers."""
    file_path = os.path.join(MUSIC_DNA_DIR, file_path)
    if not os.path.isfile(file_path):
        return {"error": "File not found"}, 404
    
    response = FileResponse(file_path)
    # Add CORS headers explicitly for audio files
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# OPTIONS handler for CORS preflight requests
@app.options("/music_dna/{file_path:path}")
async def options_music_dna(file_path: str):
    """Handle OPTIONS requests for CORS preflight."""
    response = HTMLResponse("")
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# For backward compatibility
if MUSIC_DNA_DIR.exists():
    app.mount("/music_dna_static", StaticFiles(directory=str(MUSIC_DNA_DIR)), name="music_dna_static")
else:
    logger.warning("Music DNA directory not found at %s", MUSIC_DNA_DIR)

class ConnectionManager:
    """Tracks active WebSocket connections by role and supports targeted broadcast."""
    def __init__(self):
        self.studio_connections: List[WebSocket] = []
        self.sensor_connections: List[WebSocket] = []
        self.game_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket, connection_type: str):
        await websocket.accept()
        collection = None
        if connection_type == "studio":
            collection = self.studio_connections
        elif connection_type == "sensor":
            collection = self.sensor_connections
        elif connection_type == "game":
            collection = self.game_connections
        if collection is not None and websocket not in collection:
            collection.append(websocket)
        logger.info(f"{connection_type.capitalize()} client connected: {websocket.client}")

    def disconnect(self, websocket: WebSocket, connection_type: str):
        try:
            if connection_type == "studio" and websocket in self.studio_connections:
                self.studio_connections.remove(websocket)
            elif connection_type == "sensor" and websocket in self.sensor_connections:
                self.sensor_connections.remove(websocket)
            elif connection_type == "game" and websocket in self.game_connections:
                self.game_connections.remove(websocket)
            logger.info(f"{connection_type.capitalize()} client disconnected: {websocket.client}")
        except Exception:
            # Defensive: never let disconnect raise inside event handlers
            logger.exception("Error while disconnecting websocket")

    async def broadcast_to_studios(self, message: dict):
        dead = []
        for connection in self.studio_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            if d in self.studio_connections:
                self.studio_connections.remove(d)

    async def broadcast_to_games(self, message: dict):
        dead = []
        for connection in self.game_connections:
            try:
                await connection.send_json(message)
            except Exception:
                dead.append(connection)
        for d in dead:
            if d in self.game_connections:
                self.game_connections.remove(d)

    def summary(self) -> Dict[str, int]:
        return {
            "studios": len(self.studio_connections),
            "sensors": len(self.sensor_connections),
            "games": len(self.game_connections)
        }

manager = ConnectionManager()


# --- Game Client Serving ---
@app.get("/game", response_class=HTMLResponse)
async def read_game():
    if GAME_TEMPLATE_FILE.exists():
        try:
            return HTMLResponse(content=GAME_TEMPLATE_FILE.read_text(encoding="utf-8"), status_code=200)
        except Exception as e:
            logger.error(f"Failed reading game template: {e}")
            return HTMLResponse(content="<h2>Error loading game template.</h2>", status_code=500)
    else:
        logger.warning("Game template missing at %s", GAME_TEMPLATE_FILE)
        return HTMLResponse(content="<h2>Game client not available. (Template missing)</h2>", status_code=404)

# --- HTTP Endpoints ---
@app.post("/upload_music_dna/")
async def upload_music_dna(file: UploadFile = File(...)):
    """Upload an audio file, normalize peak to -1 dBFS if needed, and set as active DNA."""
    try:
        raw_path = os.path.join("music_dna_store", file.filename)
        with open(raw_path, "wb") as buffer:
            buffer.write(await file.read())

        # Load with pydub for normalization (supports many formats via ffmpeg if installed)
        seg = AudioSegment.from_file(raw_path)
        peak_dbfs = seg.max_dBFS  # negative number (0 is max)
        normalized_filename = f"norm_{file.filename.rsplit('.',1)[0]}.wav"
        normalized_path = os.path.join("music_dna_store", normalized_filename)
        normalized = seg
        changed = False
        # If peak lower than -2 dBFS, boost so peak is at -1 dBFS
        if peak_dbfs < -2.0:
            boost = -1.0 - peak_dbfs  # positive gain to bring peak to -1
            normalized = seg.apply_gain(boost)
            changed = True
        # Always export as 16-bit PCM wav for browser compatibility
        normalized.export(normalized_path, format="wav", parameters=["-acodec", "pcm_s16le"])

        # Point audio_modulator to normalized file
        dna_info = audio_modulator.load_dna(normalized_path)
        dna_info.update({
            "normalized": True,
            "original_peak_dbfs": round(peak_dbfs, 2),
            "normalization_applied_db": round((-1.0 - peak_dbfs) if changed else 0.0, 2),
            "serving_file": normalized_filename
        })

        await manager.broadcast_to_studios({
            "type": "dna_loaded",
            "payload": {
                "filename": normalized_filename,
                "info": dna_info
            }
        })
        return {"filename": normalized_filename, "info": dna_info}
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        return {"error": str(e)}, 500


# --- Diagnostics / Health ---
@app.get("/health")
async def health():
    """Lightweight health & connection summary for troubleshooting."""
    return {
        "status": "ok",
        "connections": manager.summary(),
        "sources_last_update": orchestrator.last_update_time,
        "current_track": audio_modulator.current_dna_file,
    }

@app.get("/debug/emotions")
async def debug_emotions():
    return {
        "final_vector": orchestrator.get_final_emotion_vector(),
        "sources": orchestrator.get_all_sources_data()
    }


# --- WebSocket Endpoints ---
@app.websocket("/ws/studio")
async def websocket_studio(websocket: WebSocket):
    await manager.connect(websocket, "studio")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "audience_vote":
                vote = AudienceVote(**data.get("payload", {}))
                orchestrator.update_audience_vote(vote.mood)
                # Immediate lightweight feedback so UI feels responsive
                await websocket.send_json({
                    "type": "vote_ack",
                    "payload": {"mood": vote.mood, "tally": orchestrator.state["audience_votes"][vote.mood]}
                })
            elif data.get("type") == "update_weights":
                orchestrator.update_weights(data.get("payload", {}))
            elif data.get("type") == "set_manual_override":
                payload = data.get("payload", {})
                orchestrator.set_manual_override(payload.get("active", False), payload.get("vector", {}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, "studio")
    except Exception as e:
        logger.error(f"Studio WebSocket error: {e}")
        manager.disconnect(websocket, "studio")

@app.websocket("/ws/sensors")
async def websocket_sensors(websocket: WebSocket):
    await manager.connect(websocket, "sensor")
    try:
        while True:
            data = await websocket.receive_json()
            source = data.get("source")
            payload = data.get("payload", {})
            
            try:
                if source == "face":
                    orchestrator.update_face_emotion(EmotionPayload(**payload))
                    # Relay frame thumbnail if present
                    frame_b64 = data.get("frame")
                    if frame_b64:
                        await manager.broadcast_to_studios({
                            "type": "face_frame",
                            "payload": {"frame": frame_b64}
                        })
                elif source == "speech":
                    orchestrator.update_speech_emotion(EmotionPayload(**payload))
            except Exception as e:
                logger.warning(f"Malformed sensor payload from {source}: {e}")
                await websocket.send_json({"type": "error", "message": "Invalid sensor payload"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, "sensor")
    except Exception as e:
        logger.error(f"Sensor WebSocket error: {e}")
        manager.disconnect(websocket, "sensor")

@app.websocket("/ws/game")
async def websocket_game(websocket: WebSocket):
    await manager.connect(websocket, "game")
    try:
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "game_state":
                game_state = GameState(**data.get("payload", {}))
                orchestrator.update_game_state(game_state)
                # Lightweight ack (throttled client-side) helps confirm flow during debugging
                await websocket.send_json({"type": "ack", "payload": {"received": True}})
    except WebSocketDisconnect:
        manager.disconnect(websocket, "game")
    except Exception as e:
        logger.error(f"Game WebSocket error: {e}")
        manager.disconnect(websocket, "game")


# --- Main Application Logic Loop ---
async def main_loop():
    logger.info("Starting AURA main loop...")
    loop_counter = 0
    while True:
        # 1. Aggregate emotions from all sources
        final_emotion_vector = orchestrator.get_final_emotion_vector()
        # 2. Modulate audio: legacy (tempo, primary_emotion) + advanced descriptor
        tempo, primary_emotion = audio_modulator.get_modulation_params(final_emotion_vector)  # smoothed
        advanced_mod = audio_modulator.compute_modulation(final_emotion_vector)

        # 3. Construct the state update payload for the studio
        tempo_multiplier = round(tempo / (audio_modulator.base_tempo or 120.0), 4)
        track_name = audio_modulator.current_dna_file or "N/A"
        track_url = None
        if audio_modulator.current_dna_file:
            track_url = f"/music_dna/{audio_modulator.current_dna_file}"
        full_track_url = f"{PUBLIC_BASE_URL}{track_url}" if track_url else None

        # Derive simple modulation hints (placeholder logic)
        # intensity = max emotion value; map to filter cutoff & gain range
        intensity_val = max(final_emotion_vector.values()) if final_emotion_vector else 0.0
        filter_cutoff = 500 + int(4500 * intensity_val)  # 500Hz to 5000Hz
        gain = 0.6 + 0.4 * intensity_val  # 0.6 to 1.0
        # Legacy simple modulation (retained) + advanced fields merged under advanced_mod
        modulation = {
            "intensity": round(intensity_val, 4),
            "filter_cutoff_hz": filter_cutoff,
            "gain": round(gain, 3),
            "advanced": advanced_mod  # new nested descriptor (non-breaking addition)
        }
        studio_update = {
            "type": "aura_update",
            "payload": {
                "final_emotion_vector": final_emotion_vector,
                "source_data": orchestrator.get_all_sources_data(),
                "audio": {
                    "tempo_bpm": tempo,
                    "tempo_multiplier": tempo_multiplier,
                    "primary_emotion": primary_emotion,
                    "current_track": track_name,
                    "track_url": track_url,
                    "full_track_url": full_track_url,
                    "base_tempo": audio_modulator.base_tempo
                    ,"modulation": modulation
                }
            }
        }
        
        # 4. Broadcast the full state to all connected studios
        await manager.broadcast_to_studios(studio_update)

        # Also push simplified directive to games (tempo + primary emotion)
        await manager.broadcast_to_games({
            "type": "aura_instruction",
            "payload": {
                "primary_emotion": primary_emotion,
                "tempo_bpm": tempo
            }
        })
        
        # 5. Send simplified instructions to the game
        # TODO: Implement crossfading or track switching in the game client
        
        # 6. Wait for the next cycle
        loop_counter += 1
        if loop_counter % 40 == 0:  # every ~20s at 2Hz
            logger.info(f"Heartbeat: connections={manager.summary()} vector={final_emotion_vector}")
        await asyncio.sleep(0.5) # Update rate of 2Hz

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(main_loop())