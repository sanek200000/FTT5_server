from typing import Optional

from pydantic import BaseModel


class SimilarityResultDTO(BaseModel):
    score: float

    ratio: float
    token_ratio: float
    partial_ratio: float

    expected: str
    recognized: str

    expected_norm: str
    recognized_norm: str

    whisper_confidence: Optional[float] = None
