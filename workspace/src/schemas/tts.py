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
    # target_duration: Optional[float] = Field(default=None, gt=0)


class SynthesisResultDTO(BaseModel):
    ref_path: Path
    wav_path: Path
    generation_time: float
    ref_duration: float
    result_duration: float
    stretch_ratio: float
