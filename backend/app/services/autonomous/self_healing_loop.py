import asyncio
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from backend.app.services.ai.engine import AIEngine

logger = logging.getLogger(__name__)


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    FIXED = "fixed"
    SKIPPED = "skipped"


class AutonomousStep:
    def __init__(self, name: str, action: str, params: Dict[str, Any], validation: Optional[str] = None):
        self.name = name
        self.action = action
        self.params = params
        self.validation = validation
        self.status = StepStatus.PENDING
        self.result: Any = None
        self.error: Optional[str] = None
        self.retries = 0
        self.max_retries = 3


class SelfHealingLoop:
    def __init__(self, ai: AIEngine):
        self.ai = ai
        self._history: List[Dict] = []

    async def plan(self, goal: str) -> List[AutonomousStep]:
        system = "You are an autonomous agent. Break down the goal into a sequence of steps. Return JSON array: [{\"name\":\"...\",\"action\":\"...\",\"params\":{},\"validation\":\"...\"}]"
        result = await self.ai.generate_json(prompt=f"Plan steps to accomplish: {goal}", system=system)
        steps_data = result if isinstance(result, list) else result.get("steps", [])
        steps = [AutonomousStep(s.get("name", f"Step {i}"), s.get("action", ""), s.get("params", {}), s.get("validation")) for i, s in enumerate(steps_data)]
        logger.info(f"Planned {len(steps)} steps for: {goal}")
        return steps

    async def execute(self, steps: List[AutonomousStep], executor: Callable) -> Dict[str, Any]:
        results = []
        for i, step in enumerate(steps):
            logger.info(f"Step {i+1}/{len(steps)}: {step.name} [{step.action}]")
            step.status = StepStatus.RUNNING
            success = False
            while step.retries <= step.max_retries and not success:
                try:
                    step.result = await executor(step.action, step.params)
                    if step.validation:
                        valid = await self._validate(step.result, step.validation)
                        if valid:
                            step.status = StepStatus.PASSED
                            success = True
                        else:
                            raise ValueError(f"Validation failed: {step.validation}")
                    else:
                        step.status = StepStatus.PASSED
                        success = True
                except Exception as e:
                    step.retries += 1
                    step.error = str(e)
                    if step.retries <= step.max_retries:
                        await self._auto_fix(step, e)
                        step.status = StepStatus.FIXED if step.retries <= step.max_retries else StepStatus.FAILED
                    else:
                        step.status = StepStatus.FAILED
                    logger.warning(f"Step '{step.name}' retry {step.retries}/{step.max_retries}: {e}")
            results.append({"name": step.name, "status": step.status.value, "result": step.result, "error": step.error, "retries": step.retries})
        self._history.append({"timestamp": datetime.now(timezone.utc).isoformat(), "steps": results})
        return {"steps": results, "total": len(results), "passed": sum(1 for r in results if r["status"] in ("passed", "fixed")), "failed": sum(1 for r in results if r["status"] == "failed")}

    async def _validate(self, result: Any, validation: str) -> bool:
        system = "You are a validator. Check if the result meets the criteria. Respond with just 'true' or 'false'."
        resp = await self.ai.generate(prompt=f"Result: {result}\nValidation: {validation}\nDoes it pass?", system=system)
        return resp.strip().lower() == "true"

    async def _auto_fix(self, step: AutonomousStep, error: Exception):
        system = "You are a debugger. Suggest how to fix the error and retry."
        fix = await self.ai.generate(prompt=f"Step '{step.name}' failed with: {error}\nParams: {step.params}\nHow to fix?", system=system)
        logger.info(f"Auto-fix suggestion: {fix}")

    def get_history(self) -> List[Dict]:
        return self._history
