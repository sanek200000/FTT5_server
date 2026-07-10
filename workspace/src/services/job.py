from datetime import UTC, datetime
from uuid import uuid4

from loguru import logger

from schemas.job import JobInternalDTO, JobStatus, JobStatusResponseDTO


class JobManager:
    def __init__(self) -> None:
        self._jobs: dict[str, JobInternalDTO] = dict()

    def has_progressing_jobs(self) -> bool:
        return any(job.status == JobStatus.PROGRESSING for job in self._jobs.values())

    def get_status(self, job_id: str) -> JobStatusResponseDTO | None:
        job = self._jobs.get(job_id)

        if job:
            return JobStatusResponseDTO(**job.model_dump(exclude={"result"}))

    def create_job(self) -> str:
        job_id = str(uuid4())
        now = datetime.now(UTC)
        logger.info(f"Create job with id = {job_id}")

        self._jobs[job_id] = JobInternalDTO(
            id=job_id,
            status=JobStatus.QUEUED,
            created_at=now,
            updated_at=now,
        )

        return job_id

    def get(self, job_id) -> JobInternalDTO | None:
        return self._jobs.get(job_id)

    def update(self, job_id, **kwargs) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            detail = f"Job '{job_id}' not found"
            logger.error(detail)
            raise KeyError(detail)

        kwargs["updated_at"] = datetime.now(UTC)
        try:
            data = job.model_dump()
            data.update(kwargs)

            # updated_job = job.model_copy(update=kwargs, deep=True)
            updated_job = JobInternalDTO.model_validate(data)

            self._jobs[job_id] = updated_job
        except Exception as ex:
            detail = f"ошибка валидации при обновлении задачи: {ex}"
            logger.error(detail)
            raise ValueError(detail)

    def delete(self, job_id: str) -> None:
        self._jobs.pop(job_id, None)


job_manager = JobManager()
