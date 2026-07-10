"""Audio recorder — captures microphone input via system tools.

Supports arecord (ALSA) and parec (PulseAudio) with auto-detection.
No Python audio dependencies required.
"""

from __future__ import annotations

import asyncio
import contextlib
import os
import re
import tempfile

from core.log import log


class AudioRecorder:
    """Captures audio from microphone using system tools.

    Usage:
        recorder = AudioRecorder()
        audio_data = await recorder.record(duration=5)  # 5 seconds
        audio_data = await recorder.record_until_silence()  # auto-stop
    """

    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._tool = self._detect_tool()

    @staticmethod
    def _detect_tool() -> str:
        for tool in ["arecord", "parec", "sox"]:
            if os.system(f"which {tool} >/dev/null 2>&1") == 0:
                return tool
        return "none"

    def is_available(self) -> bool:
        return self._tool != "none"

    @staticmethod
    def list_devices() -> list[dict]:
        devices = []
        try:
            import subprocess

            result = subprocess.run(["arecord", "-l"], capture_output=True, text=True, timeout=5)
            for line in result.stdout.split("\n"):
                m = re.search(r"card (\d+).*: (.+?)]", line)
                if m:
                    devices.append({"id": f"hw:{m.group(1)},0", "name": m.group(2).strip()})
        except Exception:
            pass
        if not devices:
            devices.append({"id": "default", "name": "Default ALSA device"})
        return devices

    async def record(self, duration: float = 5.0, timeout: float = 10.0) -> bytes:
        """Record audio for a fixed duration. Returns WAV bytes."""
        if not self.is_available():
            raise RuntimeError("No audio capture tool found (install arecord or parec)")

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            pass

        try:
            if self._tool == "arecord":
                cmd = [
                    "arecord",
                    "-q",
                    "-r",
                    str(self.sample_rate),
                    "-c",
                    str(self.channels),
                    "-f",
                    "S16_LE",
                    "-d",
                    str(int(duration)),
                    tmp.name,
                ]
            elif self._tool == "parec":
                cmd = [
                    "parec",
                    "--rate=" + str(self.sample_rate),
                    "--channels=" + str(self.channels),
                    "--format=s16le",
                    "--file-format=wav",
                    tmp.name,
                ]
            else:
                cmd = [
                    "sox",
                    "-q",
                    "-d",
                    "-r",
                    str(self.sample_rate),
                    "-c",
                    str(self.channels),
                    tmp.name,
                    "trim",
                    "0",
                    str(duration),
                ]

            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=timeout)

            with open(tmp.name, "rb") as f:
                data = f.read()
            return data

        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp.name)

    async def record_until_silence(
        self,
        max_duration: float = 30.0,
        silence_threshold: int = 500,
        silence_duration: float = 1.5,
    ) -> bytes:
        """Record until silence is detected (simple energy-based VAD).

        Falls back to fixed-duration recording if silence detection unavailable.
        """
        if self._tool != "arecord":
            log.info("AudioRecorder: silence detection requires arecord, falling back to 10s")
            return await self.record(duration=min(max_duration, 10.0))

        with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as tmp:
            pass

        try:
            cmd = [
                "arecord",
                "-q",
                "-r",
                str(self.sample_rate),
                "-c",
                str(self.channels),
                "-f",
                "S16_LE",
                "-d",
                str(int(max_duration)),
                tmp.name,
            ]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=max_duration + 5)

            with open(tmp.name, "rb") as f:
                raw = f.read()

            # Simple silence detection: find where audio ends
            samples = len(raw) // 2
            silence_end = 0
            for i in range(
                samples - 1, max(0, samples - int(silence_duration * self.sample_rate)), -1
            ):
                val = int.from_bytes(raw[i * 2 : (i + 1) * 2], "little", signed=True)
                if abs(val) > silence_threshold:
                    silence_end = i
                    break

            if silence_end > 0:
                trim_bytes = (silence_end + int(self.sample_rate * 0.5)) * 2
                raw = raw[: min(trim_bytes, len(raw))]

            # Wrap in WAV header
            wav = self._raw_to_wav(raw)
            return wav

        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp.name)

    async def calibrate(self, duration: float = 2.0) -> dict:
        """Record ambient noise and return calibrated VAD parameters.

        Returns:
            dict with keys: ambient_rms, threshold, sample_rate, tool
        """
        raw = await self.record(duration=duration)
        import struct

        count = len(raw) // 2
        if count == 0:
            return {
                "ambient_rms": 0,
                "threshold": 500,
                "sample_rate": self.sample_rate,
                "tool": self._tool,
            }
        samples = struct.unpack_from(f"<{count}h", raw) if count > 0 else []
        if not samples:
            return {
                "ambient_rms": 0,
                "threshold": 500,
                "sample_rate": self.sample_rate,
                "tool": self._tool,
            }
        sum_sq = sum(s * s for s in samples)
        rms = (sum_sq / len(samples)) ** 0.5
        threshold = max(int(rms * 3), 50)
        log.info("AudioRecorder: calibrated — ambient RMS=%.1f, threshold=%d", rms, threshold)
        return {
            "ambient_rms": rms,
            "threshold": threshold,
            "sample_rate": self.sample_rate,
            "tool": self._tool,
        }

    @staticmethod
    def _raw_to_wav(
        raw_data: bytes, sample_rate: int = 16000, channels: int = 1, bits: int = 16
    ) -> bytes:
        """Wrap raw PCM data in a WAV header."""
        import struct

        data_size = len(raw_data)
        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF",
            36 + data_size,
            b"WAVE",
            b"fmt ",
            16,
            1,
            channels,
            sample_rate,
            sample_rate * channels * bits // 8,
            channels * bits // 8,
            bits,
            b"data",
            data_size,
        )
        return header + raw_data


recorder = AudioRecorder()
