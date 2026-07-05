import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Callable, Coroutine, Dict, Optional

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()
    RETRYING = auto()
    DELAYED = auto()


@dataclass
class Job:
    name: str
    handler: Callable[..., Coroutine[Any, Any, Any]]
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    delay: float = 0.0
    max_retries: int = 0
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    error: Optional[str] = None
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RecurringJob:
    name: str
    handler: Callable[..., Coroutine[Any, Any, Any]]
    interval: float
    args: tuple = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    max_executions: Optional[int] = None
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    execution_count: int = 0
    is_running: bool = False


class Scheduler:
    def __init__(self, max_workers: int = 10):
        self._jobs: Dict[str, Job] = {}
        self._recurring: Dict[str, RecurringJob] = {}
        self._queue: asyncio.Queue = asyncio.Queue()
        self._max_workers = max_workers
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        self._running = True
        for _ in range(self._max_workers):
            worker = asyncio.create_task(self._worker_loop())
            self._workers.append(worker)
        asyncio.create_task(self._recurring_loop())
        logger.info(f"Scheduler started with {self._max_workers} workers")

    async def stop(self) -> None:
        self._running = False
        for worker in self._workers:
            worker.cancel()
        if self._workers:
            await asyncio.gather(*self._workers, return_exceptions=True)
        self._workers.clear()
        logger.info("Scheduler stopped")

    async def enqueue(
        self,
        name: str,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        delay: float = 0.0,
        max_retries: int = 0,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        **kwargs,
    ) -> Job:
        job = Job(
            name=name,
            handler=handler,
            delay=delay,
            max_retries=max_retries,
            retry_delay=retry_delay,
            timeout=timeout,
            kwargs=kwargs,
        )
        async with self._lock:
            self._jobs[job.id] = job
        if delay > 0:
            job.status = JobStatus.DELAYED
            asyncio.create_task(self._delay_enqueue(job))
        else:
            await self._queue.put(job)
        return job

    async def _delay_enqueue(self, job: Job) -> None:
        await asyncio.sleep(job.delay)
        job.status = JobStatus.PENDING
        await self._queue.put(job)

    async def schedule_recurring(
        self,
        name: str,
        handler: Callable[..., Coroutine[Any, Any, Any]],
        interval: float,
        max_executions: Optional[int] = None,
        **kwargs,
    ) -> RecurringJob:
        rjob = RecurringJob(
            name=name,
            handler=handler,
            interval=interval,
            max_executions=max_executions,
            kwargs=kwargs,
        )
        async with self._lock:
            self._recurring[rjob.id] = rjob
        logger.info(f"Recurring job '{name}' scheduled every {interval}s")
        return rjob

    async def cancel(self, job_id: str) -> bool:
        async with self._lock:
            job = self._jobs.get(job_id)
            if job and job.status in (JobStatus.PENDING, JobStatus.DELAYED):
                job.status = JobStatus.CANCELLED
                return True
            rjob = self._recurring.get(job_id)
            if rjob:
                rjob.is_running = False
                del self._recurring[job_id]
                return True
        return False

    def get_status(self, job_id: str) -> Optional[JobStatus]:
        job = self._jobs.get(job_id)
        return job.status if job else None

    def get_job(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    async def _worker_loop(self) -> None:
        while self._running:
            try:
                job = await self._queue.get()
                await self._execute_job(job)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Worker error")

    async def _execute_job(self, job: Job) -> None:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        logger.info(f"Executing job '{job.name}' [{job.id[:8]}]")

        try:
            if job.timeout:
                result = await asyncio.wait_for(
                    job.handler(*job.args, **job.kwargs),
                    timeout=job.timeout,
                )
            else:
                result = await job.handler(*job.args, **job.kwargs)

            job.status = JobStatus.COMPLETED
            job.result = result
            job.completed_at = datetime.now(timezone.utc)
            logger.info(f"Job '{job.name}' completed [{job.id[:8]}]")

        except asyncio.TimeoutError:
            job.error = f"Timeout after {job.timeout}s"
            await self._handle_failure(job)
        except Exception as e:
            job.error = str(e)
            await self._handle_failure(job)

    async def _handle_failure(self, job: Job) -> None:
        if job.retry_count < job.max_retries:
            job.retry_count += 1
            job.status = JobStatus.RETRYING
            wait = job.retry_delay * (2 ** (job.retry_count - 1))
            logger.warning(
                f"Job '{job.name}' failed (retry {job.retry_count}/{job.max_retries})"
            )
            await asyncio.sleep(wait)
            await self._queue.put(job)
        else:
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job '{job.name}' failed: {job.error}")

    async def _recurring_loop(self) -> None:
        while self._running:
            try:
                now = datetime.now(timezone.utc)
                async with self._lock:
                    rjobs = list(self._recurring.values())

                for rjob in rjobs:
                    if rjob.is_running:
                        continue
                    if rjob.max_executions and rjob.execution_count >= rjob.max_executions:
                        async with self._lock:
                            self._recurring.pop(rjob.id, None)
                        continue
                    rjob.is_running = True
                    asyncio.create_task(self._execute_recurring(rjob))

                await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("Recurring loop error")

    async def _execute_recurring(self, rjob: RecurringJob) -> None:
        try:
            result = await rjob.handler(*rjob.args, **rjob.kwargs)
            rjob.execution_count += 1
        except Exception as e:
            logger.error(f"Recurring job '{rjob.name}' failed: {e}")
        finally:
            rjob.is_running = False

    def pending_count(self) -> int:
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.PENDING)

    def failed_count(self) -> int:
        return sum(1 for j in self._jobs.values() if j.status == JobStatus.FAILED)
