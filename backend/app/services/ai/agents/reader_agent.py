from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.reader.reader_service import ReaderService, ReaderCommand


class ReaderAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Reader AI",
            role="Document Reader",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.reader_service = ReaderService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "read_file":
            return await self.reader_service.read_file(params.get("path", ""))
        elif action == "read_text":
            return await self.reader_service.read_text(params.get("text", ""))
        elif action == "command":
            cmd_str = params.get("command", "read")
            cmd = ReaderCommand(cmd_str) if cmd_str in ("read", "pause", "continue", "faster", "slower", "repeat", "goto_page") else ReaderCommand.READ
            return await self.reader_service.command(cmd, **params)
        return {"error": f"Unknown action: {action}"}
