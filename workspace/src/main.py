from contextlib import asynccontextmanager
import sys
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile

sys.path.append(str(Path(__file__).parent.parent))

from src.model import TTSModel

tts: Optional[TTSModel] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts

    print("Loading model...")
    tts = TTSModel()
    print("Model loaded.")

    yield

    print("Stopping server...")


# app = FastAPI(lifespan=lifespan)
app = FastAPI()


@app.get("/")
def root():
    return {"status": "OK"}


@app.post("/tts")
async def tts_endpoint(
    ref_audio: UploadFile = File(),
    ref_text: str = Form(examples=["Hello"]),
    gen_text: str = Form(examples=["Привет"]),
):
    audio = await ref_audio.read()

    if not tts:
        raise RuntimeError("Model is not loaded")

    result = tts.synthesize(
        ref_audio_bytes=audio,
        ref_text=ref_text,
        gen_text=gen_text,
    )

    return FileResponse(
        path=result,
        media_type="audio/wav",
        filename="result.wav",
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
