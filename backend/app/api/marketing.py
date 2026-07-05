from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.ai.engine import AIEngine
from backend.app.services.marketing.seo_service import SEOService
from backend.app.services.marketing.content_service import ContentService
from backend.app.services.marketing.social_service import SocialMediaService
from backend.app.services.marketing.designer_service import DesignerService
from backend.app.services.marketing.analytics_service import AnalyticsService

router = APIRouter()
ai = AIEngine()
seo = SEOService(ai)
content = ContentService(ai)
social = SocialMediaService(ai)
designer = DesignerService(ai)
analytics = AnalyticsService(ai)


class SEORequest(BaseModel):
    url: str = ""
    content: str = ""


class BlogRequest(BaseModel):
    topic: str
    tone: str = "professional"
    length: str = "medium"


class SocialPostRequest(BaseModel):
    platform: str
    topic: str
    tone: str = "casual"


class LogoRequest(BaseModel):
    brand: str
    industry: str
    style: str = "modern"


@router.post("/seo/analyze")
async def seo_analyze(req: SEORequest):
    return await seo.analyze_page(req.url, req.content)


@router.post("/seo/audit")
async def seo_audit(url: str):
    return await seo.audit(url)


@router.post("/seo/keywords")
async def seo_keywords(topic: str, niche: str = ""):
    return await seo.suggest_keywords(topic, niche)


@router.post("/content/blog")
async def write_blog(req: BlogRequest):
    return await content.write_blog(req.topic, req.tone, req.length)


@router.post("/content/social")
async def social_post(req: SocialPostRequest):
    return await social.create_post(req.platform, req.topic)


@router.post("/content/landing")
async def landing_page(product: str, audience: str, usp: str):
    return await content.write_landing_page(product, audience, usp)


@router.post("/design/logo")
async def logo_design(req: LogoRequest):
    return await designer.generate_logo_description(req.brand, req.industry, req.style)


@router.post("/design/colors")
async def brand_colors(brand: str, industry: str):
    return await designer.generate_brand_colors(brand, industry)


@router.post("/design/banner")
async def banner(purpose: str, dimensions: str = "1200x630"):
    return await designer.generate_banner(purpose, dimensions)


@router.post("/analytics/report")
async def analyze_report(report_data: str, report_type: str = "general"):
    return await analytics.analyze_report(report_data, report_type)
