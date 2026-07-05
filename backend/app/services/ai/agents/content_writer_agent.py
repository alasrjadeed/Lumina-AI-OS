from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.media.writer_service import WriterService


class ContentWriterAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Content Writer AI",
            role="Content Writer",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.writer = WriterService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "article":
            return await self.writer.write_article(
                params.get("topic", ""),
                params.get("length", "medium"),
                params.get("tone", "professional"),
                params.get("format", "article"),
            )
        elif action == "edit":
            return await self.writer.edit_content(params.get("content", ""), params.get("instructions", ""))
        thought = await self.think(f"Content writing: {action}")
        return {"status": "writer_action", "thought": thought}
