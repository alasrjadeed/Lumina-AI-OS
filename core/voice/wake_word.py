from __future__ import annotations

import os
import re
import struct
import time
from dataclasses import dataclass, field
from typing import Protocol

try:
    import pvporcupine  # pyright: ignore[reportMissingImports]

    HAS_PVPORCUPINE = True
except ImportError:
    pvporcupine = None
    HAS_PVPORCUPINE = False

_PICOVOICE_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")


@dataclass
class WakeWordResult:
    detected: bool
    wake_word: str = ""
    confidence: float = 0.0
    timestamp: float = field(default_factory=time.time)


class WakeWordDetector(Protocol):
    def detect(self, audio_chunk: bytes) -> WakeWordResult: ...
    def set_wake_words(self, words: list[str]) -> None: ...


class PatternWakeWordDetector:
    """Simple keyword-spotting wake word detector for testing."""

    def __init__(self, wake_words: list[str] | None = None):
        self.wake_words = wake_words or ["lumina", "hey lumina"]
        self._patterns = [re.compile(re.escape(w), re.IGNORECASE) for w in self.wake_words]

    def detect(self, audio_chunk: bytes) -> WakeWordResult:
        text = audio_chunk.decode("utf-8", errors="replace")
        for word, pattern in zip(self.wake_words, self._patterns):
            match = pattern.search(text)
            if match:
                return WakeWordResult(
                    detected=True,
                    wake_word=word,
                    confidence=1.0,
                )
        return WakeWordResult(detected=False)

    def set_wake_words(self, words: list[str]) -> None:
        self.wake_words = words
        self._patterns = [re.compile(re.escape(w), re.IGNORECASE) for w in words]


class PorcupineWakeWordDetector:
    """Porcupine wake word engine wrapper."""

    def __init__(
        self,
        access_key: str | None = None,
        wake_words: list[str] | None = None,
        sensitivities: list[float] | None = None,
    ):
        self.access_key = access_key or _PICOVOICE_KEY
        self.wake_words = wake_words or ["jarvis"]
        self.sensitivities = sensitivities or [0.5] * len(self.wake_words)
        self._engine = None

    def _lazy_init(self):
        if self._engine is not None:
            return
        if not HAS_PVPORCUPINE:
            return
        if not self.access_key:
            return
        assert pvporcupine is not None
        self._engine = pvporcupine.create(
            access_key=self.access_key,
            keywords=self.wake_words,
            sensitivities=self.sensitivities,
        )

    def detect(self, audio_chunk: bytes) -> WakeWordResult:
        self._lazy_init()
        if self._engine is None:
            return WakeWordResult(detected=False)
        pcm = struct.unpack_from("h" * (len(audio_chunk) // 2), audio_chunk)
        result = self._engine.process(pcm)
        if result >= 0:
            return WakeWordResult(
                detected=True,
                wake_word=self.wake_words[result],
                confidence=1.0,
            )
        return WakeWordResult(detected=False)

    def set_wake_words(self, words: list[str]) -> None:
        self.wake_words = words


class WakeWordEngine:
    """High-level wake word engine with cooldown and chaining."""

    def __init__(
        self,
        detector: WakeWordDetector | None = None,
        cooldown_seconds: float = 2.0,
    ):
        self.detector = detector or PatternWakeWordDetector()
        self.cooldown = cooldown_seconds
        self._last_detection: float = 0.0

    def listen(self, audio_chunk: bytes) -> WakeWordResult:
        now = time.time()
        if now - self._last_detection < self.cooldown:
            return WakeWordResult(detected=False)
        result = self.detector.detect(audio_chunk)
        if result.detected:
            self._last_detection = now
        return result

    def set_wake_words(self, words: list[str]) -> None:
        self.detector.set_wake_words(words)

    def reset_cooldown(self) -> None:
        self._last_detection = 0.0
