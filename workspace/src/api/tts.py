from typing import Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse
from loguru import logger

from src.config import SS
from src.schemas.job import JobCreateResponseDTO, JobStatus, JobStatusResponseDTO
from src.schemas.tts import TTSRequestDTO
from src.schemas.tts_manager import CurrentModelResponseDTO, LoadModelRequestDTO
from src.services.job import job_manager
from src.services.job_executor import start_job

# from src.services.lifespan import TTS as tts

router = APIRouter(prefix="/f5tts", tags=["F5TTS_model"])


@router.get("/models")
def get_models():
    return SS.MODELS_LIST


@router.get("/model/current", response_model=CurrentModelResponseDTO)
def get_current_model(request: Request):
    manager = request.app.state.tts_manager

    model = manager.current_model

    if model:
        return CurrentModelResponseDTO(loaded=True, model=model)

    return CurrentModelResponseDTO(loaded=False)


@router.post("/model/load/{model_id}")
def load_model(
    request: Request,
    model_id: int,
    # dto: LoadModelRequestDTO = Form(1),
):
    manager = request.app.state.tts_manager
    model = SS.MODELS_LIST.root.get(model_id)

    if model is None:
        detail = f"Model with id={model_id} not found"
        logger.error(detail)
        raise HTTPException(status_code=404, detail=detail)

    current = manager.current_model

    if current and current.ckpt_path == model.ckpt_path:
        return CurrentModelResponseDTO(loaded=True, model=current)

    if manager.is_loaded:
        manager.reload(model)
    else:
        manager.load(model)

    return CurrentModelResponseDTO(loaded=True, model=manager.current_model)


@router.get("/job/{job_id}", response_model=JobStatusResponseDTO)
def get_job_status(job_id: str):
    status = job_manager.get_status(job_id)

    if status is None:
        detail = f"Staus by job '{job_id}' not found"
        logger.error(detail)
        raise HTTPException(status_code=404, detail=detail)

    return status


@router.get("/job/{job_id}/result")
def get_job_result(
    job_id: str,
    background_tasks: BackgroundTasks,
):
    job = job_manager.get(job_id)

    if job is None:
        detail = f"Job '{job_id}' not found"
        logger.error(detail)
        raise HTTPException(status_code=404, detail=detail)

    if job.status == JobStatus.FAILED:
        detail = job.error
        logger.error(detail)
        raise HTTPException(status_code=500, detail=detail)

    if job.status != JobStatus.COMPLETED:
        detail = f"Job status is '{job.status}'"
        logger.warning(detail)
        raise HTTPException(status_code=409, detail=detail)

    if job.result is None:
        detail = "Result is empty"
        logger.error(detail)
        raise HTTPException(status_code=500, detail=detail)

    if job.result.wav_path is None:
        detail = "Result path is empty"
        logger.error(detail)
        raise HTTPException(status_code=500, detail=detail)

    result = FileResponse(
        path=job.result.wav_path,
        media_type="audio/wav",
        filename="result.wav",
    )

    background_tasks.add_task(job.result.ref_path.unlink, missing_ok=True)
    background_tasks.add_task(job.result.wav_path.unlink, missing_ok=True)
    background_tasks.add_task(job_manager.delete, job_id)

    return result


@router.get("/")
def root():
    return {"status": "OK"}


@router.post("/tts")
async def tts_endpoint(
    tts_request: Request,
    ref_audio: UploadFile = File(),
    ref_text: str = Form(examples=["Hello"]),
    gen_text: str = Form(examples=["Привет"]),
    speed: float = Form(1.0),
    remove_silence=Form(False),
    match_duration=Form(False),
    seed: Optional[int] = Form(None),
):
    try:
        tts_manager = tts_request.app.state.tts_manager
        tts = tts_manager.get_model()
    except Exception:
        detail = "Model not found"
        logger.error(detail)
        raise RuntimeError(detail)

    # if not tts:
    #     logger.error(RuntimeError("Model is not loaded"))
    #     raise RuntimeError("Model is not loaded")

    request = TTSRequestDTO(
        ref_text=ref_text,
        gen_text=gen_text,
        speed=speed,
        remove_silence=True,
        match_duration=True,
        seed=seed,
    )
    logger.info(request.format_log())

    job_id = job_manager.create_job()

    start_job(
        job_id=job_id,
        tts=tts,
        request=request,
        ref_audio_bytes=await ref_audio.read(),
    )

    return JobCreateResponseDTO(id=job_id)
