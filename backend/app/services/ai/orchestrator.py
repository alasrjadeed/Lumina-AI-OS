import asyncio
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from backend.app.services.ai.engine import AIEngine
from backend.app.services.memory.memory_manager import MemoryManager
from backend.app.core.websocket_manager import WebSocketManager
from backend.app.core.lumina_kernel import LuminaKernel
from kernel.events.event import Event

logger = logging.getLogger(__name__)


class OrchestratorState(str, Enum):
    IDLE = "idle"
    PROCESSING = "processing"
    WAITING_FOR_APPROVAL = "waiting_for_approval"
    ERROR = "error"


class AIOrchestrator:
    def __init__(
        self,
        memory_manager: MemoryManager,
        websocket_manager: WebSocketManager,
        kernel: LuminaKernel,
    ):
        self.memory = memory_manager
        self.ws = websocket_manager
        self.kernel = kernel
        self.state = OrchestratorState.IDLE
        self.ai_engine = AIEngine()
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False

    async def initialize(self):
        await self.ai_engine.initialize()
        self._running = True
        asyncio.create_task(self._process_loop())
        logger.info("Orchestrator initialized")

    async def shutdown(self):
        self._running = False
        logger.info("Orchestrator shutdown")

    async def process_command(
        self, command: Union[str, Dict], user_id: Optional[str] = None
    ) -> Dict:
        try:
            if isinstance(command, str):
                parsed = await self._parse_command(command)
            else:
                parsed = command

            task_id = f"task_{datetime.now(timezone.utc).timestamp()}"
            await self.task_queue.put({"id": task_id, "command": parsed, "user_id": user_id})

            await self.kernel.event_bus.publish(
                Event(name="task.created", data={"task_id": task_id, "command": parsed})
            )

            return {"task_id": task_id, "status": "queued"}
        except Exception as e:
            logger.error(f"Command processing failed: {e}")
            return {"status": "error", "message": str(e)}

    async def process_voice_command(self, audio_data: bytes, user_id: Optional[str] = None) -> Dict:
        transcript = await self.ai_engine.speech_to_text(audio_data)
        return await self.process_command(transcript, user_id)

    async def get_task_status(self, task_id: str) -> Dict:
        return {"task_id": task_id, "status": "unknown"}

    async def _parse_command(self, text: str) -> Dict:
        system = "Parse the user's command into a structured task. Return JSON with: action, target, parameters."
        return await self.ai_engine.generate_json(prompt=text, system=system)

    async def _process_loop(self):
        while self._running:
            try:
                task = await self.task_queue.get()
                self.state = OrchestratorState.PROCESSING
                await self._execute_task(task)
                self.state = OrchestratorState.IDLE
                self.task_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Process loop error: {e}")
                self.state = OrchestratorState.ERROR
                await asyncio.sleep(1)

    async def _execute_task(self, task: Dict):
        command = task.get("command", {})
        action = command.get("action", "")
        logger.info(f"Executing task: {action}")

        if action == "explain":
            result = await self.ai_engine.generate(
                prompt=command.get("parameters", {}).get("topic", ""),
                system="Explain this topic clearly and thoroughly.",
            )
        else:
            result = await self.ai_engine.generate(
                prompt=json.dumps(command),
                system="You are Lumina AI, an autonomous AI employee. Execute the requested task.",
            )

        await self.kernel.event_bus.publish(
            Event(name="task.completed", data={"task_id": task["id"], "result": result})
        )
        await self.ws.broadcast(
            {"type": "task_completed", "task_id": task["id"], "result": result},
            user_id=task.get("user_id"),
        )
