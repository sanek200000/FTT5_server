from threading import Thread
import threading
import time

from loguru import logger

from schemas.job import JobStatus
from src.schemas.tts import TTSRequestDTO
from src.services.tts import TTSModel
from src.services.job import job_manager


def _run_job(
    job_id: str,
    tts: TTSModel,
    request: TTSRequestDTO,
    ref_audio_bytes: bytes,
):
    job_start = time.perf_counter()
    logger.info(f"[{job_id}] job started")

    try:
        tts_start = time.perf_counter()
        logger.info(
            f"[{job_id}] ENTER synthesize thread={threading.current_thread().name}"
        )  # TODO: delete

        result = tts.synthesize(
            request=request,
            ref_audio_bytes=ref_audio_bytes,
            job_id=job_id,
        )
        logger.info(
            f"[{job_id}] EXIT synthesize thread={threading.current_thread().name} | {time.perf_counter() - tts_start} sec"
        )  # TODO: delete

        logger.debug(
            f"TTS: "
            f" gen={result.generation_time:.2f}s"
            f" ref={result.ref_duration:.2f}s"
            f" out={result.result_duration:.2f}s"
            f" stretch={result.stretch_ratio:.3f}"
        )

        logger.info(f"[{job_id}] TOTAL {time.perf_counter() - job_start} sec")
        job_manager.update(
            job_id,
            status=JobStatus.COMPLETED,
            result=result,
            # result_path=result.wav_path,
            # ref_path=result.ref_path,
        )
    except Exception as ex:
        detail = f"{type(ex)}, {ex}"
        logger.exception(detail)
        job_manager.update(
            job_id,
            status=JobStatus.FAILED,
            error=detail,
        )


def start_job(
    job_id: str,
    tts: TTSModel,
    request: TTSRequestDTO,
    ref_audio_bytes: bytes,
):
    logger.info(f"[{job_id}] Creating worker thread")
    thread = Thread(
        target=_run_job,
        args=(job_id, tts, request, ref_audio_bytes),
        daemon=True,
    )

    thread.start()
    logger.info(f"[{job_id}] Worcer thread started")
