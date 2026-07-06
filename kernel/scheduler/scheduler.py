import asyncio
import uuid
from datetime import datetime
from typing import Any, Callable, Coroutine

from kernel.log import setup_log
from kernel.models import Job, JobStatus
from kernel.exceptions import JobNotFoundError

TaskFunc = Callable[..., Coroutine[Any, Any, Any] | Any]

log = setup_log("scheduler")


class Scheduler:
    def __init__(self, container: Any | None = None):
        self._container = container
        self._jobs: dict[str, Job] = {}
        self._running = False
        self._loop_task: asyncio.Task | None = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        log.info("Scheduler started")

    async def stop(self):
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            self._loop_task = None
        log.info("Scheduler stopped")

    async def _run_loop(self):
        while self._running:
            now = datetime.now()
            for job in list(self._jobs.values()):
                if job.status != JobStatus.PENDING:
                    continue
                if (now - job.created_at).total_seconds() >= job.delay:
                    asyncio.create_task(self._execute(job))
            await asyncio.sleep(1)

    async def add_job(
        self,
        name: str,
        task: TaskFunc,
        delay: float = 0.0,
        interval: float | None = None,
        max_retries: int = 3,
        *args,
        **kwargs,
    ) -> str:
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            name=name,
            task=task,
            delay=delay,
            interval=interval,
            max_retries=max_retries,
        )
        job._args = args
        job._kwargs = kwargs
        self._jobs[job_id] = job
        log.info("Job queued: %s [%s]", name, job_id)
        return job_id

    async def _execute(self, job: Job):
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now()
        log.info("Job running: %s [%s]", job.name, job.id)
        try:
            if asyncio.iscoroutinefunction(job.task):
                result = await job.task(*getattr(job, "_args", ()), **getattr(job, "_kwargs", {}))
            else:
                result = job.task(*getattr(job, "_args", ()), **getattr(job, "_kwargs", {}))
            job.result = result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            log.info("Job completed: %s [%s]", job.name, job.id)
        except Exception as e:
            job.error = str(e)
            if job.retries < job.max_retries:
                job.retries += 1
                job.status = JobStatus.PENDING
                log.warning("Job failed (retry %d/%d): %s [%s]", job.retries, job.max_retries, job.name, job.id)
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                log.error("Job failed: %s [%s] — %s", job.name, job.id, e)

        if job.interval and job.status == JobStatus.COMPLETED:
            job.status = JobStatus.PENDING
            job.created_at = datetime.now()

    async def get_job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        return job

    def list_jobs(self, status: str | None = None) -> list[Job]:
        if status:
            return [j for j in self._jobs.values() if j.status.value == status]
        return list(self._jobs.values())

    async def cancel_job(self, job_id: str):
        job = await self.get_job(job_id)
        job.status = JobStatus.CANCELLED
        log.info("Job cancelled: %s [%s]", job.name, job.id)
