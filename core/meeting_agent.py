from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any

_MEETINGS_DIR = os.path.expanduser("~/.lumina/meetings")


class Meeting:
    def __init__(
        self,
        title: str,
        description: str = "",
        scheduled_at: str | None = None,
        duration_minutes: int = 30,
        participants: list[str] | None = None,
        meeting_id: str | None = None,
        created_at: str | None = None,
        status: str = "scheduled",
    ):
        self.id = meeting_id or uuid.uuid4().hex[:12]
        self.title = title
        self.description = description
        self.scheduled_at = scheduled_at or datetime.now(timezone.utc).isoformat()
        self.duration_minutes = duration_minutes
        self.participants = participants or []
        self.status = status  # scheduled, in_progress, completed, cancelled
        self.notes: list[MeetingNote] = []
        self.action_items: list[ActionItem] = []
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "scheduled_at": self.scheduled_at,
            "duration_minutes": self.duration_minutes,
            "participants": self.participants,
            "status": self.status,
            "notes": [n.to_dict() for n in self.notes],
            "action_items": [a.to_dict() for a in self.action_items],
            "created_at": self.created_at,
            "note_count": len(self.notes),
            "action_count": len(self.action_items),
        }

    @classmethod
    def from_dict(cls, d: dict) -> Meeting:
        m = cls(
            title=d["title"],
            description=d.get("description", ""),
            scheduled_at=d.get("scheduled_at"),
            duration_minutes=d.get("duration_minutes", 30),
            participants=d.get("participants", []),
            meeting_id=d.get("id"),
            created_at=d.get("created_at"),
            status=d.get("status", "scheduled"),
        )
        m.notes = [MeetingNote.from_dict(n) for n in d.get("notes", [])]
        m.action_items = [ActionItem.from_dict(a) for a in d.get("action_items", [])]
        return m


class MeetingNote:
    def __init__(
        self,
        content: str,
        author: str = "",
        note_id: str | None = None,
        created_at: str | None = None,
    ):
        self.id = note_id or uuid.uuid4().hex[:8]
        self.content = content
        self.author = author
        self.created_at = created_at or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {"id": self.id, "content": self.content, "author": self.author, "created_at": self.created_at}

    @classmethod
    def from_dict(cls, d: dict) -> MeetingNote:
        return cls(
            content=d["content"],
            author=d.get("author", ""),
            note_id=d.get("id"),
            created_at=d.get("created_at"),
        )


class ActionItem:
    def __init__(
        self,
        text: str,
        assignee: str = "",
        done: bool = False,
        item_id: str | None = None,
    ):
        self.id = item_id or uuid.uuid4().hex[:8]
        self.text = text
        self.assignee = assignee
        self.done = done

    def to_dict(self) -> dict:
        return {"id": self.id, "text": self.text, "assignee": self.assignee, "done": self.done}

    @classmethod
    def from_dict(cls, d: dict) -> ActionItem:
        return cls(
            text=d["text"],
            assignee=d.get("assignee", ""),
            done=d.get("done", False),
            item_id=d.get("id"),
        )


class MeetingStore:
    def __init__(self):
        self._meetings: list[Meeting] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_MEETINGS_DIR, exist_ok=True)
        return os.path.join(_MEETINGS_DIR, name)

    def _load(self) -> None:
        path = self._path("meetings.json")
        if os.path.exists(path):
            try:
                with open(path) as f:
                    self._meetings = [Meeting.from_dict(d) for d in json.load(f)]
            except Exception:
                self._meetings = []

    def _save(self) -> None:
        with open(self._path("meetings.json"), "w") as f:
            json.dump([m.to_dict() for m in self._meetings], f, indent=2)

    def create(self, title: str, description: str = "", scheduled_at: str | None = None, duration_minutes: int = 30, participants: list[str] | None = None) -> Meeting:
        meeting = Meeting(title=title, description=description, scheduled_at=scheduled_at, duration_minutes=duration_minutes, participants=participants)
        self._meetings.append(meeting)
        self._save()
        return meeting

    def list(self, status: str | None = None) -> list[Meeting]:
        if status:
            return [m for m in self._meetings if m.status == status]
        return sorted(self._meetings, key=lambda m: m.scheduled_at, reverse=True)

    def get(self, meeting_id: str) -> Meeting | None:
        for m in self._meetings:
            if m.id == meeting_id:
                return m
        return None

    def update(self, meeting_id: str, **kwargs) -> Meeting | None:
        m = self.get(meeting_id)
        if not m:
            return None
        for k, v in kwargs.items():
            if hasattr(m, k) and k not in ("notes", "action_items"):
                setattr(m, k, v)
        self._save()
        return m

    def delete(self, meeting_id: str) -> bool:
        for i, m in enumerate(self._meetings):
            if m.id == meeting_id:
                self._meetings.pop(i)
                self._save()
                return True
        return False

    def add_note(self, meeting_id: str, content: str, author: str = "") -> MeetingNote | None:
        m = self.get(meeting_id)
        if not m:
            return None
        note = MeetingNote(content=content, author=author)
        m.notes.append(note)
        self._save()
        return note

    def add_action_item(self, meeting_id: str, text: str, assignee: str = "") -> ActionItem | None:
        m = self.get(meeting_id)
        if not m:
            return None
        item = ActionItem(text=text, assignee=assignee)
        m.action_items.append(item)
        self._save()
        return item

    def toggle_action(self, meeting_id: str, item_id: str) -> ActionItem | None:
        m = self.get(meeting_id)
        if not m:
            return None
        for a in m.action_items:
            if a.id == item_id:
                a.done = not a.done
                self._save()
                return a
        return None


meeting_store = MeetingStore()
