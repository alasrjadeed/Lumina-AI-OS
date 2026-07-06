import pytest


@pytest.mark.asyncio
async def test_add_and_execute_job():
    from kernel.scheduler.scheduler import Scheduler

    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    await sched.add_job("test", my_task, delay=0)
    await sched.start()
    import asyncio
    await asyncio.sleep(0.5)
    await sched.stop()

    assert len(results) == 1


@pytest.mark.asyncio
async def test_job_retry_on_failure():
    from kernel.scheduler.scheduler import Scheduler

    sched = Scheduler()
    attempts = []

    async def failing_task():
        attempts.append(1)
        raise ValueError("fail")

    await sched.add_job("fail", failing_task, delay=0, max_retries=2)
    await sched.start()
    import asyncio
    await asyncio.sleep(3.0)
    await sched.stop()

    assert len(attempts) == 3


@pytest.mark.asyncio
async def test_cancel_job():
    from kernel.scheduler.scheduler import Scheduler

    sched = Scheduler()
    results = []

    async def my_task():
        results.append("done")

    job_id = await sched.add_job("cancel", my_task, delay=5)
    await sched.cancel_job(job_id)
    await sched.start()
    import asyncio
    await asyncio.sleep(0.5)
    await sched.stop()

    assert len(results) == 0
