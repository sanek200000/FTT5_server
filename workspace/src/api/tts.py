from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from src.schemas.job import JobCreateResponseDTO, JobStatusResponseDTO
from src.services.job_executor import start_job
from src.schemas.tts import TTSRequestDTO
from src.services.job import job_manager

# from src.services.lifespan import TTS as tts

router = APIRouter(prefix="/f5tts", tags=["F5TTS_model"])


@router.get("/job/{job_id}", response_model=JobStatusResponseDTO)
def get_job_status(job_id: str):
    job = job_manager.get(job_id)

    if job is None:
        logger.error(f"Job '{job_id}' not found")
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return JobStatusResponseDTO.model_validate(job)


@router.get("/")
def root():
    return {"status": "OK"}


@router.post("/tts")
async def tts_endpoint(
    tts_request: Request,
    background_tasks: BackgroundTasks,
    ref_audio: UploadFile = File(),
    ref_text: str = Form(examples=["Hello"]),
    gen_text: str = Form(examples=["Привет"]),
    speed: float = Form(1.0),
    remove_silence=Form(True),
    match_duration=Form(True),
    seed: Optional[int] = Form(None),
):
    tts = tts_request.app.state.tts

    if not tts:
        logger.error(RuntimeError("Model is not loaded"))
        raise RuntimeError("Model is not loaded")

    request = TTSRequestDTO(
        ref_text=ref_text,
        gen_text=gen_text,
        speed=speed,
        remove_silence=remove_silence,
        match_duration=match_duration,
        seed=seed,
    )

    job_id = job_manager.create_job()

    start_job(
        job_id=job_id,
        tts=tts,
        request=request,
        ref_audio_bytes=await ref_audio.read(),
    )

    return JobCreateResponseDTO(id=job_id)

    result = tts.synthesize(
        request=request,
        ref_audio_bytes=await ref_audio.read(),
    )

    logger.debug(
        f"TTS: "
        f" gen={result.generation_time:.2f}s"
        f" ref={result.ref_duration:.2f}s"
        f" out={result.result_duration:.2f}s"
        f" stretch={result.stretch_ratio:.3f}"
    )

    background_tasks.add_task(result.ref_path.unlink, missing_ok=True)
    background_tasks.add_task(result.wav_path.unlink, missing_ok=True)

    return FileResponse(
        path=result.wav_path,
        media_type="audio/wav",
        filename="result.wav",
    )
