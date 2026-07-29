import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from api.agents import router as agents_router
from api.analytics_router import router as analytics_router
from api.android import router as android_router
from api.assistant import router as assistant_router
from api.audit_api import router as audit_router
from api.auth import router as auth_router
from api.automation import router as automation_router
from api.browser import router as browser_router
from api.chat import router as chat_router
from api.code import router as code_router
from api.coding_agent import router as coding_agent_router
from api.core_api import router as core_api_router
from api.crm import router as crm_router
from api.desktop import router as desktop_router
from api.email import router as email_router
from api.employee import router as employee_router
from api.learning import router as learning_router
from api.marketing import router as marketing_router
from api.marketplace import router as marketplace_router
from api.middleware.ratelimit import RateLimitMiddleware
from api.multiagent import router as multiagent_router
from api.pipeline import router as pipeline_router
from api.projects import router as projects_router
from api.queue import router as queue_router
from api.seo import router as seo_router
from api.social import router as social_router
from api.system import router as system_router
from api.tasks import router as tasks_router
from api.test_browser import router as test_browser_router
from api.tester import router as tester_router
from api.vault import router as vault_router
from api.vision import router as vision_router
from api.visual_flows import router as visual_flows_router
from api.skills import router as skills_router
from api.presets import router as presets_router
from api.connectors import router as connectors_router
from api.community_skills import router as community_skills_router
from api.voice import router as voice_router
from api.whatsapp import router as whatsapp_router
from api.writer import router as writer_router
from api.goals import router as goals_router
from api.lead_gen import router as lead_gen_router
from api.memory_tree import router as memory_tree_router
from api.workflow_editor import router as workflow_editor_router
from api.meeting_agent import router as meeting_agent_router
from api.messaging_channels import router as messaging_channels_router
from api.model_routing import router as model_routing_router
from api.agent_memory import router as agent_memory_router
from api.multi_modal import router as multi_modal_router
from api.rag_pipeline import router as rag_pipeline_router
from api.agent_chaining import router as agent_chaining_router
from api.tool_framework import router as tool_framework_router
from api.agent_builder import router as agent_builder_router
from api.brain import router as brain_router
from config.settings import settings
from core.agents.content import CONTENT_AGENTS
from core.agents.specialized import SPECIALIZED_AGENTS
from core.agents.lead_gen import lead_gen_agent
from core.android.device import android
from core.automation.engine import engine as automation_engine
from core.browser.automation import browser
from core.browser.form_filler import form_filler
from core.crm.pipeline import crm
from core.desktop.os_automation import desktop
from core.log import log
from core.memory.store import memory
from core.pipeline import pipeline_builder
from core.provider import engine
from core.seo.analytics import seo
from core.task_manager import task_manager
from core.vision import CameraDevice, ObjectDetector, SceneDescriber, VideoStream  # noqa: F401
from core.vision.cortex import VisualCortex  # noqa: F401
from core.auto_fetch import auto_fetch_loop
from core.brain import brain
from core.subconscious import Insight, subconscious_loop
from core.voice import voice_controller
from core.whatsapp.client import whatsapp
from kernel import Kernel
from kernel.events import Event, Subscription

kernel = Kernel()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Initializing Lumina AI OS Kernel...")

    kernel.services.register("ai_engine", engine)
    kernel.services.register("memory", memory)
    kernel.services.register("config", settings)
    kernel.services.register("automation_engine", automation_engine)
    kernel.services.register("form_filler", form_filler)
    kernel.services.register("browser", browser)
    kernel.services.register("desktop", desktop)
    kernel.services.register("android", android)
    kernel.services.register("whatsapp", whatsapp)
    kernel.services.register("crm", crm)
    kernel.services.register("seo", seo)
    kernel.services.register("task_manager", task_manager)
    kernel.services.register("pipeline_builder", pipeline_builder)
    kernel.services.register("voice_controller", voice_controller)
    kernel.services.register("camera_factory", lambda: CameraDevice(device_id=0))
    kernel.services.register("detector_factory", lambda: ObjectDetector())
    kernel.services.register("describer_factory", lambda: SceneDescriber(ai_engine=engine))
    kernel.services.register(
        "cortex_factory",
        lambda: VisualCortex(
            camera=CameraDevice(device_id=0),
            ai_engine=engine,
            enable_faces=True,
            enable_description=True,
        ),
    )
    all_agents = {}
    all_agents.update(SPECIALIZED_AGENTS)
    all_agents.update(CONTENT_AGENTS)
    all_agents["lead_gen"] = lead_gen_agent
    kernel.services.register("brain", brain)
    kernel.services.register("agents", all_agents)

    async def log_event(event: Event) -> None:
        log.debug("Event: %s", event.name)

    await kernel.event_bus.register(Subscription(topic="*", handler=log_event))

    await kernel.init()
    log.info("Kernel initialized. %d services", len(kernel.services.list()))

    async def _subconscious_insight_handler(insight: Insight) -> None:
        log.info("Subconscious insight: %s — %s", insight.title, insight.body[:80])
        await kernel.event_bus.publish(Event(
            name="subconscious.insight",
            payload=insight.to_dict(),
        ))

    bg = os.environ.get("ENABLE_BACKGROUND_TASKS", "0") == "1"

    if bg:
        subconscious_task = asyncio.create_task(
            subconscious_loop(on_insight=_subconscious_insight_handler)
        )

        auto_fetch_task = asyncio.create_task(
            auto_fetch_loop(memory=memory)
        )

        brain_task = asyncio.create_task(
            brain.loop()
        )

    # Auto-start Jarvis voice controller (continuous listening with wake word)
    if bg and voice_controller.recorder.is_available():
        voice_controller.listening = True
        wake_word_mode = True
        log.info("Jarvis voice: continuous mode started (wake_word=%s)", wake_word_mode)
        voice_controller._echo.clear()

        async def _voice_loop():
            while voice_controller.listening:
                try:
                    if wake_word_mode:
                        cmd = await voice_controller.listen_for_wake_word(timeout=5.0)
                    else:
                        cmd = await voice_controller.listen_for_command(timeout=5.0)
                    if not cmd:
                        continue
                    result = await voice_controller.process_command(cmd)
                    reply = result.get("reply", "")
                    if reply:
                        await voice_controller.tts.speak(reply)
                    if result.get("status") == "stopped":
                        voice_controller.listening = True
                except Exception as e:
                    log.warning("Voice loop error: %s", e)
                    await asyncio.sleep(1)

        asyncio.create_task(_voice_loop())
    elif voice_controller.recorder.is_available():
        log.info("Jarvis voice: available (enable with ENABLE_BACKGROUND_TASKS=1)")
    else:
        log.warning("Jarvis voice: no microphone available, voice disabled")

    yield
    log.info("Shutting down...")
    if bg:
        subconscious_task.cancel()
        auto_fetch_task.cancel()
        brain_task.cancel()
    await kernel.shutdown()


