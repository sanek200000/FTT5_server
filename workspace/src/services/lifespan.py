from fastapi import FastAPI
from contextlib import asynccontextmanager
from typing import Optional

from models.tts import TTSModel

TTS: Optional[TTSModel] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global TTS

    print("Loading model...")
    TTS = TTSModel()
    print("Model loaded.")

    yield

    print("Stopping server...")
