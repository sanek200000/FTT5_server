from fastapi import FastAPI
from contextlib import asynccontextmanager

from loguru import logger

from src.config import SS
from src.services.tts_manager import TTSManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing TTS manager...")

    # manager = TTSManager()

    # default_model = next(iter(SS.MODELS_LIST.root.values()), None)
    #
    # if default_model is None:
    #     detail = "No TTS models found"
    #     logger.error(detail)
    #     raise RuntimeError(detail)

    # manager.load(
    #     weights_path=default_model.ckpt_path,
    #     vocab_path=default_model.vocab_path,
    # )
    # logger.info(f"Default model loaded: {default_model.name}")

    app.state.tts = TTSManager()

    logger.info("TTS manager initialized.")

    yield

    logger.info("Stopping server...")

    app.state.tts.unload()
