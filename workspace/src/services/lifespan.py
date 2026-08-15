from fastapi import FastAPI
from contextlib import asynccontextmanager

from loguru import logger

from services.whisper import WhisperService
from src.services.tts_manager import TTSManager


def log_memory_snapshot(label: str) -> None:
    import tracemalloc

    tracemalloc.start(25)

    snapshot = tracemalloc.take_snapshot()

    total = sum(stat.size for stat in snapshot.statistics("filename"))

    logger.debug(f"[TRACEMALLOC] {label}: {total / 1024 / 1024:.2f} MiB")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing services...")

    whisper = WhisperService()
    tts_manager = TTSManager(whisper=whisper)

    app.state.whisper = whisper
    app.state.tts_manager = tts_manager

    logger.info("Services initialized.")
    # log_memory_snapshot("START")

    try:
        yield
    finally:
        logger.info("Stopping server...")

        tts_manager.unload()

        del app.state.tts_manager
        del app.state.whisper

        logger.info("Server stopped.")
        # log_memory_snapshot("AFTER_10_JOBS")
