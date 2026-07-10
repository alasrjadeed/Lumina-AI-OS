from __future__ import annotations

from pathlib import Path

import pytest

from core.task_manager.engine import TaskManager
from core.task_manager.models import Task, TaskPriority, TaskStatus, TaskStep


@pytest.fixture
def tm(tmp_path: Path) -> TaskManager:
    return TaskManager(storage_path=str(tmp_path / "tasks.json"))


class TestTaskManager:
    def test_create_task(self, tm: TaskManager):
        task = tm.create_task("Test Task", "A test")
        assert task.name == "Test Task"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.NORMAL

    def test_create_task_with_priority(self, tm: TaskManager):
        task = tm.create_task("High", priority=TaskPriority.HIGH, tags=["urgent"])
        assert task.priority == TaskPriority.HIGH
        assert "urgent" in task.tags

    def test_get_task(self, tm: TaskManager):
        task = tm.create_task("Find Me")
        assert tm.get_task(task.id) is task

    def test_get_task_missing(self, tm: TaskManager):
        assert tm.get_task("nonexistent") is None

    def test_list_tasks_empty(self, tm: TaskManager):
        assert tm.list_tasks() == []

    def test_list_tasks_multiple(self, tm: TaskManager):
        tm.create_task("A")
        tm.create_task("B")
        assert len(tm.list_tasks()) == 2

    def test_list_tasks_filter_status(self, tm: TaskManager):
        t = tm.create_task("Pending")
        t.status = TaskStatus.RUNNING
        tm.list_tasks(status="pending")
        running = tm.list_tasks(status="running")
        assert len(running) == 1
        assert running[0].name == "Pending"

    def test_list_tasks_filter_tag(self, tm: TaskManager):
        tm.create_task("A", tags=["x"])
        tm.create_task("B", tags=["y"])
        tm.create_task("C", tags=["x"])
        assert len(tm.list_tasks(tag="x")) == 2

    def test_list_tasks_limit(self, tm: TaskManager):
        for i in range(10):
            tm.create_task(f"Task {i}")
        assert len(tm.list_tasks(limit=3)) == 3

    def test_delete_task(self, tm: TaskManager):
        t = tm.create_task("Delete Me")
        assert tm.delete_task(t.id) is True
        assert tm.get_task(t.id) is None

    def test_delete_task_missing(self, tm: TaskManager):
        assert tm.delete_task("bad") is False

    def test_add_step(self, tm: TaskManager):
        t = tm.create_task("Multi Step")
        step = tm.add_step(t.id, "Step 1", agent="writer", params={"topic": "AI"})
        assert step is not None
        assert step.name == "Step 1"
        assert step.agent == "writer"

    def test_add_step_missing_task(self, tm: TaskManager):
        assert tm.add_step("bad", "Step") is None

    def test_add_step_with_deps(self, tm: TaskManager):
        t = tm.create_task("Dep")
        s1 = tm.add_step(t.id, "First")
        assert s1 is not None and s1.id is not None
        s2 = tm.add_step(t.id, "Second", depends_on=[s1.id])
        assert s2 is not None and s2.depends_on == [s1.id]

    def test_pause_and_resume(self, tm: TaskManager):
        t = tm.create_task("Pausable")
        t.status = TaskStatus.RUNNING
        assert tm.pause_task(t.id) is True
        assert t.status == TaskStatus.PAUSED
        assert tm.resume_task(t.id) is True
        assert t.status == TaskStatus.RUNNING

    def test_pause_non_running(self, tm: TaskManager):
        t = tm.create_task("Not Running")
        assert tm.pause_task(t.id) is False

    def test_cancel_task(self, tm: TaskManager):
        t = tm.create_task("Cancellable")
        t.status = TaskStatus.RUNNING
        assert tm.cancel_task(t.id) is True
        assert t.status == TaskStatus.CANCELLED

    def test_cancel_completed_task(self, tm: TaskManager):
        t = tm.create_task("Done")
        t.status = TaskStatus.COMPLETED
        assert tm.cancel_task(t.id) is False

    def test_update_progress(self, tm: TaskManager):
        t = tm.create_task("Progress")
        tm.update_progress(t.id, 50, "Halfway")
        assert t.progress == 50
        assert t.progress_label == "Halfway"

    def test_update_progress_clamped(self, tm: TaskManager):
        t = tm.create_task("Clamp")
        tm.update_progress(t.id, 150)
        assert t.progress == 100
        tm.update_progress(t.id, -10)
        assert t.progress == 0

    def test_update_step_progress(self, tm: TaskManager):
        t = tm.create_task("Steps")
        s = tm.add_step(t.id, "Step A")
        assert s is not None and s.id is not None
        tm.update_step_progress(t.id, s.id, 75, "Almost done")
        assert s.progress == 75

    def test_register_and_trigger_handler(self, tm: TaskManager):
        t = tm.create_task("Handled")
        tm.add_step(t.id, "Step", agent="test_handler")

        async def handler(params):
            return "handled!"

        tm.register_handler("test_handler", handler)

        # We're just testing registration, not full execution
        assert "test_handler" in tm._handlers

    def test_register_handlers_bulk(self, tm: TaskManager):
        async def h1(p):
            return "1"

        async def h2(p):
            return "2"

        tm.register_handlers({"h1": h1, "h2": h2})
        assert set(tm._handlers.keys()) >= {"h1", "h2"}

    def test_stats(self, tm: TaskManager):
        tm.create_task("A")
        tm.create_task("B")
        stats = tm.get_stats()
        assert stats["total"] == 2

    def test_event_listener(self, tm: TaskManager):
        events = []
        tm.on_event(lambda e: events.append(e.type))
        tm.create_task("Eventful")
        assert len(events) >= 1

    def test_persistence(self, tmp_path: Path):
        path = str(tmp_path / "persist.json")
        tm1 = TaskManager(storage_path=path)
        tm1.create_task("Persistent")
        tm2 = TaskManager(storage_path=path)
        assert len(tm2.list_tasks()) == 1

    def test_get_recent_events(self, tm: TaskManager):
        tm.create_task("A")
        tm.create_task("B")
        events = tm.get_recent_events(limit=5)
        assert len(events) >= 2

    def test_run_task_not_found(self, tm: TaskManager):
        import asyncio

        result = asyncio.run(tm.run_task("bad"))
        assert "error" in result

    def test_run_task_empty(self, tm: TaskManager):
        t = tm.create_task("Empty")
        import asyncio

        result = asyncio.run(tm.run_task(t.id))
        assert result["status"] == "completed"


