from threading import Thread

from loguru import logger

from src.schemas.tts import TTSRequestDTO
from src.services.tts import TTSModel
from src.services.job import job_manager


def _run_job(
    job_id: str,
    tts: TTSModel,
    request: TTSRequestDTO,
    ref_audio_bytes: bytes,
):
    pass
    try:
        result = tts.synthesize(
            request=request,
            ref_audio_bytes=ref_audio_bytes,
            job_id=job_id,
        )

        logger.debug(
            f"TTS: "
            f" gen={result.generation_time:.2f}s"
            f" ref={result.ref_duration:.2f}s"
            f" out={result.result_duration:.2f}s"
            f" stretch={result.stretch_ratio:.3f}"
        )

        job_manager.update(
            job_id,
            status="completed",
            result_path=result.wav_path,
        )
    except Exception as ex:
        logger.exception(ex)
        job_manager.update(
            job_id,
            status="failed",
            error=str(ex),
        )


def start_job(
    job_id: str,
    tts: TTSModel,
    request: TTSRequestDTO,
    ref_audio_bytes: bytes,
):
    thread = Thread(
        target=_run_job,
        args=(job_id, tts, request, ref_audio_bytes),
        daemon=True,
    )

    thread.start()
