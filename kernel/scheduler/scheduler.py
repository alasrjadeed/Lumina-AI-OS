from __future__ import annotations

import asyncio
import contextlib
import re
import uuid
from datetime import datetime
from typing import Any

from kernel.events import Event
from kernel.exceptions import JobNotFoundError
from kernel.log import setup_log
from kernel.scheduler.models import Job, JobStatus, TaskFunc

log = setup_log("scheduler")

# ---------------------------------------------------------------------------
# Cron helpers
# ---------------------------------------------------------------------------

_CRON_SHORTHAND: dict[str, str] = {
    "@yearly": "0 0 1 1 *",
    "@annually": "0 0 1 1 *",
    "@monthly": "0 0 1 * *",
    "@weekly": "0 0 * * 0",
    "@daily": "0 0 * * *",
    "@midnight": "0 0 * * *",
    "@hourly": "0 * * * *",
}

_CRON_RE = re.compile(
    r"^(\d+|\*|\*/\d+|\d+-\d+|\d+(?:,\d+)*)\s+"
    r"(\d+|\*|\*/\d+|\d+-\d+|\d+(?:,\d+)*)\s+"
    r"(\d+|\*|\*/\d+|\d+-\d+|\d+(?:,\d+)*)\s+"
    r"(\d+|\*|\*/\d+|\d+-\d+|\d+(?:,\d+)*)\s+"
    r"(\d+|\*|\*/\d+|\d+-\d+|\d+(?:,\d+)*)$",
)

_WEEKDAY_MAP = [1, 2, 3, 4, 5, 6, 0]


def _expand_cron(expr: str) -> str:
    return _CRON_SHORTHAND.get(expr.strip(), expr.strip())


def _parse_cron(
    expr: str,
) -> tuple[list[int], list[int], list[int], list[int], list[int]]:
    expr = _expand_cron(expr)
    m = _CRON_RE.match(expr)
    if not m:
        raise ValueError(f"Invalid cron expression: {expr}")

    def _part(s: str, lo: int, hi: int) -> list[int]:
        if s == "*":
            return list(range(lo, hi + 1))
        if s.startswith("*/"):
            step = int(s[2:])
            return list(range(lo, hi + 1, step))
        vals: list[int] = []
        for token in s.split(","):
            if "-" in token:
                a, b = token.split("-", 1)
                vals.extend(range(int(a), int(b) + 1))
            else:
                vals.append(int(token))
        return [v for v in vals if lo <= v <= hi]

    weekdays = _part(m.group(5), 0, 7)
    # Accept 7 as Sunday (cron standard) and normalise to 0
    weekdays = [0 if w == 7 else w for w in weekdays]
    return (
        _part(m.group(1), 0, 59),
        _part(m.group(2), 0, 23),
        _part(m.group(3), 1, 31),
        _part(m.group(4), 1, 12),
        weekdays,
    )


def _cron_matches(expr: str, dt: datetime | None = None) -> bool:
    dt = dt or datetime.now()
    minutes, hours, days, months, weekdays = _parse_cron(expr)
    cron_wd = _WEEKDAY_MAP[dt.weekday()]
    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in days
        and dt.month in months
        and (cron_wd in weekdays or cron_wd == 0 and 7 in weekdays)
    )


# ---------------------------------------------------------------------------
# Worker pool
# ---------------------------------------------------------------------------


class WorkerPool:
    def __init__(self, max_workers: int = 10) -> None:
        self._semaphore = asyncio.Semaphore(max_workers)
        self._max_workers = max_workers
        self._active: set[asyncio.Task[None]] = set()

    @property
    def max_workers(self) -> int:
        return self._max_workers

    @property
    def active_count(self) -> int:
        return len(self._active)

    async def run(
        self,
        coro: asyncio.Task[None],
    ) -> Any:
        async with self._semaphore:
            task = asyncio.ensure_future(coro)
            self._active.add(task)
            try:
                return await task
            finally:
                self._active.discard(task)

    async def join(self) -> None:
        if self._active:
            await asyncio.gather(*self._active, return_exceptions=True)

    async def cancel_all(self) -> None:
        for task in list(self._active):
            task.cancel()
        self._active.clear()


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------


