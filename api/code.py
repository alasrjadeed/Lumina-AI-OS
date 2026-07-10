"""Code API — generate, review, preview. Upgraded review engine."""

import re
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from core.agents import BaseAgent
from core.code_review.engine import DIMENSIONS, review_engine

LANG_IDS = {
    "python",
    "py",
    "javascript",
    "js",
    "typescript",
    "ts",
    "go",
    "golang",
    "rust",
    "rs",
    "java",
    "kotlin",
    "kt",
    "sql",
    "html",
    "css",
    "dart",
    "flutter",
    "swift",
    "php",
    "c",
    "cpp",
    "c++",
    "csharp",
    "c#",
    "ruby",
    "rb",
    "scala",
    "r",
    "perl",
    "pl",
    "bash",
    "shell",
    "sh",
    "yaml",
    "yml",
    "json",
    "xml",
    "markdown",
    "md",
    "text",
    "node",
    "nodejs",
    "react",
    "vue",
    "angular",
    "svelte",
    "nextjs",
    "nuxt",
}

router = APIRouter(prefix="/code", tags=["Code Generation"])


class CodeRequest(BaseModel):
    description: str
    language: str = "python"
    framework: str | None = None
    mode: str = "quick"


class CodeResponse(BaseModel):
    code: str
    explanation: str
    language: str
    framework: str | None = None
    mode: str = "quick"


class ReviewRequest(BaseModel):
    code: str
    language: str = "python"


CODE_AGENT_PROMPT = """You are Lumina Software Engineer AI.
Generate production-quality code based on the description.
Include clear comments. Return code and explanation."""

MODE_PROMPTS = {
    "quick": "Write concise, minimal code. Prioritize clarity and brevity.",
    "production": (
        "Write production-grade code with error handling, type hints, "
        "logging, and comprehensive comments. "
        "Follow {lang} best practices and design patterns."
    ),
    "explain": (
        "Write clean code with detailed inline comments explaining "
        "each section. Include a thorough explanation of how the code works."
    ),
}


class CodeAgent(BaseAgent):
    name = "SoftwareEngineer"
    system_prompt = CODE_AGENT_PROMPT


code_agent = CodeAgent()

_generation_history: list[dict] = []


@router.post("/generate", response_model=CodeResponse)
async def generate_code(req: CodeRequest):
    mode_prompt = MODE_PROMPTS.get(req.mode, MODE_PROMPTS["quick"])
    framework_hint = f" using {req.framework}" if req.framework else ""

    prompt = (
        f"Language: {req.language}{framework_hint}\n"
        + f"Mode: {req.mode}\n\n"
        + f"Approach: {mode_prompt.format(lang=req.language)}\n\n"
        + f"Task: {req.description}\n\n"
        + "Return your response as:\nCODE:\n```\n...\n```\nEXPLANATION:\n..."
    )

    result = await code_agent.run(prompt)
    if result.status == "error":
        raise HTTPException(status_code=500, detail=result.error)

    output = result.output
    code_section = output
    explanation = ""
    if "```" in output:
        blocks = output.split("```")
        for i, block in enumerate(blocks):
            lang_line = block.strip().split("\n")[0]
            if lang_line in LANG_IDS or i % 2 == 1:
                lines = block.strip().split("\n")
                code_section = "\n".join(lines[1:]) if lines[0] in LANG_IDS else block.strip()
                code_section = code_section.strip()
                break
    if "explanation" in output.lower():
        parts = re.split(r"(?i)(?:explanation|Explanation):?\s*", output)
        if len(parts) > 1:
            explanation = parts[-1].strip()
            if explanation.startswith("```"):
                explanation = explanation.split("```")[0].strip()

    resp = CodeResponse(
        code=code_section,
        explanation=explanation,
        language=req.language,
        framework=req.framework,
        mode=req.mode,
    )

    _generation_history.insert(
        0,
        {
            "id": uuid.uuid4().hex[:8],
            "description": req.description[:120],
            "language": req.language,
            "framework": req.framework,
            "mode": req.mode,
            "code_length": len(code_section),
            "timestamp": datetime.now().isoformat(),
        },
    )
    _generation_history[:] = _generation_history[:50]

    return resp


@router.get("/generate/history")
async def generation_history(limit: int = 20):
    return {"items": _generation_history[:limit], "total": len(_generation_history)}


FRAMEWORKS = {
    "python": ["django", "flask", "fastapi", "sqlalchemy", "pandas", "numpy", "pytest", "asyncio"],
    "javascript": ["node", "express", "react", "vue", "angular", "svelte", "nextjs", "nuxt"],
    "typescript": ["react", "nextjs", "angular", "vue", "nestjs", "express", "typeorm"],
    "java": ["spring", "spring-boot", "hibernate", "jakarta-ee", "junit"],
    "go": ["gin", "fiber", "echo", "chi", "gorm"],
    "rust": ["actix", "axum", "rocket", "tokio", "serde"],
    "kotlin": ["ktor", "spring-boot", "jetpack-compose"],
    "dart": ["flutter"],
    "php": ["laravel", "symfony", "wordpress"],
    "csharp": ["aspnet", "blazor", "entity-framework", "xamarin"],
}


