"""Build Pipeline API — autonomous code→test→build lifecycle."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.pipeline import pipeline_builder

router = APIRouter(prefix="/pipeline", tags=["Build Pipeline"])


class BuildRequest(BaseModel):
    description: str
    language: str = "python"
    framework: str = ""
    output_dir: str = ""
    headless: bool = True


@router.post("/build")
async def build_project(req: BuildRequest):
    """Launch a full code→test→build pipeline from a description."""
    result = await pipeline_builder.launch(
        description=req.description,
        language=req.language,
        framework=req.framework,
        output_dir=req.output_dir,
        headless=req.headless,
    )
    return result


@router.get("/languages")
async def list_languages():
    """List supported languages and frameworks."""
    return {
        "languages": {
            "python": {"frameworks": ["flask", "fastapi", "django", ""]},
            "js": {"frameworks": ["react", "vue", "nextjs", "express", ""]},
            "ts": {"frameworks": ["react", "vue", "nextjs", "express", ""]},
            "kotlin": {"frameworks": ["android", ""]},
            "go": {"frameworks": [""]},
            "rust": {"frameworks": [""]},
            "java": {"frameworks": ["spring", "android", ""]},
            "html": {"frameworks": [""]},
        }
    }