class TestTaskModel:
    def test_defaults(self):
        t = Task()
        assert t.status == TaskStatus.PENDING
        assert t.priority == TaskPriority.NORMAL
        assert t.max_retries == 2
        assert t.steps == []

    def test_completed_steps(self):
        t = Task()
        t.steps = [TaskStep(status=TaskStatus.COMPLETED), TaskStep(status=TaskStatus.FAILED)]
        # completed_steps counts all terminal states (COMPLETED + SKIPPED + FAILED)
        assert t.completed_steps() == 2

    def test_failed_steps(self):
        t = Task()
        t.steps = [TaskStep(status=TaskStatus.FAILED), TaskStep(status=TaskStatus.SKIPPED)]
        assert t.failed_steps() == 1

    def test_emit_event(self):
        t = Task(id="123", name="Test")
        event = t.emit_event("test.event", message="Testing")
        assert event.type == "test.event"
        assert event.task_id == "123"
        assert event.message == "Testing"


class TestTaskStep:
    def test_defaults(self):
        s = TaskStep()
        assert s.status == TaskStatus.PENDING
        assert s.params == {}
        assert s.depends_on == []
        assert s.progress == 0


class TestTaskPriority:
    def test_ordering(self):
        assert TaskPriority.LOW.value == 0
        assert TaskPriority.NORMAL.value == 1
        assert TaskPriority.HIGH.value == 2
        assert TaskPriority.CRITICAL.value == 3


class TestTaskStatus:
    def test_values(self):
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"
        assert TaskStatus.PAUSED.value == "paused"
        assert TaskStatus.CANCELLED.value == "cancelled"
        assert TaskStatus.SKIPPED.value == "skipped"
