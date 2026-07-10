from __future__ import annotations

import asyncio
import subprocess
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass

from core.log import log
from core.voice.echo import EchoDetector
from core.voice.recorder import AudioRecorder
from core.voice.stt import STTEngine, STTResult
from core.voice.vad import EnergyVAD


@dataclass
class DictationResult:
    text: str = ""
    confidence: float = 0.0
    duration_ms: float = 0.0
    filler_removed: bool = False
    corrections_applied: bool = False


FILLER_WORDS = {
    "um",
    "uh",
    "er",
    "ah",
    "like",
    "you know",
    "i mean",
    "sort of",
    "kind of",
    "actually",
    "basically",
    "literally",
    "so",
    "well",
    "right",
    "okay",
    "hmm",
}


class DictationEngine:
    def __init__(
        self,
        stt: STTEngine | None = None,
        recorder: AudioRecorder | None = None,
        vad: EnergyVAD | None = None,
        filler_removal: bool = True,
        custom_dictionary: list[str] | None = None,
        min_confidence: float = 0.3,
    ):
        self.stt = stt or STTEngine()
        self.recorder = recorder or AudioRecorder()
        self.vad = vad or EnergyVAD()
        self.filler_removal = filler_removal
        self.custom_dictionary = custom_dictionary or []
        self.min_confidence = min_confidence
        self._dict: dict[str, str] = {}
        self._active = False
        self._thread: threading.Thread | None = None
        self._hotkey_thread: threading.Thread | None = None
        self._hotkey_on_result: Callable | None = None
        self._result_queue: asyncio.Queue[DictationResult] = asyncio.Queue()
        self._echo = EchoDetector()
        self._parse_dictionary()

    def _parse_dictionary(self) -> None:
        for entry in self.custom_dictionary:
            if " -> " in entry:
                wrong, right = entry.split(" -> ", 1)
                self._dict[wrong.strip().lower()] = right.strip()
            elif ":" in entry:
                parts = entry.split(":", 1)
                self._dict[parts[0].strip().lower()] = parts[1].strip()

    def add_correction(self, wrong: str, right: str) -> None:
        self._dict[wrong.strip().lower()] = right.strip()

    def _apply_corrections(self, text: str) -> str:
        if not self._dict:
            return text
        words = text.split()
        corrected = [self._dict.get(w.lower(), w) for w in words]
        return " ".join(corrected)

    def _remove_fillers(self, text: str) -> str:
        if not self.filler_removal:
            return text
        words = text.split()
        filtered = [w for w in words if w.lower() not in FILLER_WORDS]
        return " ".join(filtered)

    def _clean_text(self, text: str) -> str:
        text = self._remove_fillers(text)
        text = self._apply_corrections(text)
        return text.strip()

    def record_once(self, timeout: float = 10.0) -> DictationResult:
        audio = asyncio.run(self.recorder.record_until_silence(max_duration=timeout))
        if not audio or len(audio) < 100:
            return DictationResult()

        result: STTResult | None = None
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.stt.transcribe(audio))
        finally:
            loop.close()
        if not result or result.confidence < self.min_confidence:
            return DictationResult(text="", confidence=result.confidence)

        self._echo.record_utterance(result.text)
        cleaned = self._clean_text(result.text)

        return DictationResult(
            text=cleaned,
            confidence=result.confidence,
            duration_ms=result.duration_ms,
            filler_removed=self.filler_removal and cleaned != result.text,
            corrections_applied=cleaned != result.text and not self.filler_removal,
        )

    def _record_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            while self._active:
                try:
                    audio = loop.run_until_complete(
                        self.recorder.record_until_silence(max_duration=10.0)
                    )
                    if not audio or len(audio) < 100:
                        continue

                    result = loop.run_until_complete(self.stt.transcribe(audio))
                    if result.confidence < self.min_confidence:
                        continue

                    self._echo.record_utterance(result.text)
                    cleaned = self._clean_text(result.text)
                    if cleaned:
                        log.info("Dictation: '%s' (conf=%.2f)", cleaned, result.confidence)
                        loop.run_until_complete(
                            self._result_queue.put(
                                DictationResult(
                                    text=cleaned,
                                    confidence=result.confidence,
                                    duration_ms=result.duration_ms,
                                )
                            )
                        )
                except Exception as e:
                    log.error("Dictation: loop error: %s", e)
        finally:
            loop.close()

    def start(self) -> None:
        if self._active:
            return
        self._active = True
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()
        log.info("Dictation: started")

    def stop(self) -> None:
        self._active = False
        if self._thread:
            self._thread.join(timeout=3)
        log.info("Dictation: stopped")

    async def next_result(self, timeout: float = 30.0) -> DictationResult | None:
        try:
            return await asyncio.wait_for(self._result_queue.get(), timeout=timeout)
        except TimeoutError:
            return None

    # ── Hotkey Mode (push-to-talk dictation) ──

    def start_hotkey_mode(
        self,
        hotkey: str = "ctrl+alt",
        on_result: Callable[[DictationResult], None] | None = None,
    ) -> None:
        """Start push-to-talk dictation via a global hotkey.

        Hold the hotkey -> speak -> release -> text is transcribed and typed.
        Requires the ``keyboard`` library (Linux) or ``pynput``.
        Falls back to a polling loop if neither is available.
        """
        if self._active:
            return

        self._active = True
        self._hotkey_on_result = on_result
        self._hotkey_thread = threading.Thread(
            target=self._hotkey_listener, args=(hotkey,), daemon=True
        )
        self._hotkey_thread.start()
        log.info("Dictation: hotkey mode started (hotkey=%s)", hotkey)

    def stop_hotkey_mode(self) -> None:
        self._active = False
        if self._hotkey_thread:
            self._hotkey_thread.join(timeout=3)
            self._hotkey_thread = None
        log.info("Dictation: hotkey mode stopped")

    def _hotkey_listener(self, hotkey: str) -> None:
        try:
            import keyboard

            log.info("Dictation: using 'keyboard' library for hotkey")
            press_time = 0.0
            recording = False
            audio_chunks: list[bytes] = []

            def on_press():
                nonlocal press_time, recording, audio_chunks
                press_time = time.time()
                recording = True
                audio_chunks = []
                log.info("Dictation: recording started")

            def on_release():
                nonlocal recording
                if not recording:
                    return
                recording = False
                elapsed = time.time() - press_time
                if elapsed < 0.3:
                    log.info("Dictation: too short, ignoring")
                    return
                audio_data = b"".join(audio_chunks)
                self._process_dictation_audio(audio_data)

            keyboard.on_press_key(hotkey, lambda _: on_press(), suppress=True)
            keyboard.on_release_key(hotkey, lambda _: on_release(), suppress=True)

            while self._active:
                if recording:
                    chunk = self._record_chunk()
                    if chunk:
                        audio_chunks.append(chunk)
                else:
                    time.sleep(0.01)

        except ImportError:
            log.warning("Dictation: 'keyboard' library not available, falling back to polling")
            self._hotkey_polling_loop()

    def _hotkey_polling_loop(self) -> None:
        try:
            import pynput.keyboard as pynput_kb
        except ImportError:
            log.error(
                "Dictation: neither 'keyboard' nor 'pynput' available. "
                "Install one with: pip install keyboard"
            )
            return

        press_time = 0.0
        recording = False
        audio_chunks: list[bytes] = []

        def on_press(key):
            nonlocal press_time, recording, audio_chunks
            try:
                if key == pynput_kb.Key.ctrl_l or key == pynput_kb.Key.ctrl_r:
                    pass
            except Exception:
                pass
            press_time = time.time()
            if not recording:
                recording = True
                audio_chunks = []
                log.info("Dictation: recording started (pynput)")

        def on_release(key):
            nonlocal recording
            if recording:
                recording = False
                elapsed = time.time() - press_time
                if elapsed < 0.3:
                    return
                audio_data = b"".join(audio_chunks)
                self._process_dictation_audio(audio_data)

        listener = pynput_kb.Listener(on_press=on_press, on_release=on_release)
        listener.start()

        while self._active:
            if recording:
                chunk = self._record_chunk()
                if chunk:
                    audio_chunks.append(chunk)
            else:
                time.sleep(0.01)

        listener.stop()

    def _record_chunk(self) -> bytes:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.recorder.record(duration=0.5, timeout=1.0))
        except Exception:
            return b""
        finally:
            loop.close()

    def _process_dictation_audio(self, audio_data: bytes) -> None:
        if not audio_data or len(audio_data) < 1000:
            return
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(self.stt.transcribe(audio_data))
            if result.confidence < self.min_confidence:
                log.info("Dictation: low confidence (%.2f), skipping", result.confidence)
                return
            cleaned = self._clean_text(result.text)
            if not cleaned:
                return
            self._echo.record_utterance(cleaned)
            dr = DictationResult(
                text=cleaned,
                confidence=result.confidence,
                duration_ms=result.duration_ms,
                filler_removed=self.filler_removal and cleaned != result.text,
            )
            log.info("Dictation: '%s' (conf=%.2f)", cleaned, result.confidence)
            self._simulate_typing(cleaned)
            if self._hotkey_on_result:
                self._hotkey_on_result(dr)
        except Exception as e:
            log.error("Dictation: processing error: %s", e)
        finally:
            loop.close()

    @staticmethod
    def _simulate_typing(text: str) -> None:
        """Type text into the currently focused application."""
        try:
            subprocess.run(
                ["xdotool", "type", "--", text],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        except FileNotFoundError:
            try:
                subprocess.run(
                    ["ydotool", "type", text],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                )
            except FileNotFoundError:
                try:
                    import pyautogui

                    pyautogui.write(text, interval=0.005)
                except ImportError:
                    log.warning("Dictation: no typing tool found (install xdotool or ydotool)")

    def simulate_typing(self, text: str) -> None:
        self._simulate_typing(text)
