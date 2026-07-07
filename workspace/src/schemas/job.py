from datetime import datetime
from enum import StrEnum
from typing import Optional

from pydantic import BaseModel

from src.schemas.tts import SynthesisResultDTO


class JobStatus(StrEnum):
    QUEUED = "queued"
    PROGRESSING = "progressing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobCreateResponseDTO(BaseModel):
    id: str


class JobStatusResponseDTO(JobCreateResponseDTO):
    status: JobStatus

    current_attempt: int = 0
    max_attempts: int = 0

    similarity: Optional[float] = None
    speed: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    error: Optional[str] = None


class JobInternalDTO(JobStatusResponseDTO):
    result: Optional[SynthesisResultDTO] = None
    # result_path: Optional[Path] = None
    # ref_path: Optional[Path] = None