app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="The World's First Autonomous AI Employee Operating System",
    lifespan=lifespan,
)

cors_origins = settings.cors_origins.split(",") if settings.cors_origins != "*" else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.debug:
    pass
else:
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.include_router(chat_router)
app.include_router(system_router)
app.include_router(code_router)
app.include_router(agents_router)
app.include_router(automation_router)
app.include_router(browser_router)
app.include_router(desktop_router)
app.include_router(android_router)
app.include_router(whatsapp_router)
app.include_router(crm_router)
app.include_router(seo_router)
app.include_router(auth_router)
app.include_router(vault_router)
app.include_router(social_router)
app.include_router(writer_router)
app.include_router(assistant_router)
app.include_router(learning_router)
app.include_router(tester_router)
app.include_router(queue_router)
app.include_router(employee_router)
app.include_router(tasks_router)
app.include_router(pipeline_router)
app.include_router(voice_router)
app.include_router(vision_router)
app.include_router(coding_agent_router)
app.include_router(email_router)
app.include_router(marketing_router)
app.include_router(marketplace_router)
app.include_router(analytics_router)
app.include_router(test_browser_router)
app.include_router(audit_router)
app.include_router(core_api_router)
app.include_router(multiagent_router)
app.include_router(projects_router)
app.include_router(visual_flows_router)
app.include_router(skills_router)
app.include_router(presets_router)
app.include_router(connectors_router)
app.include_router(community_skills_router)
app.include_router(goals_router)
app.include_router(lead_gen_router)
app.include_router(memory_tree_router)
app.include_router(workflow_editor_router)
app.include_router(meeting_agent_router)
app.include_router(messaging_channels_router)
app.include_router(model_routing_router)
app.include_router(agent_memory_router)
app.include_router(multi_modal_router)
app.include_router(rag_pipeline_router)
app.include_router(agent_chaining_router)
app.include_router(tool_framework_router)
app.include_router(agent_builder_router)
app.include_router(brain_router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.version,
        "status": "running",
        "kernel": {
            "events": len(kernel.event_bus.topics()),
            "services": kernel.services.list(),
            "scheduler": len(kernel.scheduler.list_jobs()),
        },
        "task_manager": task_manager.get_stats(),
        "endpoints": {
            "chat": "/chat",
            "code": "/code/generate",
            "agents": "/agents",
            "browser": "/browser/navigate",
            "desktop": "/desktop/info",
            "android": "/android/devices",
            "whatsapp": "/whatsapp/status",
            "crm": "/crm/summary",
            "seo": "/seo/sites",
            "automation": "/automation/workflows",
            "tasks": "/tasks",
            "pipeline": "/pipeline/build",
            "vision": "/vision/cameras",
            "marketplace": "/marketplace/catalog",
            "analytics": "/analytics/dashboard",
            "health": "/system/health",
            "docs": "/docs",
        },
    }


@app.get("/kernel/status")
async def kernel_status():
    return {
        "services": kernel.services.list(),
        "events_subscribers": len(kernel.event_bus.topics()),
        "scheduled_jobs": len(kernel.scheduler.list_jobs()),
    }


@app.get("/proxy")
async def proxy(url: str = "https://example.com"):
    """Proxy endpoint — fetch URL, rewrite relative paths, return HTML for iframe embedding."""
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0"})
        content = resp.text
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        content = re.sub(r'(src|href)=(["\'])/(?!\/)', f"\\1=\\2{base}/", content)
        content = re.sub(r'(src|href)=(["\'])(?![a-z]+:)(?!#)', f"\\1=\\2{base}/", content)
        return HTMLResponse(content=content, status_code=resp.status_code)
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.debug)
