import base64
import io
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class VoiceService:
    def __init__(self):
        self._speaking = False
        self._paused = False
        self._current_text = ""
        self._provider = "default"
        self._voices = {
            "default": {"name": "Default", "gender": "neutral", "provider": "system"},
            "nova": {"name": "Nova", "gender": "female", "provider": "openai"},
            "alloy": {"name": "Alloy", "gender": "neutral", "provider": "openai"},
            "echo": {"name": "Echo", "gender": "male", "provider": "openai"},
            "shimmer": {"name": "Shimmer", "gender": "female", "provider": "azure"},
        }

    async def speak(self, text: str, voice: str = "default", speed: float = 1.0) -> Dict[str, Any]:
        self._speaking = True
        self._current_text = text
        logger.info(f"Speaking {len(text)} chars with voice={voice} speed={speed}")
        audio_data = await self._text_to_speech(text, voice, speed)
        return {
            "audio": audio_data,
            "format": "wav",
            "duration_ms": len(text) * 60,
            "status": "speaking" if not self._paused else "paused",
            "displayed_content": text,
        }

    async def recognize(self, audio_data: str, language: str = "en") -> Dict[str, Any]:
        logger.info(f"Recognizing audio ({len(audio_data)} bytes, lang={language})")
        transcript = await self._speech_to_text(audio_data, language)
        return {
            "text": transcript,
            "confidence": 0.95,
            "language": language,
            "duration_ms": 0,
            "words": transcript.split(),
        }

    async def stop(self) -> Dict[str, Any]:
        self._speaking = False
        self._paused = False
        return {"status": "stopped"}

    async def pause(self) -> Dict[str, Any]:
        self._paused = True
        return {"status": "paused"}

    async def resume(self) -> Dict[str, Any]:
        self._paused = False
        return {"status": "resumed"}

    async def list_voices(self) -> List[Dict[str, Any]]:
        return list(self._voices.values())

    async def _text_to_speech(self, text: str, voice: str, speed: float) -> Optional[str]:
        try:
            from openai import OpenAI
            from backend.app.core.config import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            response = client.audio.speech.create(
                model="tts-1",
                voice=voice if voice in ("alloy", "echo", "fable", "nova", "onyx", "shimmer") else "nova",
                input=text,
                speed=speed,
            )
            buf = io.BytesIO()
            for chunk in response.iter_bytes():
                buf.write(chunk)
            return base64.b64encode(buf.getvalue()).decode()
        except ImportError:
            logger.warning("openai not installed, returning null audio")
            return None
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None

    async def _speech_to_text(self, audio_data: str, language: str) -> str:
        try:
            from openai import OpenAI
            from backend.app.core.config import settings
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            audio_bytes = base64.b64decode(audio_data)
            buf = io.BytesIO(audio_bytes)
            buf.name = "audio.wav"
            transcript = client.audio.transcriptions.create(model="whisper-1", file=buf, language=language)
            return transcript.text
        except ImportError:
            logger.warning("openai not installed, returning placeholder")
            return "[transcription requires openai package]"
        except Exception as e:
            logger.error(f"STT failed: {e}")
            return "[transcription error]"
