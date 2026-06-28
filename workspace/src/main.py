import sys
from pathlib import Path
from typing import Optional
from contextlib import asynccontextmanager
from fastapi.responses import FileResponse, JSONResponse
from fastapi import BackgroundTasks, FastAPI, File, Form, UploadFile

sys.path.append(str(Path(__file__).parent.parent))

from src.schemas.tts import TTSRequestDTO
from src.exceptions import SynthesisException
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


app = FastAPI(lifespan=lifespan)
# app = FastAPI()


@app.get("/")
def root():
    return {"status": "OK"}


@app.post("/tts")
async def tts_endpoint(
    background_tasks: BackgroundTasks,
    ref_audio: UploadFile = File(),
    ref_text: str = Form(examples=["Hello"]),
    gen_text: str = Form(examples=["Привет"]),
    speed: float = Form(1.0),
    remove_silence=Form(False),
    seed: Optional[int] = Form(None),
):

    if not tts:
        raise RuntimeError("Model is not loaded")

    request = TTSRequestDTO(
        ref_text=ref_text,
        gen_text=gen_text,
        speed=speed,
        remove_silence=remove_silence,
        seed=seed,
    )

    result = tts.synthesize(
        request=request,
        ref_audio_bytes=await ref_audio.read(),
    )

    print(
        f"TTS: "
        f" gen={result.generation_time:.2f}s"
        f" ref={result.ref_duration:.2f}s"
        f" out={result.result_duration:.2f}s"
    )

    background_tasks.add_task(result.ref_path.unlink, missing_ok=True)
    background_tasks.add_task(result.wav_path.unlink, missing_ok=True)

    return FileResponse(
        path=result.wav_path,
        media_type="audio/wav",
        filename="result.wav",
    )


@app.exception_handler(SynthesisException)
async def synthesis_exception_handler(request, ex):
    return JSONResponse(
        status_code=500,
        content={"error": str(ex)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", reload=True, host="0.0.0.0", port=8000)
