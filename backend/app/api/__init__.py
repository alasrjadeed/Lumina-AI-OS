from fastapi import APIRouter
from backend.app.api.auth import router as auth_router
from backend.app.api.tasks import router as tasks_router
from backend.app.api.agents import router as agents_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.memory import router as memory_router
from backend.app.api.explain import router as explain_router
from backend.app.api.reader import router as reader_router
from backend.app.api.voice import router as voice_router
from backend.app.api.settings import router as settings_router
from backend.app.api.developer import router as developer_router
from backend.app.api.desktop import router as desktop_router
from backend.app.api.browser import router as browser_router
from backend.app.api.crm import router as crm_router
from backend.app.api.marketing import router as marketing_router
from backend.app.api.whatsapp import router as whatsapp_router
from backend.app.api.email import router as email_router
from backend.app.api.autonomous import router as autonomous_router
from backend.app.api.media import router as media_router
from backend.app.api.leadgen import router as leadgen_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
router.include_router(tasks_router, prefix="/tasks", tags=["Tasks"])
router.include_router(agents_router, prefix="/agents", tags=["Agents"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(memory_router, prefix="/memory", tags=["Memory"])
router.include_router(explain_router, prefix="/explain", tags=["Explain"])
router.include_router(reader_router, prefix="/reader", tags=["Reader"])
router.include_router(voice_router, prefix="/voice", tags=["Voice"])
router.include_router(settings_router, prefix="/settings", tags=["Settings"])
router.include_router(developer_router, prefix="/developer", tags=["Developer"])
router.include_router(desktop_router, prefix="/desktop", tags=["Desktop"])
router.include_router(browser_router, prefix="/browser", tags=["Browser"])
router.include_router(crm_router, prefix="/crm", tags=["CRM"])
router.include_router(marketing_router, prefix="/marketing", tags=["Marketing"])
router.include_router(whatsapp_router, prefix="/whatsapp", tags=["WhatsApp"])
router.include_router(email_router, prefix="/email", tags=["Email"])
router.include_router(autonomous_router, prefix="/autonomous", tags=["Autonomous"])
router.include_router(media_router, prefix="/media", tags=["Media"])
router.include_router(leadgen_router, prefix="/leadgen", tags=["Lead Generation"])
