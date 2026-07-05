from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from backend.app.services.browser.browser_service import BrowserService

router = APIRouter()
_browser: Optional[BrowserService] = None


async def get_browser():
    global _browser
    if _browser is None:
        _browser = BrowserService()
        await _browser.initialize()
    return _browser


class NavigateRequest(BaseModel):
    url: str


class SelectorRequest(BaseModel):
    selector: str


class FillRequest(BaseModel):
    selector: str
    value: str


class EvaluateRequest(BaseModel):
    script: str


@router.post("/navigate")
async def navigate(req: NavigateRequest):
    b = await get_browser()
    return await b.navigate(req.url)


@router.get("/content")
async def get_content():
    b = await get_browser()
    return await b.get_content()


@router.post("/screenshot")
async def screenshot():
    b = await get_browser()
    return await b.screenshot()


@router.post("/click")
async def click(req: SelectorRequest):
    b = await get_browser()
    return await b.click(req.selector)


@router.post("/fill")
async def fill(req: FillRequest):
    b = await get_browser()
    return await b.fill(req.selector, req.value)


@router.post("/evaluate")
async def evaluate(req: EvaluateRequest):
    b = await get_browser()
    return await b.evaluate(req.script)
