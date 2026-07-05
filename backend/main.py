import json
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api import router as api_router
from backend.app.core.websocket_manager import WebSocketManager
from backend.app.services.ai.orchestrator import AIOrchestrator
from backend.app.services.memory.memory_manager import MemoryManager
from backend.app.core.lumina_kernel import LuminaKernel
from backend.app.core.middleware import LoggingMiddleware, ErrorHandlingMiddleware, RateLimitMiddleware
from backend.app.core.monitoring import monitor

logger = logging.getLogger(__name__)

websocket_manager = WebSocketManager()
kernel: LuminaKernel = None
orchestrator: AIOrchestrator = None
memory_manager: MemoryManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global kernel, orchestrator, memory_manager
    logger.info("Starting Lumina AI OS...")
    await init_db()
    memory_manager = MemoryManager()
    await memory_manager.initialize()
    kernel = LuminaKernel()
    await kernel.initialize()
    orchestrator = AIOrchestrator(
        memory_manager=memory_manager,
        websocket_manager=websocket_manager,
        kernel=kernel,
    )
    await orchestrator.initialize()
    logger.info("Lumina AI OS ready")
    yield
    logger.info("Shutting down...")
    await orchestrator.shutdown()
    await kernel.shutdown()
    await memory_manager.shutdown()


app = FastAPI(
    title="Lumina AI OS",
    description="The World's First Autonomous AI Employee Operating System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(CORSMiddleware, allow_origins=settings.ALLOWED_ORIGINS, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(LoggingMiddleware)
app.add_middleware(ErrorHandlingMiddleware)
if settings.ENVIRONMENT == "production":
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

app.include_router(api_router, prefix="/api")


@app.middleware("http")
async def monitor_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    monitor.record_request(request.method, request.url.path, response.status_code, duration)
    return response


@app.get("/")
async def root():
    return {"name": "Lumina AI OS", "version": "1.0.0", "status": "online"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "kernel": kernel.get_status() if kernel else "unavailable",
        "memory": "active" if memory_manager else "unavailable",
        "orchestrator": orchestrator.state.value if orchestrator else "unavailable",
    }


@app.get("/monitor")
async def get_monitor_stats():
    return monitor.get_stats()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            msg_type = message.get("type")
            if msg_type == "command":
                response = await orchestrator.process_command(command=message.get("data"), user_id=message.get("user_id"))
                await websocket.send_json({"type": "response", "data": response})
            elif msg_type == "voice":
                response = await orchestrator.process_voice_command(audio_data=message.get("data"), user_id=message.get("user_id"))
                await websocket.send_json({"type": "response", "data": response})
            elif msg_type == "task_status":
                status = await orchestrator.get_task_status(message.get("task_id"))
                await websocket.send_json({"type": "status", "data": status})
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
