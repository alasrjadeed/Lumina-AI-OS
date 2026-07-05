from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.core.config import settings as app_settings
from backend.app.core.deps import get_current_user

router = APIRouter()


class SettingsResponse(BaseModel):
    app_name: str
    app_version: str
    environment: str
    debug: bool
    ai_provider: str
    local_ai_url: str
    local_ai_model: str
    log_level: str
    allowed_origins: List[str]


class SettingsUpdate(BaseModel):
    ai_provider: Optional[str] = None
    local_ai_url: Optional[str] = None
    local_ai_model: Optional[str] = None
    log_level: Optional[str] = None
    llm_temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    voice_enabled: Optional[bool] = None
    voice_speed: Optional[float] = None
    auto_index: Optional[bool] = None
    theme: Optional[str] = None
    sidebar_collapsed: Optional[bool] = None


_in_memory_settings: Dict[str, Any] = {
    "ai_provider": "ollama",
    "llm_temperature": 0.7,
    "max_tokens": 4096,
    "voice_enabled": True,
    "voice_speed": 1.0,
    "auto_index": True,
    "theme": "dark",
    "sidebar_collapsed": False,
}


@router.get("/", response_model=SettingsResponse)
async def get_settings(current_user: dict = Depends(get_current_user)):
    return SettingsResponse(
        app_name=app_settings.APP_NAME,
        app_version=app_settings.APP_VERSION,
        environment=app_settings.ENVIRONMENT,
        debug=app_settings.DEBUG,
        ai_provider=_in_memory_settings.get("ai_provider", "ollama"),
        local_ai_url=app_settings.LOCAL_AI_URL,
        local_ai_model=app_settings.LOCAL_AI_MODEL,
        log_level=app_settings.LOG_LEVEL,
        allowed_origins=app_settings.ALLOWED_ORIGINS,
    )


@router.put("/")
async def update_settings(update: SettingsUpdate, current_user: dict = Depends(get_current_user)):
    _in_memory_settings.update(update.model_dump(exclude_none=True))
    return {"status": "saved", "settings": _in_memory_settings}


@router.get("/all")
async def get_all_settings(current_user: dict = Depends(get_current_user)):
    return _in_memory_settings
