from pathlib import Path
from typing import Optional

from pydantic import BaseModel, RootModel


class SafetensorDTO(BaseModel):
    name: str
    ckpt_path: Path
    vocab_path: Path


class SafetensorsDTO(RootModel[dict[int, SafetensorDTO]]):
    pass


class CurrentModelResponseDTO(BaseModel):
    loaded: bool
    model: Optional[SafetensorDTO] = None


class LoadModelRequestDTO(BaseModel):
    id: int
