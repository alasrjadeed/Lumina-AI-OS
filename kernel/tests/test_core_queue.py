from __future__ import annotations

from pathlib import Path

import pytest

from core.queue.engine import Task, TaskQueue, TaskStatus


@pytest.fixture
def queue(tmp_path: Path) -> TaskQueue:
    return TaskQueue(storage_path=str(tmp_path / "queue.json"))


class TestTaskQueue:
    def test_create_pipeline(self, queue: TaskQueue):
        p = queue.create_pipeline("Test Pipeline")
        assert p.name == "Test Pipeline"
        assert p.status == "draft"

    def test_list_pipelines_empty(self, queue: TaskQueue):
        assert queue.list_pipelines() == []

    def test_list_pipelines_with_data(self, queue: TaskQueue):
        queue.create_pipeline("P1")
        queue.create_pipeline("P2")
        assert len(queue.list_pipelines()) == 2

    def test_get_pipeline_exists(self, queue: TaskQueue):
        p = queue.create_pipeline("Find Me")
        found = queue.get_pipeline(p.id)
        assert found is not None
        assert found.name == "Find Me"

    def test_get_pipeline_missing(self, queue: TaskQueue):
        assert queue.get_pipeline("nonexistent") is None

    def test_delete_pipeline_exists(self, queue: TaskQueue):
        p = queue.create_pipeline("Delete Me")
        assert queue.delete_pipeline(p.id) is True
        assert queue.get_pipeline(p.id) is None

    def test_delete_pipeline_missing(self, queue: TaskQueue):
        assert queue.delete_pipeline("nonexistent") is False

    def test_add_task(self, queue: TaskQueue):
        p = queue.create_pipeline("P")
        task = queue.add_task(p.id, "My Task", "say_hello", module="chat", params={"prompt": "hi"})
        assert task is not None
        assert task.name == "My Task"
        assert task.module == "chat"

    def test_add_task_to_missing_pipeline(self, queue: TaskQueue):
        task = queue.add_task("bad", "task", "action")
        assert task is None

    def test_add_task_with_dependencies(self, queue: TaskQueue):
        p = queue.create_pipeline("P")
        t1 = queue.add_task(p.id, "First", "action1")
        assert t1 is not None and t1.id is not None
        t2 = queue.add_task(p.id, "Second", "action2", depends_on=[t1.id])
        assert t2 is not None and t2.depends_on == [t1.id]

    def test_run_pipeline_not_found(self, queue: TaskQueue):
        import asyncio

        result = asyncio.run(queue.run_pipeline("bad"))
        assert "error" in result

    @pytest.mark.asyncio
    async def test_run_pipeline_empty(self, queue: TaskQueue):
        p = queue.create_pipeline("Empty")
        result = await queue.run_pipeline(p.id)
        assert result["tasks"] == 0

    @pytest.mark.asyncio
    async def test_run_pipeline_skips_no_executor(self, queue: TaskQueue):
        p = queue.create_pipeline("No Exec")
        queue.add_task(p.id, "Unknown", "action", module="nonexistent")
        result = await queue.run_pipeline(p.id)
        assert result["tasks"] == 1
        task = p.tasks[0]
        assert task.status == TaskStatus.FAILED

    def test_get_stats(self, queue: TaskQueue):
        stats = queue.get_stats()
        assert stats["pipelines"] >= 0
        assert "total_tasks" in stats


class TestTask:
    def test_defaults(self):
        t = Task()
        assert t.status == TaskStatus.PENDING
        assert t.max_retries == 2
        assert t.retries == 0
        assert t.duration_ms == 0.0

    def test_with_values(self):
        t = Task(name="Test", action="run", module="chat", params={"key": "val"}, max_retries=3)
        assert t.name == "Test"
        assert t.params == {"key": "val"}
        assert t.max_retries == 3


class TestTaskStatus:
    def test_enum_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.SUCCESS.value == "success"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.SKIPPED.value == "skipped"
