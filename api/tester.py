"""Self Tester API — automated test, detect, fix, retry."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.tester.engine import tester

router = APIRouter(prefix="/tester", tags=["Tester"])


class TestRequest(BaseModel):
    command: str
    context: str = ""
    timeout: int = 60
    max_attempts: int = 5


@router.post("/run")
async def run_once(req: TestRequest):
    result = await tester.run(req.command, req.timeout)
    return {
        "success": result.success,
        "output": result.output[-500:],
        "error": result.error[-500:],
        "duration_ms": result.duration_ms,
    }


@router.post("/fix")
async def run_with_fix(req: TestRequest):
    return await tester.run_with_fix(req.command, req.context, req.timeout)


@router.post("/pytest")
async def run_pytest(path: str = "."):
    return await tester.run_pytest(path)


@router.post("/typescript")
async def run_typescript():
    return await tester.run_typescript()


@router.post("/lint")
async def run_lint(path: str = "."):
    return await tester.run_lint(path)


@router.get("/history")
async def get_history(limit: int = 20):
    items = tester.get_history(limit)
    return {
        "history": [
            {
                "command": h.command,
                "success": h.success,
                "duration_ms": h.duration_ms,
                "error": h.error[:200],
                "timestamp": getattr(h, "timestamp", ""),
            }
            for h in items
        ],
        "total": len(items),
    }


@router.get("/stats")
async def get_stats():
    items = tester.get_history(200)
    total = len(items)
    passed = sum(1 for h in items if h.success)
    failed = total - passed
    avg_duration = sum(h.duration_ms for h in items) / max(total, 1)
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": round((passed / max(total, 1)) * 100, 1),
        "avg_duration_ms": round(avg_duration, 0),
    }


@router.get("/commands")
async def list_commands():
    return {
        "presets": [
            {"label": "pytest", "cmd": "python -m pytest -v", "category": "python"},
            {"label": "pytest (all)", "cmd": "python -m pytest", "category": "python"},
            {"label": "TypeScript", "cmd": "npx tsc --noEmit", "category": "typescript"},
            {"label": "Ruff Lint", "cmd": "python -m ruff check .", "category": "python"},
            {"label": "Build UI", "cmd": "cd lumina-ui && npx vite build", "category": "build"},
            {
                "label": "Ruff Format",
                "cmd": "python -m ruff format . --check",
                "category": "python",
            },
            {"label": "Pyright", "cmd": "python -m pyright .", "category": "python"},
            {"label": "ESLint", "cmd": "npx eslint src/", "category": "javascript"},
            {"label": "Vitest", "cmd": "npx vitest run", "category": "javascript"},
            {"label": "Go Test", "cmd": "go test ./...", "category": "go"},
        ]
    }
