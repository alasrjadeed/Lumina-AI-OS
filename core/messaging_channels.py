from __future__ import annotations

import json
import os
import time
import uuid
from typing import Any

_CHANNELS_DIR = os.path.expanduser("~/.lumina/channels")

CHANNEL_TYPES = ["whatsapp", "email", "sms", "telegram", "slack", "custom"]
CHANNEL_DIRECTIONS = ["inbound", "outbound", "both"]


class Message:
    def __init__(
        self,
        channel: str,
        direction: str,
        content: str,
        sender: str = "",
        recipient: str = "",
        subject: str = "",
        message_id: str | None = None,
        timestamp: float | None = None,
        read: bool = False,
        channel_message_id: str = "",
    ):
        self.id = message_id or uuid.uuid4().hex[:12]
        self.channel = channel
        self.direction = direction  # inbound / outbound
        self.content = content
        self.sender = sender
        self.recipient = recipient
        self.subject = subject
        self.timestamp = timestamp or time.time()
        self.read = read
        self.channel_message_id = channel_message_id

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "channel": self.channel,
            "direction": self.direction,
            "content": self.content,
            "sender": self.sender,
            "recipient": self.recipient,
            "subject": self.subject,
            "timestamp": self.timestamp,
            "read": self.read,
            "channel_message_id": self.channel_message_id,
        }

    @classmethod
    def from_dict(cls, d: dict) -> Message:
        return cls(
            channel=d["channel"],
            direction=d.get("direction", "inbound"),
            content=d.get("content", ""),
            sender=d.get("sender", ""),
            recipient=d.get("recipient", ""),
            subject=d.get("subject", ""),
            message_id=d.get("id"),
            timestamp=d.get("timestamp"),
            read=d.get("read", False),
            channel_message_id=d.get("channel_message_id", ""),
        )


class ChannelConfig:
    def __init__(
        self,
        channel_type: str,
        name: str,
        enabled: bool = True,
        config: dict[str, Any] | None = None,
        channel_id: str | None = None,
    ):
        self.id = channel_id or uuid.uuid4().hex[:8]
        self.type = channel_type
        self.name = name
        self.enabled = enabled
        self.config = config or {}

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "name": self.name, "enabled": self.enabled, "config": self.config}

    @classmethod
    def from_dict(cls, d: dict) -> ChannelConfig:
        return cls(
            channel_type=d["type"],
            name=d.get("name", ""),
            enabled=d.get("enabled", True),
            config=d.get("config", {}),
            channel_id=d.get("id"),
        )


class ChannelStore:
    def __init__(self):
        self._messages: list[Message] = []
        self._channels: list[ChannelConfig] = []
        self._load()

    def _path(self, name: str) -> str:
        os.makedirs(_CHANNELS_DIR, exist_ok=True)
        return os.path.join(_CHANNELS_DIR, name)

    def _load(self) -> None:
        msg_path = self._path("messages.json")
        if os.path.exists(msg_path):
            try:
                with open(msg_path) as f:
                    self._messages = [Message.from_dict(d) for d in json.load(f)]
            except Exception:
                self._messages = []
        ch_path = self._path("channels.json")
        if os.path.exists(ch_path):
            try:
                with open(ch_path) as f:
                    self._channels = [ChannelConfig.from_dict(d) for d in json.load(f)]
            except Exception:
                self._channels = []
        if not self._channels:
            defaults = [
                ChannelConfig("whatsapp", "WhatsApp", enabled=True, config={"number": ""}),
                ChannelConfig("email", "Email", enabled=True, config={"address": ""}),
                ChannelConfig("telegram", "Telegram", enabled=False, config={"bot_token": ""}),
            ]
            self._channels = defaults
            self._save_channels()

    def _save_messages(self) -> None:
        with open(self._path("messages.json"), "w") as f:
            json.dump([m.to_dict() for m in self._messages], f, indent=2)

    def _save_channels(self) -> None:
        with open(self._path("channels.json"), "w") as f:
            json.dump([c.to_dict() for c in self._channels], f, indent=2)

    def add_message(self, channel: str, direction: str, content: str, sender: str = "", recipient: str = "", subject: str = "") -> Message:
        msg = Message(channel=channel, direction=direction, content=content, sender=sender, recipient=recipient, subject=subject)
        self._messages.append(msg)
        self._save_messages()
        return msg

    def list_messages(self, channel: str | None = None, limit: int = 50, unread_only: bool = False) -> list[Message]:
        results = list(self._messages)
        if channel:
            results = [m for m in results if m.channel == channel]
        if unread_only:
            results = [m for m in results if not m.read]
        results.sort(key=lambda m: m.timestamp, reverse=True)
        return results[:limit]

    def mark_read(self, message_id: str) -> bool:
        for m in self._messages:
            if m.id == message_id:
                m.read = True
                self._save_messages()
                return True
        return False

    def mark_all_read(self, channel: str | None = None) -> int:
        count = 0
        for m in self._messages:
            if not m.read and (channel is None or m.channel == channel):
                m.read = True
                count += 1
        if count:
            self._save_messages()
        return count

    def delete_message(self, message_id: str) -> bool:
        for i, m in enumerate(self._messages):
            if m.id == message_id:
                self._messages.pop(i)
                self._save_messages()
                return True
        return False

    def get_unread_count(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for m in self._messages:
            if not m.read:
                counts[m.channel] = counts.get(m.channel, 0) + 1
        return counts

    def get_channels(self) -> list[ChannelConfig]:
        return self._channels

    def update_channel(self, channel_id: str, **kwargs) -> ChannelConfig | None:
        for c in self._channels:
            if c.id == channel_id:
                for k, v in kwargs.items():
                    if hasattr(c, k):
                        setattr(c, k, v)
                self._save_channels()
                return c
        return None

    def get_stats(self) -> dict:
        return {
            "total_messages": len(self._messages),
            "unread": sum(1 for m in self._messages if not m.read),
            "channels": len(self._channels),
            "by_channel": {t: len([m for m in self._messages if m.channel == t]) for t in set(m.channel for m in self._messages)},
        }


channel_store = ChannelStore()