@router.get("/frameworks")
async def list_frameworks(
    language: str = Query("python", description="Language to get frameworks for"),
):
    return {"frameworks": FRAMEWORKS.get(language, [])}


TEMPLATES = [
    {
        "id": "api-crud-py",
        "title": "REST API CRUD",
        "lang": "python",
        "framework": "fastapi",
        "desc": "FastAPI CRUD with async SQLAlchemy",
        "code": """""",
    },
    {
        "id": "api-express",
        "title": "Express REST API",
        "lang": "javascript",
        "framework": "express",
        "desc": "Express.js RESTful API with routing",
        "code": """""",
    },
    {
        "id": "react-component",
        "title": "React Component",
        "lang": "typescript",
        "framework": "react",
        "desc": "Typed React component with props",
        "code": """""",
    },
    {
        "id": "data-science",
        "title": "Data Pipeline",
        "lang": "python",
        "framework": "pandas",
        "desc": "Pandas data loading + cleaning + analysis",
        "code": """""",
    },
    {
        "id": "go-server",
        "title": "HTTP Server",
        "lang": "go",
        "framework": "",
        "desc": "Basic Go HTTP server with handlers",
        "code": """""",
    },
    {
        "id": "rust-cli",
        "title": "CLI Tool",
        "lang": "rust",
        "framework": "",
        "desc": "Rust CLI with clap argument parser",
        "code": """""",
    },
    {
        "id": "sql-query",
        "title": "SQL Query Builder",
        "lang": "sql",
        "framework": "",
        "desc": "Multi-table join + aggregation query",
        "code": """""",
    },
    {
        "id": "bash-script",
        "title": "Bash Automation",
        "lang": "bash",
        "framework": "",
        "desc": "Shell script with argument parsing + loops",
        "code": """""",
    },
    {
        "id": "html-landing",
        "title": "Landing Page",
        "lang": "html",
        "framework": "",
        "desc": "Responsive landing page with CSS grid",
        "code": """""",
    },
    {
        "id": "docker-compose",
        "title": "Docker Compose",
        "lang": "yaml",
        "framework": "",
        "desc": "Multi-service Docker Compose setup",
        "code": """""",
    },
]


@router.get("/templates")
async def list_templates(language: str | None = Query(None, description="Filter by language")):
    items = TEMPLATES if not language else [t for t in TEMPLATES if t["lang"] == language]
    return {"templates": items, "total": len(items)}


# ── Upgraded Code Review ──


@router.post("/review")
async def review_code(req: ReviewRequest):
    result = await review_engine.review(req.code, req.language)
    return result.to_dict()


@router.get("/review/dimensions")
async def list_dimensions():
    return {"dimensions": DIMENSIONS}


@router.get("/review/patterns")
async def list_patterns():
    return {"patterns": review_engine.get_all_issue_patterns()}


@router.get("/review/history")
async def review_history(limit: int = 20):
    records = review_engine.get_history(limit)
    return {"reviews": [r.to_dict() for r in records], "total": len(records)}


@router.get("/review/{review_id}")
async def get_review(review_id: str):
    result = review_engine.get_review(review_id)
    if not result:
        return {"error": "Review not found"}, 404
    return {"review": result.to_dict()}


# ── Code Preview ──

_previews: dict[str, dict] = {}


class PreviewRequest(BaseModel):
    code: str
    language: str = "html"


@router.post("/preview")
async def create_preview(req: PreviewRequest):
    pid = str(uuid.uuid4())[:8]
    _previews[pid] = {"code": req.code, "language": req.language}
    return {"preview_url": f"/code/preview/{pid}", "id": pid}


@router.get("/preview/{preview_id}")
async def show_preview(preview_id: str):
    data = _previews.get(preview_id)
    if not data:
        return HTMLResponse("<h1>Preview not found or expired</h1>", status_code=404)

    code = data["code"]
    lang = data["language"]

    if lang == "html":
        html = code
    elif lang in ("javascript", "js"):
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>JS Test</title></head>
<body><div id="app"></div><script>{code}</script></body></html>"""
    elif lang in ("react", "jsx", "tsx"):
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8">
<script src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
<script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
<script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
</head><body><div id="root"></div>
<script type="text/babel">{code}</script></body></html>"""
    elif lang == "css":
        body = '<div style="padding:40px;font-family:sans-serif">'
        body += "<h1>CSS Preview</h1><p>Your styles are applied above.</p></div>"
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>{code}</style></head>
<body>{body}</body></html>"""
    else:
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Code Output</title>
<style>body{{background:#1e1e2e;color:#cdd6f4;font-family:monospace;padding:40px;white-space:pre-wrap}}</style>
</head><body><pre>{code}</pre></body></html>"""

    return HTMLResponse(content=html)
