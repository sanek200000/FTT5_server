from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class JobCreateResponseDTO(BaseModel):
    id: str


class JobStatusResponseDTO(JobCreateResponseDTO):
    status: str

    current_attempt: int = 0
    max_attempts: int = 9

    similarity: Optional[float] = None
    speed: Optional[float] = None

    created_at: datetime
    updated_at: datetime

    error: Optional[str] = None


class JobInternalDTO(JobStatusResponseDTO):
    result_path: Optional[Path] = None
