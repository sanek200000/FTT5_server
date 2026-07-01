from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Optional

from loguru import logger

from src.services.tts import TTSModel

TTS: Optional[TTSModel] = None


# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global TTS
#
#     print("Loading model...")
#     TTS = TTSModel()
#     print("Model loaded.")
#
#     yield
#
#     print("Stopping server...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Loading model...")

    app.state.tts = TTSModel()

    logger.info("Model loaded.")

    yield

    logger.info("Stopping server...")
