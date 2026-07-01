from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field


class TTSRequestDTO(BaseModel):
    ref_text: str
    gen_text: str

    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    remove_silence: bool = False
    seed: Optional[int] = None

    match_duration: bool = False

    max_attempts: int = Field(default=3, ge=1, le=10)
    min_similarity: float = Field(default=95.0, ge=0.0, le=100.0)
    verify_with_whisper: bool = True


class SynthesisResultDTO(BaseModel):
    ref_path: Path
    wav_path: Path
    generation_time: float
    ref_duration: float
    result_duration: float
    stretch_ratio: float

    attempts: int = 1
    similarity: Optional[float] = None
    recognized_text: Optional[str] = None
