import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class CodingAgentService:
    def __init__(self, ai_engine: AIEngine, workspace: str = "./workspace"):
        self.ai = ai_engine
        self.workspace = Path(workspace)
        self.workspace.mkdir(parents=True, exist_ok=True)

    async def generate_code(self, specification: str, language: str = "python") -> Dict[str, Any]:
        system = f"You are a senior {language} developer. Generate production-ready code with type hints, error handling, and logging. Return the code in a code block."
        code = await self.ai.generate(prompt=specification, system=system)
        return {"language": language, "code": code, "specification": specification}

    async def review_code(self, code: str, language: str = "") -> Dict[str, Any]:
        system = "Review this code for bugs, security issues, performance problems, and style violations. Be specific and actionable."
        review = await self.ai.generate(prompt=f"Review this {language} code:\n{code}", system=system)
        return {"review": review, "language": language}

    async def debug_error(self, code: str, error: str) -> Dict[str, Any]:
        system = "Analyze the error and provide a fix. Explain the root cause."
        analysis = await self.ai.generate(
            prompt=f"Code:\n{code}\n\nError:\n{error}\n\nFind and fix the bug.",
            system=system,
        )
        return {"analysis": analysis, "error": error}

    async def refactor_code(self, code: str, target: str = "performance") -> Dict[str, Any]:
        system = f"Refactor this code for better {target}. Keep the same functionality. Explain what changed and why."
        refactored = await self.ai.generate(prompt=f"Refactor for {target}:\n{code}", system=system)
        return {"refactored": refactored, "target": target}

    async def generate_tests(self, code: str, framework: str = "pytest") -> Dict[str, Any]:
        system = f"Generate {framework} tests covering edge cases, normal cases, and error cases."
        tests = await self.ai.generate(prompt=f"Generate tests for:\n{code}", system=system)
        return {"tests": tests, "framework": framework}
