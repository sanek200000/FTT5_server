from fastapi import APIRouter, File, Request, UploadFile

from src.services.temp_files import TempFiles
from src.services.whisper import WhisperService
from src.schemas.whisper import TranscruptionResponseDTO

router = APIRouter(prefix="/transcribe", tags=["Whisper_model"])

# whisper = WhisperService()


@router.get("/")
def root():
    return {"text": "Привет"}


@router.post("/", response_model=TranscruptionResponseDTO)
async def transcribe(
    request: Request,
    audio: UploadFile = File(...),
) -> TranscruptionResponseDTO:
    whisper = request.app.state.whisper
    wav_path = TempFiles.create_wav(await audio.read())

    try:
        text = whisper.transcribe(wav_path)
        return TranscruptionResponseDTO(text=text)
    finally:
        pass
        # wav_path.unlink(missing_ok=True)
