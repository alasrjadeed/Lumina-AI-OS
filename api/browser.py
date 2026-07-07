import json
from fastapi import APIRouter
from pydantic import BaseModel

from core.browser.automation import browser
from core.browser.agent import browser_agent
from core.browser.form_filler import form_filler

router = APIRouter(prefix="/browser", tags=["Browser"])


class NavigateRequest(BaseModel):
    url: str


class ClickRequest(BaseModel):
    selector: str


class FillRequest(BaseModel):
    selector: str
    value: str


class FormAnalyzeRequest(BaseModel):
    html: str


@router.post("/navigate")
async def navigate(req: NavigateRequest):
    await browser.navigate(req.url)
    title = await browser.get_text("title")
    return {"status": "ok", "url": req.url, "title": title}


@router.post("/click")
async def click(req: ClickRequest):
    await browser.click(req.selector)
    return {"status": "ok", "selector": req.selector}


@router.post("/fill")
async def fill(req: FillRequest):
    await browser.fill(req.selector, req.value)
    return {"status": "ok"}


@router.get("/content")
async def get_content():
    html = await browser.get_html()
    text = await browser.get_text("body")
    return {"html": html[:500000], "text": text[:100000]}


@router.get("/links")
async def get_links():
    links = await browser.extract_links()
    return {"links": links}


@router.get("/forms")
async def get_forms():
    forms = await browser.extract_forms()
    return {"forms": forms}


@router.post("/screenshot")
async def screenshot():
    path = await browser.screenshot()
    return {"status": "ok", "path": path}


@router.post("/close")
async def close():
    await browser.close()
    return {"status": "ok"}


@router.post("/form/analyze")
async def analyze_form(req: FormAnalyzeRequest):
    fields = await form_filler.analyze_form(req.html)
    return {"fields": fields}


class AgentTaskRequest(BaseModel):
    task: str
    headless: bool = False


@router.post("/agent")
async def run_agent(req: AgentTaskRequest):
    """AI Browser Agent — execute natural language browser tasks."""
    result = await browser_agent.execute(req.task, headless=req.headless)
    return result
