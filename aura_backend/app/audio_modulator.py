import os
import math
import random
import time
from pydub import AudioSegment
from typing import Dict, Tuple, Optional, List

class AudioModulator:
    """Music DNA modulation engine.

    Current design keeps heavy DSP out (no realtime re-render). Instead we output a rich
    modulation descriptor the frontend (or a future audio engine) can use to:
      * Adjust playbackRate (tempo) with smoothing / quantization
      * Apply dynamic filters, distortion, reverb sends
      * Introduce sectional variation (A/B/Bridge) & phrase level micro-variation
      * Trigger / mute stems (once stems are supported)

    Backward compatibility: get_modulation_params() still returns (tempo, primary_emotion)
    so existing consumers keep working.
    """
    def __init__(self):
        self.base_dna: Optional[AudioSegment] = None
        self.current_dna_file: Optional[str] = None
        self.base_tempo: float = 120.0  # Default BPM (placeholder until tempo detection integrated)

        # Internal evolving state for smoother / less static feel
        self._last_target_tempo: Optional[float] = None
        self._last_announced_tempo: Optional[float] = None
        self._tempo_smoothing_factor: float = 0.15  # exponential smoothing
        self._section_index: int = 0
        self._phrase_index: int = 0
        self._last_section_change: float = time.time()
        self._last_phrase_change: float = time.time()
        self._section_duration_beats: int = 32  # configurable
        self._phrase_duration_beats: int = 8
        self._beat_counter: float = 0.0  # approximate beats passed (updated externally via tick if needed)
        self._rng = random.Random(42)

    # --- Core DNA Loading ---

    def load_dna(self, file_path: str) -> Dict:
        """Loads a music file and analyzes its basic properties."""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            self.base_dna = AudioSegment.from_file(file_path)
            self.current_dna_file = os.path.basename(file_path)
            
            # Simple analysis (can be replaced with librosa for more accuracy)
            self.base_tempo = 120.0 # Placeholder, real tempo detection is complex
            
            info = {
                "duration_seconds": self.base_dna.duration_seconds,
                "channels": self.base_dna.channels,
                "sample_rate": self.base_dna.frame_rate,
                "base_tempo_estimate": self.base_tempo
            }
            return info
        except Exception as e:
            self.base_dna = None
            self.current_dna_file = None
            raise e

    def get_modulation_params(self, emotion_vector: Dict[str, float]) -> Tuple[float, str]:
        """
        Determines audio modulation parameters based on the emotion vector.
        Returns (target_tempo, primary_emotion).
        """
        if not self.base_dna:
            return 120.0, "None"
            
        # Determine primary emotion
        primary_emotion = max(emotion_vector, key=emotion_vector.get) if emotion_vector else "calm"
        intensity = emotion_vector.get(primary_emotion, 0.0)

        # Tempo mapping
        tempo_map = {
            "excitement": (1.1, 1.4), # speed up by 10-40%
            "tension": (1.05, 1.25),
            "fear": (0.9, 1.1), # can be slow or fast
            "joy": (1.0, 1.2),
            "calm": (0.8, 0.95) # slow down
        }
        
        min_mult, max_mult = tempo_map.get(primary_emotion, (1.0, 1.0))
        tempo_multiplier = min_mult + (max_mult - min_mult) * intensity
        target_tempo = self.base_tempo * tempo_multiplier

        # In a full implementation, you would apply these changes here:
        # e.g., self.change_speed(tempo_multiplier)
        # e.g., self.apply_filter(primary_emotion)
        # and then stream the resulting audio.
        # For this version, we are just returning the parameters.

        # Apply smoothing so tempo does not jump every 500ms dramatically
        if self._last_target_tempo is None:
            smoothed = target_tempo
        else:
            smoothed = (self._tempo_smoothing_factor * target_tempo +
                        (1 - self._tempo_smoothing_factor) * self._last_target_tempo)
        self._last_target_tempo = smoothed
        self._last_announced_tempo = smoothed
        return round(smoothed, 2), primary_emotion

    # --- Advanced Modulation Descriptor ---
    def compute_modulation(self, emotion_vector: Dict[str, float]) -> Dict:
        """Return a rich modulation descriptor capturing multiple musical dimensions.

        Output fields (stable contract, additive):
          tempo_bpm: smoothed tempo suggestion
          tempo_multiplier: relative to base_tempo
          primary_emotion: highest weight emotion
          energy: scalar 0-1 (derived from excitement + tension + fear)
          valence: scalar 0-1 (joy vs fear/tension) for brightness / major-minor decisions
          section: {'index','label','length_beats'} macro structural bucket (A/B/Bridge)
          phrase: {'index','within_section','length_beats'} micro phrase cycle
          fx: list of effect intents with target parameters
          layers: suggestion which stem groups should be active (future)
          micro_variation: seed + toggles to randomize arps, ornaments client-side
        """
        if not self.base_dna:
            return {}

        # Derive primary emotion & intensities
        primary_emotion = 'calm'
        intensity = 0.0
        if emotion_vector:
            primary_emotion = max(emotion_vector, key=emotion_vector.get)
            intensity = emotion_vector.get(primary_emotion, 0.0)

        # Energy & Valence heuristics
        energy = min(1.0, (
            emotion_vector.get('excitement', 0) * 0.5 +
            emotion_vector.get('tension', 0) * 0.3 +
            emotion_vector.get('fear', 0) * 0.2
        ))
        # Joy minus dark emotions for valence
        valence = emotion_vector.get('joy', 0) * 0.7 + emotion_vector.get('calm', 0) * 0.3 - (
            emotion_vector.get('fear', 0) * 0.5 + emotion_vector.get('tension', 0) * 0.3
        )
        valence = max(0.0, min(1.0, 0.5 + valence * 0.5))  # normalize around 0.5 baseline

        # Tempo (reuse mapping logic)
        tempo, _ = self.get_modulation_params(emotion_vector)
        tempo_multiplier = tempo / (self.base_tempo or 120.0)

        # Section / phrase progression (time-based fallback). Without a beat clock, we approximate
        now = time.time()
        section_elapsed = now - self._last_section_change
        phrase_elapsed = now - self._last_phrase_change
        # Use seconds->beats approximation (base tempo) to decide rollovers
        sec_per_beat = 60.0 / (self.base_tempo or 120.0)
        if section_elapsed / sec_per_beat >= self._section_duration_beats:
            self._section_index += 1
            self._last_section_change = now
        if phrase_elapsed / sec_per_beat >= self._phrase_duration_beats:
            self._phrase_index += 1
            self._last_phrase_change = now
        section_cycle = ['A','A','B','A','Bridge']
        section_label = section_cycle[self._section_index % len(section_cycle)]

        # Effects intent generation: dynamic list so frontend can map to Web Audio
        fx: List[Dict] = []

        # Low emotions -> gentle LPF swell; high energy -> open filter / add drive
        base_cutoff = 400 + energy * 5000
        fx.append({
            'type': 'filter', 'mode': 'lowpass', 'cutoff_hz': int(base_cutoff),
            'resonance': round(0.7 + 0.6 * intensity, 2)
        })

        # Reverb: more on calm/fear, less on excitement (dry focused)
        reverb_mix = 0.6 * emotion_vector.get('calm', 0) + 0.5 * emotion_vector.get('fear', 0) - 0.3 * emotion_vector.get('excitement', 0)
        reverb_mix = max(0.05, min(0.85, reverb_mix + 0.15))
        fx.append({'type': 'reverb_send', 'mix': round(reverb_mix, 3)})

        # Delay sprinkles for joy/excitement
        delay_prob = 0.2 + 0.5 * emotion_vector.get('joy', 0) + 0.3 * emotion_vector.get('excitement', 0)
        if self._rng.random() < delay_prob * 0.1:  # not every frame
            fx.append({'type': 'delay_event', 'time_sync': '1/8', 'feedback': round(0.2 + 0.4 * energy, 2)})

        # Distortion / saturation for tension/fear peaks
        drive = (emotion_vector.get('tension',0) * 0.6 + emotion_vector.get('fear',0) * 0.4)
        if drive > 0.15:
            fx.append({'type': 'saturation', 'drive': round(0.3 + drive * 0.7, 3)})

        # Layer activation suggestions (future stems). Always include 'core'
        layers = {
            'core': True,
            'percussion_plus': energy > 0.35,
            'high_arps': valence > 0.55 and energy > 0.4,
            'dark_pad': valence < 0.45 and emotion_vector.get('fear',0) > 0.2,
            'sub_pulse': emotion_vector.get('tension',0) > 0.25
        }

        # Micro-variation seed ensures deterministic randomness per phrase
        phrase_seed = hash((self._section_index, self._phrase_index)) & 0xFFFFFFFF
        self._rng.seed(phrase_seed)
        micro_variation = {
            'seed': phrase_seed,
            'ghost_notes': self._rng.random() < 0.4 + 0.3 * energy,
            'stutter_gate': primary_emotion in ('excitement','tension') and self._rng.random() < 0.25 * energy,
            'reverse_one_shot': primary_emotion in ('fear','tension') and self._rng.random() < 0.15 + 0.25 * emotion_vector.get('fear',0)
        }

        descriptor = {
            'tempo_bpm': round(tempo,2),
            'tempo_multiplier': round(tempo_multiplier,4),
            'primary_emotion': primary_emotion,
            'energy': round(energy,3),
            'valence': round(valence,3),
            'section': {
                'index': self._section_index,
                'label': section_label,
                'length_beats': self._section_duration_beats
            },
            'phrase': {
                'global_index': self._phrase_index,
                'within_section': self._phrase_index - (self._section_index * (self._section_duration_beats // self._phrase_duration_beats)),
                'length_beats': self._phrase_duration_beats
            },
            'fx': fx,
            'layers': layers,
            'micro_variation': micro_variation
        }
        return descriptor

    def change_speed(self, audio_segment: AudioSegment, speed: float = 1.0) -> AudioSegment:
        """Changes the speed of an audio segment without changing pitch. (Currently unused)"""
        if speed == 1.0:
            return audio_segment
        return audio_segment.speedup(playback_speed=speed)