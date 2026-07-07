from __future__ import annotations

import math
import struct
import time
from collections.abc import Callable
from dataclasses import dataclass, field


MIN_INT16 = -32768
MAX_INT16 = 32767


@dataclass
class VADResult:
    is_speech: bool = False
    energy: float = 0.0
    rms: float = 0.0
    timestamp: float = field(default_factory=time.time)
    duration_sec: float = 0.0


class EnergyVAD:
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_ms: int = 30,
        threshold: float = 500.0,
        min_speech_frames: int = 3,
        silence_frames: int = 15,
    ):
        self.sample_rate = sample_rate
        self.frame_size = int(sample_rate * frame_ms / 1000)
        self.threshold = threshold
        self.min_speech_frames = min_speech_frames
        self.silence_frames = silence_frames
        self._speech_frames = 0
        self._silence_frames = 0
        self._is_speech = False

    def _rms(self, samples: list[int]) -> float:
        if not samples:
            return 0.0
        sum_sq = sum(s * s for s in samples)
        return math.sqrt(sum_sq / len(samples))

    def is_speech(self, audio_chunk: bytes) -> VADResult:
        count = len(audio_chunk) // 2
        samples = struct.unpack_from(f"<{count}h", audio_chunk) if count > 0 else []
        rms = self._rms(list(samples))
        energy = rms * rms
        speaking = rms > self.threshold

        if speaking:
            self._speech_frames += 1
            self._silence_frames = 0
        else:
            self._silence_frames += 1
            self._speech_frames = max(0, self._speech_frames - 1)

        if self._speech_frames >= self.min_speech_frames:
            self._is_speech = True
        if self._silence_frames >= self.silence_frames:
            self._is_speech = False

        return VADResult(
            is_speech=self._is_speech,
            energy=energy, rms=rms,
            duration_sec=len(audio_chunk) / (self.sample_rate * 2),
        )

    def reset(self) -> None:
        self._speech_frames = 0
        self._silence_frames = 0
        self._is_speech = False

    @staticmethod
    def trim_silence(
        audio_data: bytes,
        sample_rate: int = 16000,
        threshold: int = 500,
        padding_ms: int = 300,
    ) -> bytes:
        samples_count = len(audio_data) // 2
        samples = struct.unpack_from(f"<{samples_count}h", audio_data) if samples_count > 0 else []

        start = 0
        for i, s in enumerate(samples):
            if abs(s) > threshold:
                start = max(0, i - int(sample_rate * padding_ms / 1000))
                break

        end = len(samples)
        for i in range(len(samples) - 1, -1, -1):
            if abs(samples[i]) > threshold:
                end = min(len(samples), i + int(sample_rate * padding_ms / 1000))
                break

        if start >= end:
            return b""

        trimmed = samples[start:end]
        return struct.pack(f"<{len(trimmed)}h", *trimmed)


class SilenceBuffer:
    def __init__(self, sample_rate: int = 16000, silence_sec: float = 1.5):
        self.sample_rate = sample_rate
        self.silence_samples = int(sample_rate * silence_sec)
        self._buffer = b""
        self._last_voice_time = 0.0

    def add(self, chunk: bytes, is_voice: bool, now: float | None = None) -> bytes | None:
        now = now or time.time()
        if is_voice:
            self._buffer += chunk
            self._last_voice_time = now
            return None

        elapsed = now - self._last_voice_time
        if elapsed < (self.silence_samples / self.sample_rate):
            self._buffer += chunk
            return None

        result = self._buffer
        self._buffer = b""
        return result if result else None

    def flush(self) -> bytes:
        result = self._buffer
        self._buffer = b""
        return result

    def reset(self) -> None:
        self._buffer = b""
        self._last_voice_time = 0.0
