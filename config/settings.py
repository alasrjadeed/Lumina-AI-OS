import contextlib
import os

import dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Lumina AI OS"
    version: str = "1.0.0"
    debug: bool = True

    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5-coder:0.5b"

    openai_api_key: str | None = None
    openai_base_url: str | None = None
    openai_model: str = "gpt-4o-mini"

    openrouter_api_key: str | None = None
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "cohere/north-mini-code:free"

    deepseek_api_key: str | None = None
    deepseek_model: str = "deepseek-chat"

    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-8b-instant"

    gemini_api_key: str | None = None
    gemini_model: str = "gemini-1.5-flash"

    whatsapp_api_key: str | None = None
    whatsapp_phone_id: str | None = None

    cloudflare_account_id: str | None = None
    cloudflare_api_token: str | None = None

    serp_api_key: str | None = None

    nvidia_api_key: str | None = None

    zai_api_key: str | None = None

    apify_api_token: str | None = None

    google_business_api_key: str | None = None
    google_business_account_id: str | None = None
    google_business_location_id: str | None = None

    max_tokens: int = 4096
    temperature: float = 0.7

    vision_camera_id: int = 0
    vision_camera_width: int = 640
    vision_camera_height: int = 480
    vision_camera_fps: int = 15
    vision_detection_confidence: float = 0.25
    vision_enable_yolo: bool = False

    auth_enabled: bool = False
    api_keys: str = ""
    cors_origins: str = "*"

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
        env_file_encoding = "utf-8"

    def reload(self) -> dict[str, str | None]:
        """Reload settings from .env file without restarting the server."""
        dotenv.load_dotenv(self.Config.env_file, override=True)
        # Re-read fields from environment
        updated = {}
        for field_name in self.model_fields:
            env_var = field_name.upper()
            val = os.environ.get(env_var)
            if val is not None:
                field_type = self.model_fields[field_name].annotation
                if isinstance(field_type, type) and issubclass(field_type, bool):
                    setattr(self, field_name, val.lower() in ("true", "1", "yes"))
                elif isinstance(field_type, type) and issubclass(field_type, int):
                    with contextlib.suppress(ValueError):
                        setattr(self, field_name, int(val))
                elif isinstance(field_type, type) and issubclass(field_type, float):
                    with contextlib.suppress(ValueError):
                        setattr(self, field_name, float(val))
                else:
                    setattr(self, field_name, val)
                updated[field_name] = val[:20] + "..." if len(val) > 20 else val
        return {"status": "reloaded", "updated": list(updated.keys())}


settings = Settings()
