from pathlib import Path

from faster_whisper import WhisperModel

from src.config import DEVICE


class WhisperService:
    def __init__(self, model_size: str = "medium", device: str = DEVICE, compute_type: str = "float32") -> None:
        self._model = WhisperModel(model_size, device=device, compute_type=compute_type)

    def transcribe(self, wav_path: Path) -> str:
        segments, _ = self._model.transcribe(str(wav_path), language="ru", beam_size=5)

        return " ".join(segment.text.strip() for segment in segments)
