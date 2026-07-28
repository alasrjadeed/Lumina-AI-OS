"""Goals & Todos — long-term goals, per-thread goals, and kanban board."""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any


_GOALS_DIR = os.path.expanduser("~/.lumina/goals")

KANBAN_COLUMNS = ["backlog", "todo", "in_progress", "review", "done"]


class GoalStatus(str, Enum):
    active = "active"
    paused = "paused"
    completed = "completed"
    cancelled = "cancelled"


class TodoStatus(str, Enum):
    backlog = "backlog"
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class Goal:
    def __init__(
        self,
        title: str,
        description: str = "",
        status: GoalStatus = GoalStatus.active,
        goal_id: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        tags: list[str] | None = None,
        thread_id: str | None = None,
    ):
        self.id = goal_id or uuid.uuid4().hex[:12]
        self.title = title
        self.description = description
        self.status = status
        self.tags = tags or []
        self.thread_id = thread_id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "tags": self.tags,
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Goal:
        return cls(
            title=d["title"],
            description=d.get("description", ""),
            status=GoalStatus(d.get("status", "active")),
            goal_id=d.get("id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            tags=d.get("tags", []),
            thread_id=d.get("thread_id"),
        )


class Todo:
    def __init__(
        self,
        title: str,
        goal_id: str | None = None,
        description: str = "",
        status: TodoStatus = TodoStatus.backlog,
        todo_id: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        assignee: str = "",
        priority: int = 0,
        thread_id: str | None = None,
    ):
        self.id = todo_id or uuid.uuid4().hex[:12]
        self.title = title
        self.goal_id = goal_id
        self.description = description
        self.status = status
        self.assignee = assignee
        self.priority = priority
        self.thread_id = thread_id
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()
        self.updated_at = updated_at or self.created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "goal_id": self.goal_id,
            "description": self.description,
            "status": self.status.value,
            "assignee": self.assignee,
            "priority": self.priority,
            "thread_id": self.thread_id,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Todo:
        return cls(
            title=d["title"],
            goal_id=d.get("goal_id"),
            description=d.get("description", ""),
            status=TodoStatus(d.get("status", "backlog")),
            todo_id=d.get("id"),
            created_at=d.get("created_at"),
            updated_at=d.get("updated_at"),
            assignee=d.get("assignee", ""),
            priority=d.get("priority", 0),
            thread_id=d.get("thread_id"),
        )


class GoalStore:
    def __init__(self):
        self._goals: list[Goal] = []
        self._todos: list[Todo] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_GOALS_DIR, exist_ok=True)
        return os.path.join(_GOALS_DIR, name)

    def _load(self) -> None:
        goals_path = self._path("goals.json")
        if os.path.exists(goals_path):
            try:
                with open(goals_path) as f:
                    self._goals = [Goal.from_dict(d) for d in json.load(f)]
            except Exception:
                self._goals = []
        todos_path = self._path("todos.json")
        if os.path.exists(todos_path):
            try:
                with open(todos_path) as f:
                    self._todos = [Todo.from_dict(d) for d in json.load(f)]
            except Exception:
                self._todos = []

    def _save_goals(self) -> None:
        with open(self._path("goals.json"), "w") as f:
            json.dump([g.to_dict() for g in self._goals], f, indent=2)

    def _save_todos(self) -> None:
        with open(self._path("todos.json"), "w") as f:
            json.dump([t.to_dict() for t in self._todos], f, indent=2)

    def create_goal(self, title: str, description: str = "", tags: list[str] | None = None, thread_id: str | None = None) -> Goal:
        goal = Goal(title=title, description=description, tags=tags, thread_id=thread_id)
        self._goals.append(goal)
        self._save_goals()
        return goal

    def list_goals(self, status: GoalStatus | None = None) -> list[Goal]:
        if status:
            return [g for g in self._goals if g.status == status]
        return sorted(self._goals, key=lambda g: g.created_at, reverse=True)

    def get_goal(self, goal_id: str) -> Goal | None:
        for g in self._goals:
            if g.id == goal_id:
                return g
        return None

    def update_goal(self, goal_id: str, **kwargs) -> Goal | None:
        goal = self.get_goal(goal_id)
        if not goal:
            return None
        for key, val in kwargs.items():
            if hasattr(goal, key):
                if key == "status":
                    setattr(goal, key, GoalStatus(val))
                else:
                    setattr(goal, key, val)
        goal.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_goals()
        return goal

    def delete_goal(self, goal_id: str) -> bool:
        for i, g in enumerate(self._goals):
            if g.id == goal_id:
                self._goals.pop(i)
                self._todos = [t for t in self._todos if t.goal_id != goal_id]
                self._save_goals()
                self._save_todos()
                return True
        return False

    def create_todo(self, title: str, goal_id: str | None = None, description: str = "", priority: int = 0, thread_id: str | None = None) -> Todo:
        todo = Todo(title=title, goal_id=goal_id, description=description, priority=priority, thread_id=thread_id)
        self._todos.append(todo)
        self._save_todos()
        return todo

    def list_todos(self, status: TodoStatus | None = None, goal_id: str | None = None) -> list[Todo]:
        results = list(self._todos)
        if status:
            results = [t for t in results if t.status == status]
        if goal_id:
            results = [t for t in results if t.goal_id == goal_id]
        return sorted(results, key=lambda t: (-t.priority, t.created_at))

    def get_todo(self, todo_id: str) -> Todo | None:
        for t in self._todos:
            if t.id == todo_id:
                return t
        return None

    def update_todo(self, todo_id: str, **kwargs) -> Todo | None:
        todo = self.get_todo(todo_id)
        if not todo:
            return None
        for key, val in kwargs.items():
            if hasattr(todo, key):
                if key == "status":
                    setattr(todo, key, TodoStatus(val))
                else:
                    setattr(todo, key, val)
        todo.updated_at = datetime.now(timezone.utc).isoformat()
        self._save_todos()
        return todo

    def move_todo(self, todo_id: str, new_status: TodoStatus) -> Todo | None:
        return self.update_todo(todo_id, status=new_status)

    def delete_todo(self, todo_id: str) -> bool:
        for i, t in enumerate(self._todos):
            if t.id == todo_id:
                self._todos.pop(i)
                self._save_todos()
                return True
        return False

    def get_kanban(self) -> dict[str, list[dict]]:
        board = {col: [] for col in KANBAN_COLUMNS}
        for todo in self._todos:
            col = todo.status.value if todo.status.value in KANBAN_COLUMNS else "backlog"
            todo_dict = todo.to_dict()
            if todo.goal_id:
                goal = self.get_goal(todo.goal_id)
                if goal:
                    todo_dict["goal_title"] = goal.title
            board[col].append(todo_dict)
        return board

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_goals": len(self._goals),
            "active_goals": len([g for g in self._goals if g.status == GoalStatus.active]),
            "completed_goals": len([g for g in self._goals if g.status == GoalStatus.completed]),
            "total_todos": len(self._todos),
            "done_todos": len([t for t in self._todos if t.status == TodoStatus.done]),
            "in_progress_todos": len([t for t in self._todos if t.status == TodoStatus.in_progress]),
        }


goal_store = GoalStore()
