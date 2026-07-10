from pathlib import Path

from pydantic import BaseModel, RootModel


class SafetensorDTO(BaseModel):
    name: str
    ckpt_path: Path
    vocab_path: Path


class SafetensorsDTO(RootModel[dict[int, SafetensorDTO]]):
    pass
