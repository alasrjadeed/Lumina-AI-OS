import asyncio
from datetime import datetime, timedelta

import pytest

from kernel.exceptions import JobNotFoundError
from kernel.scheduler.models import JobStatus
from kernel.scheduler.scheduler import Scheduler, WorkerPool, _cron_matches


@pytest.mark.asyncio
async def test_add_and_execute_job():
    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    await sched.add_job("test", my_task, delay=0)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()

    assert len(results) == 1


@pytest.mark.asyncio
async def test_job_retry_on_failure():
    sched = Scheduler()
    attempts = []

    async def failing_task():
        attempts.append(1)
        raise ValueError("fail")

    await sched.add_job("fail", failing_task, delay=0, max_retries=2)
    await sched.start()
    await asyncio.sleep(3.0)
    await sched.stop()

    assert len(attempts) == 3


@pytest.mark.asyncio
async def test_cancel_job():
    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    job_id = await sched.add_job("cancel", my_task, delay=5)
    await sched.cancel_job(job_id)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()

    assert len(results) == 0


@pytest.mark.asyncio
async def test_get_job():
    sched = Scheduler()
    job_id = await sched.add_job("get_test", lambda: None, delay=0)
    job = await sched.get_job(job_id)
    assert job.id == job_id
    assert job.name == "get_test"


@pytest.mark.asyncio
async def test_get_job_not_found():
    sched = Scheduler()
    with pytest.raises(JobNotFoundError):
        await sched.get_job("nonexistent")


@pytest.mark.asyncio
async def test_list_jobs():
    sched = Scheduler()
    await sched.add_job("a", lambda: None, delay=1)
    await sched.add_job("b", lambda: None, delay=2)
    assert len(sched.list_jobs()) == 2


@pytest.mark.asyncio
async def test_list_jobs_by_status():
    sched = Scheduler()
    j1 = await sched.add_job("a", lambda: None, delay=1)
    await sched.add_job("b", lambda: None, delay=2)
    await sched.cancel_job(j1)
    pending = sched.list_jobs("pending")
    cancelled = sched.list_jobs("cancelled")
    assert len(pending) == 1
    assert len(cancelled) == 1


@pytest.mark.asyncio
async def test_pause_and_resume_job():
    sched = Scheduler()

    async def my_task():
        pass

    job_id = await sched.add_job("pause_test", my_task, delay=0.1)
    await sched.pause_job(job_id)
    job = await sched.get_job(job_id)
    assert job.status.value == "paused"

    await sched.resume_job(job_id)
    job = await sched.get_job(job_id)
    assert job.status.value == "pending"


@pytest.mark.asyncio
async def test_pause_running_job_raises():
    sched = Scheduler()

    async def long_task():
        await asyncio.sleep(10)

    job_id = await sched.add_job("long", long_task, delay=0)
    await sched.start()
    await asyncio.sleep(0.3)

    job = await sched.get_job(job_id)
    if job.status.value == "running":
        with pytest.raises(RuntimeError):
            await sched.pause_job(job_id)
    await sched.stop()


@pytest.mark.asyncio
async def test_update_job():
    sched = Scheduler()
    job_id = await sched.add_job("update_test", lambda: None, delay=5)
    await sched.update_job(job_id, delay=10, max_retries=5)
    job = await sched.get_job(job_id)
    assert job.delay == 10
    assert job.max_retries == 5


@pytest.mark.asyncio
async def test_delete_job():
    sched = Scheduler()
    job_id = await sched.add_job("delete_test", lambda: None)
    await sched.delete_job(job_id)
    assert len(sched.list_jobs()) == 0


@pytest.mark.asyncio
async def test_find_jobs_by_tag():
    sched = Scheduler()
    await sched.add_job("a", lambda: None, tags={"urgent"})
    await sched.add_job("b", lambda: None, tags={"normal"})
    await sched.add_job("c", lambda: None, tags={"urgent"})
    assert len(sched.find_jobs_by_tag("urgent")) == 2
    assert len(sched.find_jobs_by_tag("normal")) == 1
    assert len(sched.find_jobs_by_tag("missing")) == 0


@pytest.mark.asyncio
async def test_stats():
    sched = Scheduler()
    await sched.add_job("a", lambda: None, delay=1)
    await sched.add_job("b", lambda: None, delay=2)
    await sched.add_job("c", lambda: None, delay=3)
    stats = sched.stats()
    assert stats["total"] == 3
    assert stats["pending"] == 3


@pytest.mark.asyncio
async def test_interval_job():
    sched = Scheduler()
    count = 0

    async def recurring():
        nonlocal count
        count += 1

    await sched.add_job("interval_test", recurring, delay=0, interval=0.5, max_retries=1)
    await sched.start()
    await asyncio.sleep(1.2)
    await sched.stop()

    assert count >= 2


@pytest.mark.asyncio
async def test_sync_task():
    sched = Scheduler()
    results = []

    def sync_task():
        results.append("ok")

    await sched.add_job("sync", sync_task, delay=0)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()
    assert results == ["ok"]


