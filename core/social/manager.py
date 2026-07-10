"""Social Media Manager — Facebook/Instagram page & content management."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from core.log import log


@dataclass
class Post:
    """A social media post."""

    id: str = ""
    platform: str = "facebook"
    content: str = ""
    media_urls: list[str] = field(default_factory=list)
    scheduled: float = 0.0
    status: str = "draft"
    published: float = 0.0
    engagement: dict = field(default_factory=lambda: {"likes": 0, "comments": 0, "shares": 0})


@dataclass
class Page:
    """A Facebook page or Instagram account."""

    id: str = ""
    name: str = ""
    platform: str = "facebook"
    category: str = ""
    url: str = ""
    followers: int = 0
    description: str = ""
    logo_url: str = ""
    cover_url: str = ""
    website: str = ""
    email: str = ""
    phone: str = ""
    status: str = "active"


class SocialManager:
    """Manage Facebook pages, Instagram accounts, posts, and ads."""

    def __init__(self, storage_path: str = "social_data.json"):
        self.storage_path = storage_path
        self._pages: dict[str, Page] = {}
        self._posts: list[Post] = []
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path) as f:
                data = json.load(f)
            for p in data.get("pages", []):
                self._pages[p["id"]] = Page(**p)
            self._posts = [Post(**p) for p in data.get("posts", [])]
        except Exception:
            pass

    def _save(self) -> None:
        with open(self.storage_path, "w") as f:
            json.dump(
                {
                    "pages": [p.__dict__ for p in self._pages.values()],
                    "posts": [p.__dict__ for p in self._posts],
                },
                f,
                indent=2,
            )

    # ── Pages ──

    def add_page(
        self,
        name: str,
        platform: str = "facebook",
        url: str = "",
        category: str = "",
        description: str = "",
    ) -> Page:
        pid = f"page_{int(time.time())}_{len(self._pages)}"
        page = Page(
            id=pid,
            name=name,
            platform=platform,
            url=url,
            category=category,
            description=description,
        )
        self._pages[pid] = page
        self._save()
        log.info("Social page added: %s (%s)", name, platform)
        return page

    def get_page(self, page_id: str) -> Page | None:
        return self._pages.get(page_id)

    def list_pages(self, platform: str = "") -> list[Page]:
        if platform:
            return [p for p in self._pages.values() if p.platform == platform]
        return list(self._pages.values())

    def update_page(self, page_id: str, **kwargs: Any) -> Page | None:
        page = self._pages.get(page_id)
        if not page:
            return None
        for key, value in kwargs.items():
            if hasattr(page, key):
                setattr(page, key, value)
        self._save()
        return page

    def delete_page(self, page_id: str) -> bool:
        if page_id in self._pages:
            del self._pages[page_id]
            self._save()
            return True
        return False

    # ── Posts ──

    def create_post(
        self,
        content: str,
        platform: str = "facebook",
        media_urls: list[str] | None = None,
        scheduled: float = 0.0,
    ) -> Post:
        pid = f"post_{int(time.time())}_{len(self._posts)}"
        post = Post(
            id=pid,
            platform=platform,
            content=content,
            media_urls=media_urls or [],
            scheduled=scheduled,
        )
        self._posts.append(post)
        self._save()
        return post

    def list_posts(self, platform: str = "", status: str = "", limit: int = 50) -> list[Post]:
        results = list(self._posts)
        if platform:
            results = [p for p in results if p.platform == platform]
        if status:
            results = [p for p in results if p.status == status]
        return sorted(results, key=lambda p: p.scheduled or p.published, reverse=True)[:limit]

    def update_post(self, post_id: str, **kwargs: Any) -> Post | None:
        for post in self._posts:
            if post.id == post_id:
                for key, value in kwargs.items():
                    if hasattr(post, key):
                        setattr(post, key, value)
                self._save()
                return post
        return None

    def delete_post(self, post_id: str) -> bool:
        before = len(self._posts)
        self._posts = [p for p in self._posts if p.id != post_id]
        if len(self._posts) < before:
            self._save()
            return True
        return False

    def get_scheduled(self) -> list[Post]:
        return [p for p in self._posts if p.status == "draft" and p.scheduled > 0]

    def get_published(self) -> list[Post]:
        return [p for p in self._posts if p.status == "published"]

    # ── Automation via Browser Agent ──

    async def publish_via_browser(self, post_id: str, headless: bool = False) -> dict:
        """Use Browser Agent to publish a post on Facebook/Instagram."""
        from core.browser.agent import browser_agent

        post = next((p for p in self._posts if p.id == post_id), None)
        if not post:
            return {"error": "Post not found"}

        platform_url = (
            "https://business.facebook.com"
            if post.platform == "facebook"
            else "https://instagram.com"
        )
        task = (
            f"Go to {platform_url}, log in if needed, navigate to the "
            f"creator studio / posts section. "
            f"Create a new post with the following content:\n\n{post.content}\n\n"
            f"Publish the post. Report back what happened."
        )
        result = await browser_agent.execute(task, headless=headless)
        post.status = "published"
        post.published = time.time()
        self._save()
        return result

    async def upload_page_photo(
        self, page_id: str, image_url: str, photo_type: str = "logo", headless: bool = False
    ) -> dict:
        """Use Browser Agent to upload a logo or cover photo to a Facebook page."""
        from core.browser.agent import browser_agent

        page = self._pages.get(page_id)
        if not page:
            return {"error": "Page not found"}

        field = "logo_url" if photo_type == "logo" else "cover_url"
        task = (
            f"Go to https://business.facebook.com, navigate to the page '{page.name}', "
            f"go to settings, and upload a new {photo_type} photo from this URL: {image_url}. "
            f"Save and confirm."
        )
        result = await browser_agent.execute(task, headless=headless)
        setattr(page, field, image_url)
        self._save()
        return result

    async def reply_to_comments(
        self, page_id: str, reply_text: str, headless: bool = False
    ) -> dict:
        """Use Browser Agent to reply to recent comments on a page."""
        from core.browser.agent import browser_agent

        page = self._pages.get(page_id)
        if not page:
            return {"error": "Page not found"}
        task = (
            f"Go to https://business.facebook.com, navigate to page '{page.name}', "
            f"go to the Inbox or Recent Posts, find recent comments, and reply to each with: "
            f"{reply_text}"
        )
        return await browser_agent.execute(task, headless=headless)

    async def create_ad(
        self, page_id: str, ad_description: str, budget: float = 10.0, headless: bool = False
    ) -> dict:
        """Use Browser Agent to create a Facebook ad."""
        from core.browser.agent import browser_agent

        page = self._pages.get(page_id)
        if not page:
            return {"error": "Page not found"}
        task = (
            f"Go to https://business.facebook.com, navigate to Ads Manager. "
            f"Create a new ad for page '{page.name}' with: {ad_description}. "
            f"Set budget to ${budget}/day. Save as draft."
        )
        return await browser_agent.execute(task, headless=headless)

    # ── Analytics ──

    def get_stats(self) -> dict:
        return {
            "total_pages": len(self._pages),
            "total_posts": len(self._posts),
            "published": len(self.get_published()),
            "scheduled": len(self.get_scheduled()),
            "drafts": len([p for p in self._posts if p.status == "draft" and p.scheduled == 0]),
            "facebook_pages": len([p for p in self._pages.values() if p.platform == "facebook"]),
            "instagram_accounts": len(
                [p for p in self._pages.values() if p.platform == "instagram"]
            ),
        }


social = SocialManager()
