from typing import Any, Dict
from backend.app.services.ai.agents.base_agent import BaseAgent


class DocumentationAgent(BaseAgent):
    def __init__(self, ai_engine, memory):
        super().__init__(
            name="Documentation AI",
            role="Documentation Specialist",
            ai_engine=ai_engine,
            memory=memory,
        )

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        if action == "generate_docs":
            docs = await self.think(
                f"Generate documentation for:\n{params.get('content', '')}",
                system="You are a technical writer. Generate clear, comprehensive documentation with examples.",
            )
            return {"topic": params.get("topic", ""), "documentation": docs}
        elif action == "readme":
            readme = await self.think(
                f"Generate a README for this project:\n{params.get('project_summary', '')}",
                system="Generate a professional README.md with installation, usage, and API sections.",
            )
            return {"readme": readme}
        elif action == "api_docs":
            api_docs = await self.think(
                f"Generate API documentation for:\n{params.get('api_spec', '')}",
                system="Generate detailed API documentation with endpoints, parameters, and examples.",
            )
            return {"api_docs": api_docs}
        thought = await self.think(f"Documentation: {action}")
        return {"status": "docs_action", "thought": thought}