def test_cron_matches():
    assert _cron_matches("* * * * *", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("0 * * * *", datetime(2025, 1, 1, 0, 0))
    assert not _cron_matches("0 * * * *", datetime(2025, 1, 1, 0, 1))
    assert _cron_matches("*/5 * * * *", datetime(2025, 1, 1, 0, 5))
    assert not _cron_matches("*/5 * * * *", datetime(2025, 1, 1, 0, 3))
    assert _cron_matches("30 9 * * 1-5", datetime(2025, 1, 7, 9, 30))


@pytest.mark.asyncio
async def test_stop_idempotent():
    sched = Scheduler()
    await sched.stop()
    await sched.stop()


@pytest.mark.asyncio
async def test_start_idempotent():
    sched = Scheduler()
    await sched.start()
    await sched.start()
    await sched.stop()


# ------------------------------------------------------------------
# Cron shorthand
# ------------------------------------------------------------------

def test_cron_shorthand():
    assert _cron_matches("@hourly", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("@hourly", datetime(2025, 1, 1, 23, 0))
    assert not _cron_matches("@hourly", datetime(2025, 1, 1, 0, 1))
    assert _cron_matches("@daily", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("@midnight", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("@weekly", datetime(2025, 1, 5, 0, 0))  # Sunday
    assert _cron_matches("@monthly", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("@yearly", datetime(2025, 1, 1, 0, 0))
    assert _cron_matches("@annually", datetime(2025, 1, 1, 0, 0))


def test_cron_weekday_7_as_sunday():
    assert _cron_matches("0 0 * * 7", datetime(2025, 1, 5, 0, 0))  # Sunday
    assert not _cron_matches("0 0 * * 7", datetime(2025, 1, 6, 0, 0))  # Monday


# ------------------------------------------------------------------
# Cron job reset (repeated execution)
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cron_job_executes_multiple_times():
    sched = Scheduler()
    count = 0

    async def cron_task():
        nonlocal count
        count += 1

    # Use a wildcard cron so it fires frequently; we'll stop after ~2 ticks
    job_id = await sched.add_job("cron_repeat", cron_task, cron="* * * * *", max_retries=1)
    await sched.start()

    # Allow 3 ticks
    await asyncio.sleep(3.5)
    await sched.stop()

    # Should have run at least once and reset to PENDING for next tick
    job = await sched.get_job(job_id)
    assert job.execution_count >= 1
    assert job.status == JobStatus.PENDING


# ------------------------------------------------------------------
# auto_remove
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_auto_remove_after_completion():
    sched = Scheduler()

    async def my_task():
        pass

    job_id = await sched.add_job("auto_remove", my_task, delay=0, auto_remove=True)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()

    with pytest.raises(JobNotFoundError):
        await sched.get_job(job_id)


# ------------------------------------------------------------------
# max_executions
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_max_executions_limits_interval_job():
    sched = Scheduler()
    count = 0

    async def limited_task():
        nonlocal count
        count += 1

    await sched.add_job("limited", limited_task, delay=0, interval=0.2, max_executions=3)
    await sched.start()
    await asyncio.sleep(2.5)
    await sched.stop()

    assert count == 3


# ------------------------------------------------------------------
# start_at / end_at
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_at_delays_execution():

    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    future = datetime.now() + timedelta(seconds=2)
    await sched.add_job("start_at_test", my_task, delay=0, start_at=future)
    await sched.start()
    await asyncio.sleep(0.5)
    # Should not have run yet
    assert len(results) == 0
    await asyncio.sleep(2)
    await sched.stop()
    assert len(results) == 1


@pytest.mark.asyncio
async def test_end_at_prevents_execution():

    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    past = datetime.now() - timedelta(seconds=1)
    await sched.add_job("end_at_test", my_task, delay=0, end_at=past)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()
    assert len(results) == 0


# ------------------------------------------------------------------
# WorkerPool
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_worker_pool_executes_task():

    pool = WorkerPool(max_workers=5)
    results = []

    async def my_task():
        results.append("ok")

    await pool.run(my_task())
    assert results == ["ok"]
    assert pool.active_count == 0


@pytest.mark.asyncio
async def test_worker_pool_limits_concurrency():

    pool = WorkerPool(max_workers=2)
    active_max = 0
    lock = asyncio.Lock()

    async def slow_task(idx):
        nonlocal active_max
        async with lock:
            current = pool.active_count
            if current > active_max:
                active_max = current
        await asyncio.sleep(1)

    tasks = [pool.run(slow_task(i)) for i in range(5)]
    await asyncio.gather(*tasks)
    assert active_max <= 2


@pytest.mark.asyncio
async def test_worker_pool_join():

    pool = WorkerPool(max_workers=5)
    results = []

    async def task():
        await asyncio.sleep(0.1)
        results.append("ok")

    await pool.run(task())
    await pool.join()
    assert results == ["ok"]


@pytest.mark.asyncio
async def test_worker_pool_cancel_all():

    pool = WorkerPool(max_workers=5)

    async def long_task():
        await asyncio.sleep(10)

    t = asyncio.create_task(long_task())
    pool._active.add(t)
    assert pool.active_count == 1
    await pool.cancel_all()
    await asyncio.sleep(0.05)
    assert pool.active_count == 0
    assert t.cancelled()


@pytest.mark.asyncio
async def test_scheduler_uses_worker_pool():
    sched = Scheduler(max_workers=3)
    assert sched.pool.max_workers == 3
    results = []

    async def my_task():
        await asyncio.sleep(0.1)
        results.append("done")

    await sched.add_job("pool_test", my_task, delay=0)
    await sched.start()
    await asyncio.sleep(0.5)
    await sched.stop()
    assert len(results) == 1
