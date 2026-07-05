import pytest
from kernel.scheduler.scheduler import Scheduler, JobStatus


@pytest.fixture
def scheduler():
    return Scheduler(max_workers=3)


@pytest.mark.asyncio
async def test_enqueue_and_execute(scheduler):
    results = []

    async def my_job(msg: str):
        results.append(msg)

    await scheduler.start()
    await scheduler.enqueue("test.job", my_job, msg="hello")
    await asyncio.sleep(0.2)
    await scheduler.stop()

    assert "hello" in results


@pytest.mark.asyncio
async def test_retry_on_failure(scheduler):
    attempts = 0

    async def failing_job():
        nonlocal attempts
        attempts += 1
        if attempts < 2:
            raise ValueError("Not yet")

    await scheduler.start()
    job = await scheduler.enqueue("failing.job", failing_job, max_retries=2, retry_delay=0.1)
    await asyncio.sleep(0.5)
    await scheduler.stop()

    assert job.status == JobStatus.COMPLETED
    assert attempts == 2


@pytest.mark.asyncio
async def test_cancel_job(scheduler):
    async def slow_job():
        await asyncio.sleep(10)

    await scheduler.start()
    job = await scheduler.enqueue("slow.job", slow_job)
    cancelled = await scheduler.cancel(job.id)
    assert cancelled


@pytest.mark.asyncio
async def test_recurring_job(scheduler):
    count = 0

    async def recurring():
        nonlocal count
        count += 1

    await scheduler.start()
    await scheduler.schedule_recurring("recurring", recurring, interval=0.05, max_executions=3)
    await asyncio.sleep(0.8)
    await scheduler.stop()

    assert count == 3


@pytest.mark.asyncio
async def test_delayed_job(scheduler):
    results = []

    async def delayed():
        results.append("done")

    await scheduler.start()
    await scheduler.enqueue("delayed", delayed, delay=0.3)
    await asyncio.sleep(0.1)
    assert len(results) == 0
    await asyncio.sleep(0.3)
    assert len(results) == 1
    await scheduler.stop()


import asyncio
