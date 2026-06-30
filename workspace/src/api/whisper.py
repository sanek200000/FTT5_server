from fastapi import APIRouter, File, UploadFile

from src.services.temp_files import TempFiles
from src.services.whisper import WhisperService
from src.schemas.whisper import TranscruptionResponseDTO

router = APIRouter(prefix="/transcribe", tags=["Whisper_model"])

whisper = WhisperService()


@router.get("/")
def root():
    return {"text": "Привет"}


@router.post("/", response_model=TranscruptionResponseDTO)
async def transcribe(audio: UploadFile = File(...)) -> TranscruptionResponseDTO:

    wav_path = TempFiles.create_wav(await audio.read())
    text = whisper.transcribe(wav_path)

    return TranscruptionResponseDTO(text=text)
