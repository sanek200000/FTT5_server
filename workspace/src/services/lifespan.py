from fastapi import FastAPI
from contextlib import asynccontextmanager

from loguru import logger

from services.whisper import WhisperService
from src.services.tts_manager import TTSManager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing services...")

    whisper = WhisperService()
    tts_manager = TTSManager(whisper=whisper)

    app.state.whisper = whisper
    app.state.tts_manager = tts_manager

    logger.info("Services initialized.")

    try:
        yield
    finally:
        logger.info("Stopping server...")

        tts_manager.unload()

        del app.state.tts_manager
        del app.state.whisper

        logger.info("Server stopped.")
