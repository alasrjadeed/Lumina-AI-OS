import base64
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.voice.voice_service import VoiceService

logger = logging.getLogger(__name__)
router = APIRouter()
voice_service = VoiceService()


class VoiceRequest(BaseModel):
    text: Optional[str] = None
    audio_data: Optional[str] = None
    voice: str = "default"
    speed: float = 1.0
    language: str = "en"
    display_simultaneously: bool = True


class SpeakResponse(BaseModel):
    audio: Optional[str] = None
    text: Optional[str] = None
    format: str = "wav"
    duration_ms: Optional[int] = None
    displayed_content: Optional[str] = None


class RecognizeResponse(BaseModel):
    text: str
    confidence: float = 0.0
    language: str = "en"
    duration_ms: Optional[int] = None
    words: list = []


@router.post("/speak", response_model=SpeakResponse)
async def speak(req: VoiceRequest):
    if not req.text:
        raise HTTPException(status_code=400, detail="text field required")
    result = await voice_service.speak(req.text, req.voice, req.speed)
    return SpeakResponse(
        audio=result.get("audio"),
        text=req.text,
        format="wav",
        duration_ms=result.get("duration_ms"),
        displayed_content=req.text if req.display_simultaneously else None,
    )


@router.post("/recognize", response_model=RecognizeResponse)
async def recognize(req: VoiceRequest):
    if not req.audio_data:
        raise HTTPException(status_code=400, detail="audio_data field required")
    result = await voice_service.recognize(req.audio_data, req.language)
    return RecognizeResponse(
        text=result.get("text", ""),
        confidence=result.get("confidence", 0.0),
        language=result.get("language", req.language),
        duration_ms=result.get("duration_ms"),
        words=result.get("words", []),
    )


@router.post("/stop")
async def stop():
    return await voice_service.stop()


@router.post("/pause")
async def pause():
    return await voice_service.pause()


@router.post("/resume")
async def resume():
    return await voice_service.resume()


@router.get("/voices")
async def list_voices():
    return await voice_service.list_voices()


@router.get("/languages")
async def list_languages():
    return {"languages": ["en", "ar", "es", "fr", "de", "zh", "hi", "ur"]}
