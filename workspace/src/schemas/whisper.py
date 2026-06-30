from pydantic import BaseModel


class TranscruptionResponseDTO(BaseModel):
    text: str
