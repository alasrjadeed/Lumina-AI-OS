from fastapi import APIRouter
from pydantic import BaseModel

from core.seo.analytics import seo

router = APIRouter(prefix="/seo", tags=["SEO"])


class SiteRequest(BaseModel):
    url: str
    name: str = ""


class PageAnalysis(BaseModel):
    html: str
    url: str = ""


class MetaRequest(BaseModel):
    content: str
    focus_keyword: str = ""


@router.get("/sites")
async def list_sites():
    return {"sites": seo.list_sites()}


@router.post("/sites")
async def add_site(req: SiteRequest):
    return seo.add_site(req.url, req.name)


@router.post("/analyze")
async def analyze_page(req: PageAnalysis):
    result = await seo.analyze_page(req.html, req.url)
    return result


@router.post("/meta")
async def generate_meta(req: MetaRequest):
    result = await seo.generate_meta(req.content, req.focus_keyword)
    return result


@router.get("/history")
async def audit_history(limit: int = 20):
    return {"audits": seo.get_audit_history(limit)}
