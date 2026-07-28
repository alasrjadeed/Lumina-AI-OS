from fastapi import APIRouter, HTTPException

from core.meeting_agent import meeting_store

router = APIRouter(prefix="/meetings", tags=["Meeting Agents"])


@router.get("")
async def list_meetings(status: str | None = None):
    return {"meetings": [m.to_dict() for m in meeting_store.list(status)]}


@router.post("")
async def create_meeting(title: str, description: str = "", scheduled_at: str | None = None, duration_minutes: int = 30, participants: str = ""):
    participant_list = [p.strip() for p in participants.split(",") if p.strip()] if participants else []
    meeting = meeting_store.create(title=title, description=description, scheduled_at=scheduled_at, duration_minutes=duration_minutes, participants=participant_list)
    return {"meeting": meeting.to_dict()}


@router.get("/{meeting_id}")
async def get_meeting(meeting_id: str):
    m = meeting_store.get(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting": m.to_dict()}


@router.patch("/{meeting_id}")
async def update_meeting(meeting_id: str, title: str | None = None, description: str | None = None, status: str | None = None, duration_minutes: int | None = None):
    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if status is not None:
        kwargs["status"] = status
    if duration_minutes is not None:
        kwargs["duration_minutes"] = duration_minutes
    m = meeting_store.update(meeting_id, **kwargs)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"meeting": m.to_dict()}


@router.delete("/{meeting_id}")
async def delete_meeting(meeting_id: str):
    ok = meeting_store.delete(meeting_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"deleted": True}


@router.post("/{meeting_id}/notes")
async def add_note(meeting_id: str, content: str, author: str = ""):
    note = meeting_store.add_note(meeting_id, content=content, author=author)
    if not note:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"note": note.to_dict()}


@router.post("/{meeting_id}/actions")
async def add_action(meeting_id: str, text: str, assignee: str = ""):
    item = meeting_store.add_action_item(meeting_id, text=text, assignee=assignee)
    if not item:
        raise HTTPException(status_code=404, detail="Meeting not found")
    return {"action_item": item.to_dict()}


@router.post("/{meeting_id}/actions/{item_id}/toggle")
async def toggle_action(meeting_id: str, item_id: str):
    item = meeting_store.toggle_action(meeting_id, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Action item not found")
    return {"action_item": item.to_dict()}


@router.get("/{meeting_id}/summary")
async def summarize_meeting(meeting_id: str):
    m = meeting_store.get(meeting_id)
    if not m:
        raise HTTPException(status_code=404, detail="Meeting not found")
    summary = {
        "title": m.title,
        "status": m.status,
        "participant_count": len(m.participants),
        "note_count": len(m.notes),
        "action_items": [{"text": a.text, "done": a.done, "assignee": a.assignee} for a in m.action_items],
        "open_actions": len([a for a in m.action_items if not a.done]),
        "done_actions": len([a for a in m.action_items if a.done]),
    }
    return {"summary": summary}
