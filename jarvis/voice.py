from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.voice.controller import VoiceController
from core.voice.recorder import AudioRecorder
from core.voice.stt import STTEngine
from core.voice.tts import TTSEngine
from jarvis.jarvis_settings import JarvisSettings


class VoiceManager:
    def __init__(self, settings: JarvisSettings):
        self.settings = settings
        self.controller: VoiceController | None = None
        self.recorder = AudioRecorder()
        self.stt = STTEngine()
        self.tts = TTSEngine()

    async def start(self) -> None:
        if not self.recorder.is_available():
            return
        if not self.controller:
            self.controller = VoiceController(
                recorder=self.recorder,
                stt_engine=self.stt,
                tts_engine=self.tts,
                wake_word=self.settings.get("wake_word", "jarvis") or "jarvis",
            )
        wake = bool(self.settings.get("wake_word_enabled", True))
        asyncio.create_task(self.controller.start_continuous(wake_word_mode=wake))

    async def stop(self) -> None:
        if self.controller:
            self.controller.stop()

    async def speak(self, text: str) -> None:
        await self.tts.speak(text)

    async def transcribe(self, audio: bytes) -> str:
        result = await self.stt.transcribe(audio)
        return result.text
