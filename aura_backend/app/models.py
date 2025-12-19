from pydantic import BaseModel, Field
from typing import Optional

class GameState(BaseModel):
    player_health: int = 100
    enemy_count: int = 0
    score: int = 0
    player_speed: float = 0.0
    threat_proximity: float = 0.0
    game_time: int = 0
    bullets_fired: int = 0

class EmotionPayload(BaseModel):
    emotion: str = "neutral"
    confidence: float = 0.0

class AudienceVote(BaseModel):
    mood: str