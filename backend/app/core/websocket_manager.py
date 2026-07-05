import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    def __init__(self):
        self._connections: Dict[str, Set[WebSocket]] = {}
        self._metadata: Dict[WebSocket, Dict[str, Any]] = {}

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        uid = user_id or "anonymous"
        self._connections.setdefault(uid, set()).add(websocket)
        self._metadata[websocket] = {
            "user_id": uid,
            "connected_at": datetime.now(timezone.utc),
        }
        logger.info(f"WS connected: {uid}")

    def disconnect(self, websocket: WebSocket):
        meta = self._metadata.pop(websocket, None)
        if meta:
            uid = meta["user_id"]
            self._connections.get(uid, set()).discard(websocket)
            if not self._connections.get(uid):
                self._connections.pop(uid, None)

    async def send(self, message: Any, websocket: WebSocket):
        try:
            if isinstance(message, dict):
                await websocket.send_json(message)
            else:
                await websocket.send_text(str(message))
        except Exception as e:
            logger.error(f"WS send error: {e}")

    async def broadcast(self, message: Any, user_id: Optional[str] = None):
        targets = []
        if user_id:
            targets = list(self._connections.get(user_id, set()))
        else:
            for conns in self._connections.values():
                targets.extend(conns)
        for ws in targets:
            await self.send(message, ws)

    def active_connections(self) -> int:
        return sum(len(conns) for conns in self._connections.values())
