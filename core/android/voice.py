from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass
from typing import Any

from core.android.device import AndroidDevice
from core.log import log


@dataclass
class VoiceCaptureResult:
    audio_path: str
    duration_ms: float = 0.0
    text: str = ""
    success: bool = False


class AndroidVoiceInterface:
    """Voice capture and interaction with Android device."""

    def __init__(self, device: AndroidDevice | None = None):
        self.device = device or AndroidDevice()
        self._stt_provider = None
        self._tts_provider = None

    # ── Audio Capture ──

    def capture_audio(self, duration: int = 5, sample_rate: int = 16000) -> VoiceCaptureResult:
        remote_path = "/sdcard/voice_capture.raw"
        local_path = os.path.join(tempfile.gettempdir(), "voice_capture.raw")
        command = (
            f"tinycap {remote_path} -D 0 -d 0 -r {sample_rate} -b 16 -c 1 -t {duration}"
            f" 2>/dev/null || "
            f"su 0 'screencap -p {remote_path}' 2>/dev/null"
        )
        try:
            self.device.shell(command)
            time.sleep(duration + 1)
            self.device.pull(remote_path, local_path)
            self.device.shell(f"rm {remote_path}")
            if os.path.exists(local_path) and os.path.getsize(local_path) > 100:
                return VoiceCaptureResult(
                    audio_path=local_path,
                    duration_ms=duration * 1000,
                    success=True,
                )
            return VoiceCaptureResult(audio_path=local_path, success=False)
        except Exception as e:
            log.error("Audio capture failed: %s", e)
            return VoiceCaptureResult(audio_path="", success=False)

    def capture_audio_media(self, duration: int = 5) -> VoiceCaptureResult:
        remote_path = "/sdcard/voice_capture.mp4"
        local_path = os.path.join(tempfile.gettempdir(), "voice_capture.mp4")
        try:
            self.device.shell(f"screenrecord --time-limit {duration} {remote_path}")
            time.sleep(duration + 2)
            self.device.pull(remote_path, local_path)
            self.device.shell(f"rm {remote_path}")
            return VoiceCaptureResult(
                audio_path=local_path,
                duration_ms=duration * 1000,
                success=os.path.exists(local_path),
            )
        except Exception as e:
            log.error("Media capture failed: %s", e)
            return VoiceCaptureResult(audio_path="", success=False)

    # ── Speech-to-Text ──

    def set_stt_provider(self, provider: Any) -> None:
        self._stt_provider = provider

    def transcribe(self, audio_path: str = "") -> str:
        if not audio_path:
            result = self.capture_audio(duration=3)
            if not result.success:
                return ""
            audio_path = result.audio_path
        if self._stt_provider:
            try:
                with open(audio_path, "rb") as f:
                    audio_data = f.read()
                text = self._stt_provider.transcribe(audio_data).text
                log.info("STT: %s", text[:100])
                return text
            except Exception as e:
                log.error("STT failed: %s", e)
        return ""

    # ── Text-to-Speech ──

    def set_tts_provider(self, provider: Any) -> None:
        self._tts_provider = provider

    def speak(self, text: str, language: str = "en") -> bool:
        if self._tts_provider:
            try:
                result = self._tts_provider.synthesize(text)
                remote_path = "/sdcard/tts_output.mp3"
                local_path = os.path.join(tempfile.gettempdir(), "tts_output.mp3")
                with open(local_path, "wb") as f:
                    f.write(result.audio_data)
                self.device.push(local_path, remote_path)
                self.device.shell(f"play {remote_path} 2>/dev/null || "
                                  f"mediaplayer {remote_path} 2>/dev/null")
                log.info("TTS: %s", text[:100])
                return True
            except Exception as e:
                log.error("TTS failed: %s", e)
                return False
        else:
            safe_text = text.replace("'", "\\'")
            cmd = (
                f"am broadcast -a com.lumina.SPEAK"
                f" -e text '{safe_text}' --es language '{language}'"
            )
            self.device.shell(cmd)
            return True

    def speak_file(self, audio_path: str) -> bool:
        remote_path = "/sdcard/play_audio.mp3"
        try:
            self.device.push(audio_path, remote_path)
            self.device.shell(f"play {remote_path} 2>/dev/null")
            return True
        except Exception as e:
            log.error("Play audio failed: %s", e)
            return False

    # ── Voice Commands ──

    def listen_for_command(self, timeout: int = 10) -> str:
        result = self.capture_audio(duration=timeout)
        if result.success:
            text = self.transcribe(result.audio_path)
            return text
        return ""

    def listen_for_wake_word(self, wake_word: str = "lumina", timeout: int = 30) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.capture_audio(duration=2)
            if result.success:
                text = self.transcribe(result.audio_path)
                if wake_word.lower() in text.lower():
                    log.info("Wake word detected: %s", wake_word)
                    return True
        return False
