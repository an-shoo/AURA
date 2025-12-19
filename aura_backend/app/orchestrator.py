import time
from typing import Dict, Any
from .models import GameState, EmotionPayload

class Orchestrator:
    def __init__(self):
        self.weights = {
            "game_state": 0.8,
            "face": 0.1,
            "speech": 0.1,
            "audience": 0.0  # Kept for structure, but not influencing the final vector
        }
        # Manual override lets demos force a specific emotion vector
        self.manual_override = {
            "active": False,
            "vector": {k: 0.0 for k in ["tension", "excitement", "fear", "joy", "calm"]}
        }
        self.state = {
            "game_state": GameState(),
            "face_emotion": EmotionPayload(),
            "speech_emotion": EmotionPayload(),
            "audience_votes": {
                "tension": 0, "excitement": 0, "fear": 0, "joy": 0, "calm": 0
            }
        }
        self.last_update_time = {
            "game_state": 0, "face_emotion": 0, "speech_emotion": 0
        }
        self.emotion_map = ["tension", "excitement", "fear", "joy", "calm"]

    def _is_stale(self, source: str, timeout: int = 5) -> bool:
        return time.time() - self.last_update_time.get(source, 0) > timeout

    def update_game_state(self, game_state: GameState):
        self.state["game_state"] = game_state
        self.last_update_time["game_state"] = time.time()

    def update_face_emotion(self, emotion_payload: EmotionPayload):
        self.state["face_emotion"] = emotion_payload
        self.last_update_time["face_emotion"] = time.time()

    def update_speech_emotion(self, emotion_payload: EmotionPayload):
        self.state["speech_emotion"] = emotion_payload
        self.last_update_time["speech_emotion"] = time.time()

    def update_audience_vote(self, mood: str):
        if mood in self.state["audience_votes"]:
            self.state["audience_votes"][mood] += 1

    def update_weights(self, new_weights: Dict[str, float]):
        """Update source weights dynamically (clamped 0-1)."""
        for k, v in new_weights.items():
            if k in self.weights:
                try:
                    self.weights[k] = max(0.0, min(1.0, float(v)))
                except Exception:
                    continue

    def set_manual_override(self, active: bool, vector: Dict[str, float] = None):
        """Enable/disable manual override and optionally set the vector."""
        self.manual_override["active"] = bool(active)
        if vector:
            for k, v in vector.items():
                if k in self.manual_override["vector"]:
                    try:
                        self.manual_override["vector"][k] = max(0.0, min(1.0, float(v)))
                    except Exception:
                        continue

    def _get_game_state_vector(self) -> Dict[str, float]:
        gs = self.state["game_state"]
        
        # Threat proximity is a good proxy for Fear and Tension
        fear = gs.threat_proximity * 0.8
        tension = gs.threat_proximity * 0.6
        
        # Player speed and bullets fired can indicate Excitement
        excitement = (gs.player_speed * 0.5 + min(gs.bullets_fired / 10, 1) * 0.5)
        
        # High score and low threat can indicate Joy/Calm
        low_threat_calm = (1 - gs.threat_proximity)
        joy = low_threat_calm * (min(gs.score / 1000, 1) * 0.5)
        calm = low_threat_calm * (1 - gs.player_speed) * 0.7
        
        # Normalize to prevent overpowering
        vector = {
            "fear": min(1.0, fear),
            "tension": min(1.0, tension),
            "excitement": min(1.0, excitement),
            "joy": min(1.0, joy),
            "calm": min(1.0, calm)
        }
        return vector

    def _get_emotion_payload_vector(self, payload: EmotionPayload) -> Dict[str, float]:
        # Mapping from DeepFace/Speech model outputs to our desired vector
        # This needs to be customized based on your model's output labels
        emotion_mapping = {
            "angry": {"tension": 0.8, "excitement": 0.4},
            "disgust": {"tension": 0.6},
            "fear": {"fear": 1.0, "tension": 0.7},
            "happy": {"joy": 1.0, "excitement": 0.6},
            "sad": {"calm": 0.5}, # Can be mapped differently
            "surprise": {"excitement": 0.9, "fear": 0.2},
            "neutral": {"calm": 0.8}
        }
        
        base_vector = {k: 0.0 for k in self.emotion_map}
        dominant_emotion = payload.emotion.lower()
        
        if dominant_emotion in emotion_mapping:
            for key, value in emotion_mapping[dominant_emotion].items():
                base_vector[key] = value * payload.confidence
        return base_vector
    
    def get_audience_vector(self) -> Dict[str, float]:
        total_votes = sum(self.state["audience_votes"].values())
        if total_votes == 0:
            return {k: 0.0 for k in self.emotion_map}
        
        return {
            emotion: count / total_votes
            for emotion, count in self.state["audience_votes"].items()
        }

    def get_final_emotion_vector(self) -> Dict[str, float]:
        # Manual override short-circuit for demos
        if self.manual_override["active"]:
            return self.manual_override["vector"].copy()

        final_vector = {k: 0.0 for k in self.emotion_map}

        # Determine active sources and dynamically re-normalize weights so that
        # emotions still move when the game client (dominant weight) is absent.
        active_sources = []
        effective_weights = {}
        for source_key, weight_key in [("game_state", "game_state"), ("face_emotion", "face"), ("speech_emotion", "speech")]:
            if not self._is_stale(source_key):
                active_sources.append(weight_key)
        if not active_sources:
            return final_vector  # all stale -> zeros
        weight_sum = sum(self.weights[w] for w in active_sources)
        if weight_sum == 0:
            # fallback uniform distribution if configured weights zero out
            for w in active_sources:
                effective_weights[w] = 1 / len(active_sources)
        else:
            for w in active_sources:
                effective_weights[w] = self.weights[w] / weight_sum

        if "game_state" in active_sources:
            game_vector = self._get_game_state_vector()
            for k in self.emotion_map:
                final_vector[k] += game_vector.get(k, 0.0) * effective_weights["game_state"]
        if "face" in active_sources:
            face_vector = self._get_emotion_payload_vector(self.state["face_emotion"])
            for k in self.emotion_map:
                final_vector[k] += face_vector.get(k, 0.0) * effective_weights["face"]
        if "speech" in active_sources:
            speech_vector = self._get_emotion_payload_vector(self.state["speech_emotion"])
            for k in self.emotion_map:
                final_vector[k] += speech_vector.get(k, 0.0) * effective_weights["speech"]

        for k in self.emotion_map:
            final_vector[k] = max(0.0, min(1.0, final_vector[k]))
        return final_vector

    def get_all_sources_data(self) -> Dict[str, Any]:
        return {
            "game_state": self.state["game_state"].dict(),
            "face_emotion": self.state["face_emotion"].dict(),
            "speech_emotion": self.state["speech_emotion"].dict(),
            "audience_votes": self.state["audience_votes"],
            "audience_vector": self.get_audience_vector(),
            "weights": self.weights,
            "manual_override": self.manual_override,
        }