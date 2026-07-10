from __future__ import annotations

import asyncio
import contextlib
import math
import os
import tempfile
from dataclasses import dataclass, field
from typing import Any, Protocol

from core.log import log

try:
    from dotenv import load_dotenv

    _env_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"
    )
    load_dotenv(_env_path)
except ImportError:
    pass


@dataclass
class STTResult:
    text: str = ""
    confidence: float = 0.0
    duration_ms: float = 0.0
    is_final: bool = True
    language: str = ""
    segments: list[dict] = field(default_factory=list)
    no_speech_prob: float = 0.0
    avg_logprob: float = 0.0
    provider: str = ""


class STTProvider(Protocol):
    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult: ...
    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult: ...


class DummySTTProvider:
    def __init__(self, responses: dict[str, str] | None = None):
        self.responses = responses or {}

    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult:
        text_key = audio_data.decode("utf-8", errors="replace").strip()
        text = text_key
        for key, val in self.responses.items():
            if key in text_key.lower():
                text = val
                break
        else:
            text = text_key or "hello world"
        return STTResult(
            text=text, confidence=0.95, duration_ms=100.0, is_final=True, provider="dummy"
        )

    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult:
        with open(file_path, "rb") as f:
            data = f.read()
        return await self.transcribe(data, language)


class OpenAIWhisperProvider:
    def __init__(self, api_key: str | None = None, model: str = "whisper-1"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.hallucination_min_confidence: float = 0.3
        self.hallucination_no_speech_threshold: float = 0.5

    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=self.api_key)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
        try:
            kwargs: dict[str, Any] = {"model": self.model, "response_format": "verbose_json"}
            if language:
                kwargs["language"] = language
            if prompt:
                kwargs["prompt"] = prompt
            with open(tmp.name, "rb") as f:
                transcript = await client.audio.transcriptions.create(
                    file=("audio.wav", f, "audio/wav"),
                    **kwargs,
                )
            text = transcript.text if hasattr(transcript, "text") else transcript.get("text", "")
            raw_segments = (
                transcript.segments
                if hasattr(transcript, "segments")
                else transcript.get("segments", [])
            )
            seg_list = []
            avg_logprob = 0.0
            no_speech_prob = 0.0
            if raw_segments:
                for s in raw_segments:
                    sd = (
                        dict(s)
                        if hasattr(s, "keys")
                        else {
                            "text": s.get("text", ""),
                            "confidence": s.get("confidence", 1.0),
                            "no_speech_prob": s.get("no_speech_prob", 0.0),
                            "avg_logprob": s.get("avg_logprob", 0.0),
                        }
                    )
                    seg_list.append(sd)
                avg_logprob = seg_list[0].get("avg_logprob", 0.0) if seg_list else 0.0
                no_speech_prob = seg_list[0].get("no_speech_prob", 0.0) if seg_list else 0.0

            confidence = math.exp(avg_logprob) if avg_logprob < 0 else 1.0

            if no_speech_prob >= self.hallucination_no_speech_threshold:
                return STTResult(
                    text="",
                    confidence=0.0,
                    duration_ms=0.0,
                    is_final=True,
                    no_speech_prob=no_speech_prob,
                    avg_logprob=avg_logprob,
                )
            if confidence < self.hallucination_min_confidence:
                return STTResult(
                    text="",
                    confidence=confidence,
                    duration_ms=0.0,
                    is_final=True,
                    no_speech_prob=no_speech_prob,
                    avg_logprob=avg_logprob,
                )

            lang = (
                transcript.language
                if hasattr(transcript, "language")
                else transcript.get("language", language)
            )
            duration = (
                transcript.duration
                if hasattr(transcript, "duration")
                else transcript.get("duration", 0)
            )
            return STTResult(
                text=text.strip(),
                confidence=confidence,
                duration_ms=duration * 1000 if duration else 0,
                is_final=True,
                language=lang,
                segments=seg_list,
                no_speech_prob=no_speech_prob,
                avg_logprob=avg_logprob,
                provider="openai_whisper",
            )
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp.name)

    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult:
        with open(file_path, "rb") as f:
            data = f.read()
        return await self.transcribe(data, language)