class Scheduler:
    def __init__(
        self,
        container: Any | None = None,
        max_workers: int = 10,
    ) -> None:
        self._container = container
        self._jobs: dict[str, Job] = {}
        self._running = False
        self._loop_task: asyncio.Task[None] | None = None
        self._event_bus: Any = None
        self._pool = WorkerPool(max_workers=max_workers)
        if container is not None:
            self._event_bus = container.try_resolve("event_bus")

    @property
    def pool(self) -> WorkerPool:
        return self._pool

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        log.info("Scheduler started")

    async def stop(self) -> None:
        self._running = False
        await self._pool.join()
        if self._loop_task:
            self._loop_task.cancel()
            self._loop_task = None
        log.info("Scheduler stopped")

    async def _run_loop(self) -> None:
        while self._running:
            now = datetime.now()
            for job in list(self._jobs.values()):
                if job.status is not JobStatus.PENDING:
                    continue
                if job.start_at and now < job.start_at:
                    continue
                if job.end_at and now > job.end_at:
                    continue
                if job.max_executions is not None and job.execution_count >= job.max_executions:
                    continue
                if self._should_run(job, now):
                    job.status = JobStatus.RUNNING
                    await self._pool.run(self._execute(job))  # pyright: ignore[reportArgumentType]
            await asyncio.sleep(1)

    def _should_run(self, job: Job, now: datetime) -> bool:
        if job.cron:
            cron_expr = _expand_cron(job.cron)
            return _cron_matches(cron_expr, now)
        elapsed = (now - job.created_at).total_seconds()
        if job.execution_count > 0 and job.interval is not None:
            return elapsed >= job.interval
        return elapsed >= job.delay

    async def add_job(
        self,
        name: str,
        task: TaskFunc,
        delay: float = 0.0,
        interval: float | None = None,
        cron: str | None = None,
        max_retries: int = 3,
        tags: set[str] | None = None,
        auto_remove: bool = False,
        max_executions: int | None = None,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> str:
        job_id = str(uuid.uuid4())[:8]
        job = Job(
            id=job_id,
            name=name,
            task=task,
            delay=delay,
            interval=interval,
            cron=cron,
            max_retries=max_retries,
            tags=tags or set(),
            auto_remove=auto_remove,
            max_executions=max_executions,
            start_at=start_at,
            end_at=end_at,
        )
        job._args = args  # pyright: ignore[reportAttributeAccessIssue]
        job._kwargs = kwargs  # pyright: ignore[reportAttributeAccessIssue]
        self._jobs[job_id] = job
        await self._emit("job.added", job_id, name)
        log.info("Job queued: %s [%s]", name, job_id)
        return job_id

    async def _execute(self, job: Job) -> None:
        job.started_at = datetime.now()
        log.info("Job running: %s [%s]", job.name, job.id)
        try:
            task = job.task
            resolved_args = getattr(job, "_args", ())
            resolved_kwargs = getattr(job, "_kwargs", {})
            if asyncio.iscoroutinefunction(task):
                result = await task(*resolved_args, **resolved_kwargs)
            else:
                result = task(*resolved_args, **resolved_kwargs)
            job.result = result
            job.execution_count += 1
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.now()
            await self._emit("job.completed", job.id, job.name)
            log.info("Job completed: %s [%s]", job.name, job.id)
        except Exception as e:
            job.error = str(e)
            if job.retries < job.max_retries:
                job.retries += 1
                job.status = JobStatus.PENDING
                log.warning(
                    "Job failed (retry %d/%d): %s [%s]",
                    job.retries,
                    job.max_retries,
                    job.name,
                    job.id,
                )
            else:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.now()
                await self._emit("job.failed", job.id, job.name, error=str(e))
                log.error("Job failed: %s [%s] — %s", job.name, job.id, e)

        if job.status is JobStatus.COMPLETED:
            if job.auto_remove:
                del self._jobs[job.id]
                log.info("Job auto-removed: %s [%s]", job.name, job.id)
                return

            if job.interval or job.cron:
                reached_max = (
                    job.max_executions is not None and job.execution_count >= job.max_executions
                )
                if not reached_max:
                    job.status = JobStatus.PENDING
                    if job.interval:
                        job.created_at = datetime.now()

    async def _emit(
        self,
        event_name: str,
        job_id: str,
        job_name: str,
        **extra: Any,
    ) -> None:
        if self._event_bus is None:
            return
        with contextlib.suppress(Exception):
            await self._event_bus.publish(
                Event(
                    name=f"scheduler.{event_name}",
                    payload={"job_id": job_id, "job_name": job_name, **extra},
                    source="scheduler",
                ),
            )

    # ------------------------------------------------------------------
    # Job management
    # ------------------------------------------------------------------

    async def pause_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        if job.status == JobStatus.RUNNING:
            raise RuntimeError(f"Cannot pause running job: {job_id}")
        job.status = JobStatus.PAUSED
        log.info("Job paused: %s [%s]", job.name, job.id)

    async def resume_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        job.status = JobStatus.PENDING
        log.info("Job resumed: %s [%s]", job.name, job.id)

    async def update_job(
        self,
        job_id: str,
        delay: float | None = None,
        interval: float | None = None,
        max_retries: int | None = None,
        tags: set[str] | None = None,
    ) -> Job:
        job = await self.get_job(job_id)
        if delay is not None:
            job.delay = delay
        if interval is not None:
            job.interval = interval
        if max_retries is not None:
            job.max_retries = max_retries
        if tags is not None:
            job.tags = tags
        return job

    async def get_job(self, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        return job

    def list_jobs(self, status: str | None = None) -> list[Job]:
        if status:
            return [j for j in self._jobs.values() if j.status.value == status]
        return list(self._jobs.values())

    def find_jobs_by_tag(self, tag: str) -> list[Job]:
        return [j for j in self._jobs.values() if tag in j.tags]

    async def cancel_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        job.status = JobStatus.CANCELLED
        await self._emit("job.cancelled", job.id, job.name)
        log.info("Job cancelled: %s [%s]", job.name, job.id)

    async def delete_job(self, job_id: str) -> None:
        job = await self.get_job(job_id)
        del self._jobs[job_id]
        log.info("Job deleted: %s [%s]", job.name, job.id)

    def stats(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for j in self._jobs.values():
            counts[j.status.value] = counts.get(j.status.value, 0) + 1
        counts["total"] = len(self._jobs)
        return counts
