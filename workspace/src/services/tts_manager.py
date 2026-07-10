from typing import Optional
from pathlib import Path
import gc

from loguru import logger

from schemas.tts_manager import SafetensorDTO
from src.config import VOCAB_MISHA
from src.services.tts import TTSModel


class TTSManager:
    def __init__(self) -> None:
        self._tts: Optional[TTSModel] = None
        self._weights_path: Optional[Path] = None
        self._model_info: Optional[SafetensorDTO] = None

    @property
    def current_model(self) -> Path | None:
        return self._model_info

    @property
    def is_loaded(self) -> bool:
        return self._tts is not None

    def get_model(self) -> TTSModel:
        if self._tts is None:
            detail = "TTS model is not loaded"
            logger.error(detail)
            raise RuntimeError(detail)

        return self._tts

    def load(self, model: SafetensorDTO):
        if self._tts is not None:
            detail = "Model is already loaded"
            logger.error(detail)
            raise RuntimeError(detail)

        logger.info(f"Loading model: {model.name}")

        self._tts = TTSModel(
            ckpt_file=model.ckpt_path,
            vocab_file=model.vocab_path,
        )
        self._model_info = model

        logger.info("Model loaded.")

    def unload(self):
        if self._tts is None:
            return

        logger.info("Unloading modef...")

        del self._tts

        self._tts = None
        self._model_info = None

        gc.collect()

        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception as ex:
            logger.warning(f"Faild to clear CUDA cache: {ex}")

        logger.info("Model unload.")

    def reload(self, model: SafetensorDTO):
        self.unload()
        self.load(model)
