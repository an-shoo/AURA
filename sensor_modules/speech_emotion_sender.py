import asyncio
import websockets
import json
import logging
import pickle
import numpy as np
import pyaudio
import wave
import os
import threading
import time
from collections import deque
import soundfile
import librosa

logging.basicConfig(level=logging.INFO)

# --- Configuration ---
SERVER_URI = "ws://localhost:8000/ws/sensors" 
# SERVER_URI = os.environ.get("AURA_BACKEND_WS_URL", "ws://localhost:8000/ws/sensors")
MODEL_PATH = "aura_backend/emotion_models/" # Relative path to models

# --- Model Loading ---
try:
    with open(os.path.join(MODEL_PATH, 'emotion_recognition_model.pkl'), 'rb') as f:
        model = pickle.load(f)
    logging.info("Speech emotion model loaded successfully.")
except FileNotFoundError:
    logging.error(f"Model file not found in {MODEL_PATH}. Please ensure the path is correct.")
    exit()

def extract_feature_from_array(audio_data, sample_rate):
    result = np.array([])
    mfccs = np.mean(librosa.feature.mfcc(y=audio_data, sr=sample_rate, n_mfcc=40).T, axis=0)
    result = np.hstack((result, mfccs))
    stft = np.abs(librosa.stft(audio_data))
    chroma = np.mean(librosa.feature.chroma_stft(S=stft, sr=sample_rate).T, axis=0)
    result = np.hstack((result, chroma))
    mel = np.mean(librosa.feature.melspectrogram(y=audio_data, sr=sample_rate).T, axis=0)
    result = np.hstack((result, mel))
    return result

class RealTimeEmotionRecognizer:
    def __init__(self, websocket):
        self.websocket = websocket
        self.chunk_duration = 2.0  # seconds
        self.sample_rate = 44100
        self.chunk_samples = int(self.chunk_duration * self.sample_rate)
        self.audio_buffer = deque(maxlen=self.chunk_samples)
        self.is_recording = False
        self.p = pyaudio.PyAudio()
        self.stream = None

    def audio_callback(self, in_data, frame_count, time_info, status):
        audio_data = np.frombuffer(in_data, dtype=np.float32)
        self.audio_buffer.extend(audio_data)
        return (in_data, pyaudio.paContinue)

    async def process_audio_chunk(self):
        if len(self.audio_buffer) < self.chunk_samples:
            return

        audio_array = np.array(list(self.audio_buffer))
        
        try:
            features = extract_feature_from_array(audio_array, self.sample_rate)
            prediction = model.predict([features])
            confidence_scores = model.predict_proba([features])[0]
            
            dominant_emotion = prediction[0]
            confidence = np.max(confidence_scores)

            payload = {
                "source": "speech",
                "payload": {
                    "emotion": dominant_emotion,
                    "confidence": round(float(confidence), 4)
                }
            }
            
            await self.websocket.send(json.dumps(payload))
            logging.info(f"Sent speech emotion: {payload['payload']}")

        except Exception as e:
            logging.error(f"Processing error: {e}")

    async def start(self):
        logging.info("Starting real-time speech recognition...")
        self.stream = self.p.open(
            format=pyaudio.paFloat32,
            channels=1,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback
        )
        self.is_recording = True
        self.stream.start_stream()
        
        try:
            while self.is_recording:
                await self.process_audio_chunk()
                await asyncio.sleep(1.0) # Analyze every second
        finally:
            self.stop()

    def stop(self):
        self.is_recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.p.terminate()

async def speech_emotion_sender():
    logging.info("Attempting to connect to AURA server at %s", SERVER_URI)
    try:
        async with websockets.connect(SERVER_URI) as websocket:
            logging.info("Successfully connected to AURA server.")
            # Initial handshake (neutral) so backend marks sensor active quickly
            try:
                await websocket.send(json.dumps({"source": "speech", "payload": {"emotion": "neutral", "confidence": 0.0}}))
            except Exception:
                logging.debug("Failed to send initial handshake payload")
            recognizer = RealTimeEmotionRecognizer(websocket)
            await recognizer.start()
    except (websockets.exceptions.ConnectionClosedError, ConnectionRefusedError) as e:
        logging.error(f"Connection to server failed: {e}. Retrying in 5 seconds...")
        await asyncio.sleep(5)
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    while True:
        try:
            asyncio.run(speech_emotion_sender())
        except KeyboardInterrupt:
            print("Sender stopped by user.")
            break
        except Exception:

            pass