class FasterWhisperProvider:
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.hallucination_min_confidence: float = 0.3
        self.hallucination_no_speech_threshold: float = 0.5
        self._model = None

    async def _get_model(self):
        if self._model is None:
            from faster_whisper import WhisperModel

            self._model = WhisperModel(
                self.model_size, device=self.device, compute_type=self.compute_type
            )
        return self._model

    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult:
        model = await self._get_model()
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_data)
        try:
            segments, info = await asyncio.to_thread(
                model.transcribe,
                tmp.name,
                language=language or None,
                beam_size=5,
            )
            text = " ".join(seg.text for seg in segments)
            no_speech_prob = getattr(info, "no_speech_prob", 0.0)
            avg_logprob = getattr(info, "average_logprob", 0.0)
            confidence = math.exp(avg_logprob) if avg_logprob < 0 else 1.0

            if no_speech_prob >= self.hallucination_no_speech_threshold:
                return STTResult(
                    text="",
                    confidence=0.0,
                    duration_ms=0.0,
                    is_final=True,
                    no_speech_prob=no_speech_prob,
                    avg_logprob=avg_logprob,
                )
            if confidence < self.hallucination_min_confidence:
                return STTResult(
                    text="",
                    confidence=confidence,
                    duration_ms=0.0,
                    is_final=True,
                    no_speech_prob=no_speech_prob,
                    avg_logprob=avg_logprob,
                )

            return STTResult(
                text=text.strip(),
                confidence=confidence,
                duration_ms=info.duration * 1000 if hasattr(info, "duration") else 0,
                is_final=True,
                language=info.language,
                no_speech_prob=no_speech_prob,
                avg_logprob=avg_logprob,
                provider="faster_whisper",
            )
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp.name)

    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult:
        with open(file_path, "rb") as f:
            data = f.read()
        return await self.transcribe(data, language)


class GoogleSTTProvider:
    def __init__(self, credentials_path: str | None = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult:
        from google.cloud import speech  # pyright: ignore[reportAttributeAccessIssue]

        client = speech.SpeechClient()  # pyright: ignore[reportAttributeAccessIssue]
        audio = speech.RecognitionAudio(content=audio_data)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language or "en-US",
            enable_automatic_punctuation=True,
        )
        response = client.recognize(config=config, audio=audio)
        text = " ".join(result.alternatives[0].transcript for result in response.results)
        conf = response.results[0].alternatives[0].confidence if response.results else 0
        return STTResult(
            text=text.strip(),
            confidence=conf,
            duration_ms=0,
            is_final=True,
            language=language or "en-US",
            provider="google_stt",
        )

    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult:
        with open(file_path, "rb") as f:
            data = f.read()
        return await self.transcribe(data, language)


class STTEngine:
    def __init__(self, provider: STTProvider | None = None):
        self._provider: STTProvider | None = None
        self._providers: list[STTProvider] = []
        if provider:
            self._provider = provider
        else:
            self._init_providers()

    def _init_providers(self) -> None:
        try:
            import faster_whisper  # noqa: F401

            self._providers.append(FasterWhisperProvider())
        except ImportError:
            pass
        if os.getenv("OPENAI_API_KEY"):
            self._providers.append(OpenAIWhisperProvider())
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
            self._providers.append(GoogleSTTProvider())
        if not self._providers:
            self._providers.append(OpenAIWhisperProvider())

    def set_provider(self, provider: STTProvider) -> None:
        self._provider = provider
        self._providers = [provider]

    async def transcribe(
        self, audio_data: bytes, language: str = "", prompt: str = ""
    ) -> STTResult:
        if not language:
            language = "en"
        if self._provider:
            return await self._provider.transcribe(audio_data, language, prompt)
        last_error = ""
        for p in self._providers:
            try:
                return await p.transcribe(audio_data, language, prompt)
            except Exception as e:
                last_error = str(e)
                log.warning("STT: provider %s failed: %s", type(p).__name__, e)
                continue
        raise RuntimeError(f"All STT providers failed. Last error: {last_error}")

    async def transcribe_file(self, file_path: str, language: str = "") -> STTResult:
        if self._provider:
            return await self._provider.transcribe_file(file_path, language)
        last_error = ""
        for p in self._providers:
            try:
                return await p.transcribe_file(file_path, language)
            except Exception as e:
                last_error = str(e)
                continue
        raise RuntimeError(f"All STT providers failed. Last error: {last_error}")


stt = STTEngine()
