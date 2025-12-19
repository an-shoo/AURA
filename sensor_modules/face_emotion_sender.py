import cv2
import asyncio
import websockets
import json
import logging
from deepface import DeepFace
import time
import base64
from collections import deque
import os
logging.basicConfig(level=logging.INFO)

# --- Configuration ---
SERVER_URI = "ws://localhost:8000/ws/sensors"
# SERVER_URI = os.environ.get("AURA_BACKEND_WS_URL", "ws://localhost:8000/ws/sensors")
FACE_CASCADE = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
FRAME_RATE = 8  # Target visual frame rate sent over WS
ANALYZE_EVERY_N_FRAMES = 4  # Run DeepFace only every N frames to reduce CPU
STREAM_WIDTH = 320  # Width we will scale outgoing frame to for consistency
JPEG_QUALITY = 70  # Trade-off clarity vs bandwidth
CAMERA_INDICES = [0, 1, 2]  # Try multiple indices in case default isn't 0 (USB cams)

def open_camera():
    for idx in CAMERA_INDICES:
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            logging.info(f"Camera opened on index {idx}")
            return cap
        cap.release()
    return None

async def face_emotion_sender():
    logging.info("Attempting to connect to AURA server at %s", SERVER_URI)
    try:
        async with websockets.connect(SERVER_URI) as websocket:
            logging.info("Successfully connected to AURA server.")
            cap = open_camera()
            if not cap:
                logging.error("Cannot open any camera (tried indices %s)", CAMERA_INDICES)
                return

            # Send a handshake so backend can mark sensor as active sooner
            await websocket.send(json.dumps({"source": "face", "payload": {"emotion": "neutral", "confidence": 0.0}}))

            frame_counter = 0
            last_emotion = {"emotion": "neutral", "confidence": 0.0}
            last_box = None  # (x,y,w,h)
            fps_times = deque(maxlen=30)
            while True:
                ret, frame = cap.read()
                if not ret:
                    logging.warning("Can't receive frame (stream end?). Exiting ...")
                    break
                t_now = time.time()
                fps_times.append(t_now)
                # Basic FPS calc over recent timestamps
                if len(fps_times) >= 2:
                    fps = len(fps_times) / (fps_times[-1] - fps_times[0] + 1e-6)
                else:
                    fps = 0.0

                # Resize frame to consistent width while keeping aspect
                h, w = frame.shape[:2]
                scale = STREAM_WIDTH / float(w)
                resized = cv2.resize(frame, (STREAM_WIDTH, int(h * scale)))
                gray_resized = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

                # Detect faces on resized frame
                faces = FACE_CASCADE.detectMultiScale(gray_resized, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                # Only run heavy DeepFace every N frames if a face exists
                run_analysis = (frame_counter % ANALYZE_EVERY_N_FRAMES == 0) and len(faces) > 0
                dominant_emotion = last_emotion["emotion"]
                confidence = last_emotion["confidence"]

                if len(faces) > 0:
                    (x, y, w_box, h_box) = faces[0]
                    last_box = (x, y, w_box, h_box)
                    if run_analysis:
                        # Extract ROI from resized (convert BGR->RGB for DeepFace)
                        roi_bgr = resized[y:y+h_box, x:x+w_box]
                        roi_rgb = cv2.cvtColor(roi_bgr, cv2.COLOR_BGR2RGB)
                        try:
                            result = DeepFace.analyze(roi_rgb, actions=['emotion'], enforce_detection=False)
                            analysis = result[0] if isinstance(result, list) else result
                            dominant_emotion = analysis.get('dominant_emotion', 'neutral')
                            em_map = analysis.get('emotion', {})
                            if dominant_emotion in em_map:
                                confidence = float(em_map[dominant_emotion]) / 100.0
                            else:
                                confidence = 0.0
                            last_emotion = {"emotion": dominant_emotion, "confidence": confidence}
                        except Exception as e:
                            logging.warning("DeepFace analysis failed: %s", e)
                else:
                    # No face this frame; keep last box a few frames then clear
                    if frame_counter % (ANALYZE_EVERY_N_FRAMES * 3) == 0:
                        last_box = None

                # Draw bounding box + label if we have one
                if last_box:
                    (bx, by, bw, bh) = last_box
                    cv2.rectangle(resized, (bx, by), (bx+bw, by+bh), (120, 0, 255), 2)
                    label = f"{dominant_emotion}:{confidence*100:.1f}%"
                    cv2.putText(resized, label, (bx, max(0, by-8)), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1, cv2.LINE_AA)
                else:
                    cv2.putText(resized, "NO FACE", (8, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 1, cv2.LINE_AA)

                # Overlay FPS small
                cv2.putText(resized, f"FPS:{fps:.1f}", (8, resized.shape[0]-8), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200,200,200), 1, cv2.LINE_AA)

                # Encode full frame
                success, buf = cv2.imencode('.jpg', resized, [int(cv2.IMWRITE_JPEG_QUALITY), JPEG_QUALITY])
                frame_b64 = base64.b64encode(buf.tobytes()).decode('utf-8') if success else None

                payload = {
                    "source": "face",
                    "payload": {
                        "emotion": dominant_emotion,
                        "confidence": round(confidence, 4)
                    },
                    "frame": frame_b64,
                    "meta": {
                        "width": resized.shape[1],
                        "height": resized.shape[0],
                        "fps": round(fps, 2)
                    }
                }

                await websocket.send(json.dumps(payload))
                logging.debug(f"Sent face frame + emotion: {payload['payload']}")

                frame_counter += 1
                await asyncio.sleep(1 / FRAME_RATE)

            cap.release()

    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
        logging.error(f"Connection to server failed: {e}. Please ensure the backend is running. Retrying in 5 seconds...")
        await asyncio.sleep(5)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(face_emotion_sender())
        except KeyboardInterrupt:
            print("Sender stopped by user.")
            break
        except Exception as e:
            logging.exception("Unexpected top-level error in face sender: %s", e)
            time.sleep(3)