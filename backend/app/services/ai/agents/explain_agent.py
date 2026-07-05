from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent
from backend.app.services.explain.explain_service import ExplainService, ExplainLevel


class ExplainAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Explain AI",
            role="Explanation Specialist",
            ai_engine=ai_engine,
            memory=memory,
        )
        self.explain_service = ExplainService(ai_engine)

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        topic = params.get("topic", "")
        level_str = params.get("level", "intermediate")
        level = ExplainLevel(level_str) if level_str in ("beginner", "intermediate", "expert") else ExplainLevel.INTERMEDIATE
        code = params.get("code")
        content = params.get("content")
        url = params.get("url")
        report_type = params.get("report_type")
        report_data = params.get("report_data")

        if code:
            return await self.explain_service.explain_code(code, params.get("language", ""), level)
        if content:
            return await self.explain_service.explain_document(content, params.get("filename", ""), level)
        if url:
            return await self.explain_service.explain_website(url, params.get("page_content", ""), level)
        if report_type and report_data:
            return await self.explain_service.explain_report(report_type, report_data, level)
        return await self.explain_service.explain_text(topic, level)
