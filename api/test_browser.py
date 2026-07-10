"""Self-Test Browser API — launch, inspect, audit, screenshot, UI tests."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.browser.test_browser import UITestCase, test_browser

router = APIRouter(prefix="/test-browser", tags=["Test Browser"])


class NavigateRequest(BaseModel):
    url: str
    wait_until: str = "networkidle"


class UITestRequest(BaseModel):
    name: str
    steps: list[dict]
    expected: str = ""


class CompareRequest(BaseModel):
    name: str
    url_before: str
    url_after: str


class InspectRequest(BaseModel):
    selector: str = "body"


@router.post("/launch")
async def launch(headless: bool = Query(True)):
    try:
        await test_browser.launch()
        return {"status": "launched", "headless": headless}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


@router.post("/close")
async def close():
    await test_browser.close()
    return {"status": "closed"}


@router.post("/navigate")
async def navigate(req: NavigateRequest):
    return await test_browser.navigate(req.url, req.wait_until)


@router.post("/inspect/html")
async def inspect_html(req: InspectRequest):
    return await test_browser.inspect_html(req.selector)


@router.post("/inspect/css")
async def inspect_css(req: InspectRequest):
    return await test_browser.inspect_css(req.selector)


@router.post("/inspect/js")
async def inspect_js(expression: str = Query("")):
    return await test_browser.inspect_javascript(expression)


@router.get("/network")
async def network():
    return test_browser.get_network()


@router.get("/console")
async def console():
    return test_browser.get_console()


@router.post("/screenshot")
async def screenshot(name: str = Query("screenshot"), full_page: bool = Query(True)):
    path = await test_browser.screenshot(name, full_page)
    return {"path": path, "name": name}


@router.post("/compare")
async def compare_screenshots(req: CompareRequest):
    comp = await test_browser.compare_screenshots(
        req.name,
        req.url_before,
        req.url_after,
    )
    return comp.to_dict()


@router.post("/ui-test")
async def run_ui_test(req: UITestRequest):
    import uuid

    test = UITestCase(
        id=uuid.uuid4().hex[:12],
        name=req.name,
        steps=req.steps,
        expected=req.expected,
        timestamp=0,
    )
    result = await test_browser.run_ui_test(test)
    return result.to_dict()


@router.post("/audit")
async def audit(url: str = Query("")):
    return await test_browser.full_audit(url)


@router.get("/stats")
async def stats():
    return test_browser.get_stats()
