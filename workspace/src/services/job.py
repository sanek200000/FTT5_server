from datetime import UTC, datetime
from uuid import uuid4

from loguru import logger

from schemas.job import JobInternalDTO


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobInternalDTO] = dict()

    def create_job(self) -> str:
        job_id = str(uuid4())
        now = datetime.now(UTC)
        logger.info(f"Create job with id = {job_id}")

        self._jobs[job_id] = JobInternalDTO(
            id=job_id,
            status="queued",
            created_at=now,
            updated_at=now,
        )

        return job_id

    def get(self, job_id) -> JobInternalDTO | None:
        return self._jobs.get(job_id)

    def update(self, job_id, **kwargs) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            logger.error(f"Job '{job_id}' not found")
            raise KeyError(f"Job '{job_id}' not found")

        kwargs["updated_at"] = datetime.now(UTC)
        try:
            updated_job = job.model_copy(update=kwargs, deep=True)
            self._jobs[job_id] = updated_job
        except Exception as ex:
            logger.error(f"ошибка валидации при обновлении задачи: {ex}")
            raise ValueError(f"ошибка валидации при обновлении задачи: {ex}")


job_manager = JobManager()
