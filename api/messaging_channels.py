from fastapi import APIRouter

from core.messaging_channels import channel_store

router = APIRouter(prefix="/channels", tags=["Messaging Channels"])


@router.get("/inbox")
async def get_inbox(channel: str | None = None, limit: int = 50, unread_only: bool = False):
    messages = channel_store.list_messages(channel=channel, limit=limit, unread_only=unread_only)
    return {"messages": [m.to_dict() for m in messages], "total": len(messages)}


@router.post("/inbox/send")
async def send_message(channel: str, content: str, sender: str = "", recipient: str = "", subject: str = ""):
    msg = channel_store.add_message(channel=channel, direction="outbound", content=content, sender=sender, recipient=recipient, subject=subject)
    return {"message": msg.to_dict()}


@router.post("/inbox/receive")
async def receive_message(channel: str, content: str, sender: str = "", recipient: str = "", subject: str = ""):
    msg = channel_store.add_message(channel=channel, direction="inbound", content=content, sender=sender, recipient=recipient, subject=subject)
    return {"message": msg.to_dict()}


@router.get("/inbox/unread")
async def get_unread_counts():
    return {"unread": channel_store.get_unread_count()}


@router.post("/inbox/{message_id}/read")
async def mark_read(message_id: str):
    ok = channel_store.mark_read(message_id)
    return {"ok": ok}


@router.post("/inbox/read-all")
async def mark_all_read(channel: str | None = None):
    count = channel_store.mark_all_read(channel=channel)
    return {"marked_read": count}


@router.delete("/inbox/{message_id}")
async def delete_message(message_id: str):
    ok = channel_store.delete_message(message_id)
    return {"deleted": ok}


@router.get("/config")
async def get_channels():
    return {"channels": [c.to_dict() for c in channel_store.get_channels()]}


@router.patch("/config/{channel_id}")
async def update_channel(channel_id: str, name: str | None = None, enabled: bool | None = None, config: str | None = None):
    kwargs = {}
    if name is not None:
        kwargs["name"] = name
    if enabled is not None:
        kwargs["enabled"] = enabled
    if config is not None:
        import json as _json
        try:
            kwargs["config"] = _json.loads(config)
        except Exception:
            pass
    ch = channel_store.update_channel(channel_id, **kwargs)
    if not ch:
        return {"error": "Channel not found"}, 404
    return {"channel": ch.to_dict()}


@router.get("/stats")
async def get_stats():
    return channel_store.get_stats()
