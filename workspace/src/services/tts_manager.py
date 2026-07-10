from typing import Optional
from pathlib import Path
import gc

from loguru import logger

from src.config import VOCAB_MISHA
from src.services.tts import TTSModel


class TTSManager:
    def __init__(self) -> None:
        self._tts: Optional[TTSModel] = None
        self._weights_path: Optional[Path] = None

    @property
    def current_weights(self) -> Path | None:
        return self._weights_path

    @property
    def is_loaded(self) -> bool:
        return self._tts is not None

    def get_model(self) -> TTSModel:
        if self._tts is None:
            detail = "TTS model is not loaded"
            logger.error(detail)
            raise RuntimeError(detail)

        return self._tts

    def load(self, weights_path: Path, vocab_path: Path = VOCAB_MISHA):
        if self._tts is not None:
            detail = "Model is already loaded"
            logger.error(detail)
            raise RuntimeError(detail)

        logger.info(f"Loading model: {weights_path.name}")

        self._tts = TTSModel(
            ckpt_file=weights_path,
            vocab_file=vocab_path,
        )
        self._weights_path = weights_path

        logger.info("Model loaded.")

    def unload(self):
        if self._tts is None:
            return

        logger.info("Unloading modef...")

        del self._tts

        self._tts = None
        self._weights_path = None

        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as ex:
            logger.warning(f"Faild to clear CUDA cache: {ex}")

        logger.info("Model unload.")

    def reload(self, weights_path: Path, vocab_path: Path = VOCAB_MISHA):
        self.unload()
        self.load(weights_path, vocab_path)
