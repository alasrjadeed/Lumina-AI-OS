"""Social Media API — Facebook & Instagram management."""

from fastapi import APIRouter
from pydantic import BaseModel

from core.social.manager import social

router = APIRouter(prefix="/social", tags=["Social"])


class PageCreate(BaseModel):
    name: str
    platform: str = "facebook"
    url: str = ""
    category: str = ""
    description: str = ""


class PostCreate(BaseModel):
    content: str
    platform: str = "facebook"
    media_urls: list[str] = []
    scheduled: float = 0.0


@router.get("/stats")
async def get_stats():
    return social.get_stats()


@router.get("/pages")
async def list_pages(platform: str = ""):
    return {"pages": [{"id": p.id, "name": p.name, "platform": p.platform,
                        "url": p.url, "category": p.category, "followers": p.followers,
                        "status": p.status} for p in social.list_pages(platform)]}


@router.post("/pages")
async def create_page(req: PageCreate):
    p = social.add_page(req.name, req.platform, req.url, req.category, req.description)
    return {"id": p.id, "name": p.name, "platform": p.platform}


@router.delete("/pages/{page_id}")
async def delete_page(page_id: str):
    return {"deleted": social.delete_page(page_id)}


@router.post("/pages/{page_id}/upload-photo")
async def upload_photo(page_id: str, image_url: str, photo_type: str = "logo", headless: bool = False):
    result = await social.upload_page_photo(page_id, image_url, photo_type, headless=headless)
    return result


@router.get("/posts")
async def list_posts(platform: str = "", status: str = ""):
    return {"posts": [{"id": p.id, "platform": p.platform, "content": p.content[:100],
                        "status": p.status, "scheduled": p.scheduled,
                        "engagement": p.engagement} for p in social.list_posts(platform, status)]}


@router.post("/posts")
async def create_post(req: PostCreate):
    p = social.create_post(req.content, req.platform, req.media_urls, req.scheduled)
    return {"id": p.id, "content": p.content[:50], "status": p.status}


@router.delete("/posts/{post_id}")
async def delete_post(post_id: str):
    return {"deleted": social.delete_post(post_id)}


@router.post("/posts/{post_id}/publish")
async def publish_post(post_id: str, headless: bool = False):
    result = await social.publish_via_browser(post_id, headless=headless)
    return result


@router.post("/pages/{page_id}/reply")
async def reply_comments(page_id: str, reply_text: str, headless: bool = False):
    result = await social.reply_to_comments(page_id, reply_text, headless=headless)
    return result


@router.post("/ads/create")
async def create_ad(page_id: str, description: str, budget: float = 10.0, headless: bool = False):
    result = await social.create_ad(page_id, description, budget, headless=headless)
    return result
