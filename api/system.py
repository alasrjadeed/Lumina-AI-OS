from fastapi import APIRouter

from config.settings import settings
from core.log import log
from core.provider import engine

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health")
async def health_check():
    provider_names = [p.name for p in engine.providers]
    return {
        "status": "ok",
        "version": settings.version,
        "providers": provider_names,
        "primary_provider": engine.providers[0].name if engine.providers else None,
    }


@router.get("/config")
async def get_config():
    return {
        "app_name": settings.app_name,
        "version": settings.version,
        "provider_priority": [p.name for p in engine.providers],
        "models": {
            "ollama": settings.ollama_model,
            "openrouter": settings.openrouter_model,
            "deepseek": settings.deepseek_model,
            "openai": settings.openai_model,
            "groq": settings.groq_model,
            "gemini": settings.gemini_model,
        },
        "providers": {
            "ollama": True,
            "openrouter": bool(settings.openrouter_api_key),
            "groq": bool(settings.groq_api_key),
            "gemini": bool(settings.gemini_api_key),
            "deepseek": bool(settings.deepseek_api_key),
            "openai": bool(settings.openai_api_key),
            "cloudflare": bool(settings.cloudflare_api_token and settings.cloudflare_account_id),
            "nvidia": bool(settings.nvidia_api_key),
            "serp": bool(settings.serp_api_key),
            "apify": bool(settings.apify_api_token),
            "whatsapp": bool(settings.whatsapp_api_key),
        },
        "reload": "/system/reload",
        "fallback": (
            "If a provider fails or credits run out,"
            " Lumina automatically tries the next one in sequence."
        ),
    }


@router.post("/reload")
async def reload_config():
    """Reload settings from .env without restarting the server."""
    result = settings.reload()
    log.info("Settings reloaded: %s", result)
    return result
