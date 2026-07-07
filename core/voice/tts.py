from __future__ import annotations

import asyncio
import os
import tempfile
from dataclasses import dataclass, field
from typing import Protocol

from core.log import log
from core.voice.languages import LANGUAGE_VOICES, get_voice_for_language


TTS_VOICES = {
    "alloy": "OpenAI - versatile, balanced",
    "echo": "OpenAI - deep, male",
    "fable": "OpenAI - British, storytelling",
    "nova": "OpenAI - female, warm",
    "onyx": "OpenAI - deep, authoritative",
    "shimmer": "OpenAI - female, clear",
}

TTS_EMOTIONS = {
    "neutral": "Default, neutral tone",
    "happy": "Cheerful, bright delivery",
    "excited": "Energetic, enthusiastic",
    "sad": "Somber, gentle delivery",
    "angry": "Firm, assertive tone",
    "surprised": "Curious, lifted pitch",
    "whisper": "Soft, hushed delivery",
    "fearful": "Tense, cautious tone",
}


@dataclass
class TTSResult:
    audio_data: bytes = b""
    format: str = "wav"
    duration_ms: float = 0.0
    text: str = ""
    characters: int = 0
    path: str = ""
    provider: str = ""


class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        ...
    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        ...


class DummyTTSProvider:
    def __init__(self, format: str = "wav"):
        self._format = format

    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        audio = f"[AUDIO:{text}]".encode()
        return TTSResult(
            audio_data=audio, format=self._format,
            duration_ms=len(audio) * 10.0, text=text,
            characters=len(text), provider="dummy",
        )

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        audio = f"[AUDIO:{text}]".encode()
        with open(path, "wb") as f:
            f.write(audio)
        return path


class OpenAITTSProvider:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=self.api_key)
        voice = voice or "shimmer"
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            response = await client.audio.speech.create(
                model="tts-1", voice=voice, input=text,
                speed=speed, response_format="mp3",
            )
            response.stream_to_file(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_data = f.read()
            return TTSResult(
                audio_data=audio_data, format="mp3",
                duration_ms=0, text=text,
                characters=len(text), path=tmp.name,
                provider="openai_tts",
            )
        except Exception:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            raise

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        result = await self.synthesize(text, voice, speed)
        with open(path, "wb") as f:
            f.write(result.audio_data)
        return path


class GTTSSynthesizer:
    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        import asyncio
        from gtts import gTTS
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            tts = gTTS(text=text, lang="en", slow=False)
            await asyncio.to_thread(tts.save, tmp.name)
            with open(tmp.name, "rb") as f:
                audio_data = f.read()
            return TTSResult(
                audio_data=audio_data, format="mp3",
                duration_ms=0, text=text,
                characters=len(text), path=tmp.name,
                provider="gtts",
            )
        except Exception:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            raise

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        result = await self.synthesize(text, voice, speed)
        with open(path, "wb") as f:
            f.write(result.audio_data)
        return path


class PyTTSEngine:
    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        import asyncio
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        await asyncio.to_thread(engine.save_to_file, text, tmp.name)
        await asyncio.to_thread(engine.runAndWait)
        with open(tmp.name, "rb") as f:
            audio_data = f.read()
        return TTSResult(
            audio_data=audio_data, format="wav",
            duration_ms=0, text=text,
            characters=len(text), path=tmp.name,
            provider="pyttsx3",
        )

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        result = await self.synthesize(text, voice, speed)
        with open(path, "wb") as f:
            f.write(result.audio_data)
        return path


class PiperTTSProvider:
    """Local neural TTS using Piper. Downloads ~60MB model on first use.
    Fully offline, fast synthesis, multiple voices available.
    """
    MODEL_URLS = {
        "en_GB-alan-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx",
        "en_US-amy-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx",
        "en_US-lessac-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
    }
    CONFIG_URLS = {
        "en_GB-alan-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/en_GB-alan-medium.onnx.json",
        "en_US-amy-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json",
        "en_US-lessac-medium": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
    }

    def __init__(self, model_name: str = "en_GB-alan-medium", models_dir: str = ""):
        self.model_name = model_name
        self.models_dir = models_dir or os.path.expanduser("~/.local/share/lumina/piper")
        self._model_path = ""
        self._config_path = ""

    def _ensure_model(self) -> tuple[str, str]:
        os.makedirs(self.models_dir, exist_ok=True)
        model_path = os.path.join(self.models_dir, f"{self.model_name}.onnx")
        config_path = os.path.join(self.models_dir, f"{self.model_name}.onnx.json")

        if not os.path.exists(model_path):
            url = self.MODEL_URLS.get(self.model_name)
            if not url:
                raise RuntimeError(f"Unknown Piper model: {self.model_name}. Available: {list(self.MODEL_URLS.keys())}")
            log.info("Piper: downloading model %s from %s", self.model_name, url)
            import urllib.request
            urllib.request.urlretrieve(url, model_path)
            log.info("Piper: model downloaded to %s", model_path)

        if not os.path.exists(config_path):
            url = self.CONFIG_URLS.get(self.model_name)
            if url:
                log.info("Piper: downloading config for %s", self.model_name)
                import urllib.request
                urllib.request.urlretrieve(url, config_path)

        return model_path, config_path

    async def _synthesize_piper(self, text: str, path: str) -> None:
        model_path, config_path = self._ensure_model()
        proc = await asyncio.create_subprocess_exec(
            "piper",
            "--model", model_path,
            "--config", config_path,
            "--output_file", path,
            "--sentence-silence", "0.2",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
            input=text.encode("utf-8"),
        )
        await proc.communicate()

    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        try:
            await self._synthesize_piper(text, tmp.name)
            with open(tmp.name, "rb") as f:
                audio_data = f.read()
            return TTSResult(
                audio_data=audio_data, format="wav",
                duration_ms=0, text=text,
                characters=len(text), path=tmp.name,
                provider="piper",
            )
        except Exception:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            raise

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        await self._synthesize_piper(text, path)
        return path


class EmotiVoiceProvider:
    """EmotiVoice TTS provider — emotional synthesis with prompt control.

    Connects to a local (or remote) EmotiVoice instance via its
    OpenAI-compatible TTS API endpoint. Supports emotions: happy,
    excited, sad, angry, surprised, whisper, fearful, neutral.

    The EmotiVoice server defaults to http://localhost:8000.
    """
    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        api_key: str = "",
        default_voice: str = "8051",
        default_emotion: str = "neutral",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.default_voice = default_voice
        self.default_emotion = default_emotion

    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        import httpx
        voice = voice or self.default_voice
        emotion = self.default_emotion
        if ":" in voice:
            parts = voice.split(":", 1)
            voice = parts[0]
            if parts[1] in TTS_EMOTIONS:
                emotion = parts[1]

        prompt = f"{emotion}: {text}" if emotion else text
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/v1/audio/speech",
                json={
                    "model": "emotivoice",
                    "input": prompt,
                    "voice": voice,
                    "speed": speed,
                },
                headers=headers,
            )
            resp.raise_for_status()
            audio_data = resp.content

        return TTSResult(
            audio_data=audio_data, format="mp3",
            duration_ms=0, text=text,
            characters=len(text), provider="emotivoice",
        )

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        result = await self.synthesize(text, voice, speed)
        with open(path, "wb") as f:
            f.write(result.audio_data)
        return path

    def list_voices(self) -> list[str]:
        return ["8044", "8047", "8051", "8054", "8063", "9065",
                "9069", "9081", "9085", "9102", "9116", "9120"]

    def list_emotions(self) -> list[str]:
        return list(TTS_EMOTIONS.keys())


class EdgeTTSProvider:
    """Microsoft Edge TTS — free neural TTS with 400+ voices in 100+ languages.

    Uses the ``edge-tts`` Python package (pip install edge-tts).
    Caches voices after first use. Supports SSML and rate/pitch control.
    """
    def __init__(self):
        self._voices_cache: dict[str, str] = {}

    async def synthesize(self, text: str, voice: str = "", speed: float = 1.0) -> TTSResult:
        import edge_tts
        voice = voice or "en-US-JennyNeural"
        rate = f"+{int((speed - 1) * 100)}%" if speed >= 1.0 else f"-{int((1 - speed) * 100)}%"
        tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        tmp.close()
        try:
            communicate = edge_tts.Communicate(text, voice, rate=rate)
            await communicate.save(tmp.name)
            with open(tmp.name, "rb") as f:
                audio_data = f.read()
            return TTSResult(
                audio_data=audio_data, format="mp3",
                duration_ms=0, text=text,
                characters=len(text), path=tmp.name,
                provider="edge_tts",
            )
        except Exception:
            try:
                os.unlink(tmp.name)
            except OSError:
                pass
            raise

    async def synthesize_to_file(self, text: str, path: str, voice: str = "", speed: float = 1.0) -> str:
        import edge_tts
        voice = voice or "en-US-JennyNeural"
        rate = f"+{int((speed - 1) * 100)}%" if speed >= 1.0 else f"-{int((1 - speed) * 100)}%"
        communicate = edge_tts.Communicate(text, voice, rate=rate)
        await communicate.save(path)
        return path

    @staticmethod
    def list_language_voices() -> dict[str, str]:
        return {code: lv.edge_voice for code, lv in LANGUAGE_VOICES.items()}


class TTSEngine:
    def __init__(self, provider: TTSProvider | None = None, default_voice: str = "shimmer"):
        self.default_voice = default_voice
        self._provider: TTSProvider | None = None
        self._providers: list[TTSProvider] = []
        if provider:
            self._provider = provider
        else:
            self._init_providers()

    def _init_providers(self) -> None:
        try:
            import edge_tts  # noqa: F401
            self._providers.append(EdgeTTSProvider())
        except ImportError:
            log.info("TTS: edge-tts not installed (pip install edge-tts for 100+ languages)")
        if os.getenv("EMOTIVOICE_URL"):
            self._providers.append(EmotiVoiceProvider(
                base_url=os.getenv("EMOTIVOICE_URL"),
                default_emotion=os.getenv("EMOTIVOICE_EMOTION", "neutral"),
            ))
        if os.getenv("PIPER_MODEL"):
            self._providers.append(PiperTTSProvider(model_name=os.getenv("PIPER_MODEL")))
        if os.getenv("OPENAI_API_KEY"):
            self._providers.append(OpenAITTSProvider())
        try:
            import gtts  # noqa: F401
            self._providers.append(GTTSSynthesizer())
        except ImportError:
            pass
        try:
            import pyttsx3  # noqa: F401
            self._providers.append(PyTTSEngine())
        except ImportError:
            pass
        if not self._providers:
            if os.system("which piper >/dev/null 2>&1") == 0:
                self._providers.append(PiperTTSProvider())
            else:
                self._providers.append(GTTSSynthesizer())

    def set_provider(self, provider: TTSProvider) -> None:
        self._provider = provider
        self._providers = [provider]

    async def speak_in_language(self, text: str, lang_code: str = "", speed: float = 1.0, play: bool = True) -> TTSResult:
        """Speak text auto-selecting the best voice for the given language code."""
        if not lang_code:
            lang_code = "en"
        lv = get_voice_for_language(lang_code)
        voice = lv.edge_voice
        log.info("TTS: speaking in %s (%s) with voice %s", lv.name, lang_code, voice)
        return await self.speak(text, voice=voice, speed=speed, play=play)

    async def speak(self, text: str, voice: str = "", speed: float = 1.0, play: bool = True) -> TTSResult:
        voice = voice or self.default_voice
        if self._provider:
            result = await self._provider.synthesize(text, voice, speed)
            if play:
                await self._play_audio(result)
            return result
        last_error = ""
        for p in self._providers:
            try:
                result = await p.synthesize(text, voice, speed)
                if play:
                    await self._play_audio(result)
                return result
            except Exception as e:
                last_error = str(e)
                log.warning("TTS: provider %s failed: %s", type(p).__name__, e)
                continue
        raise RuntimeError(f"All TTS providers failed. Last error: {last_error}")

    async def _play_audio(self, result: TTSResult) -> None:
        for player in ["ffplay", "aplay", "paplay", "mpg123", "sox"]:
            if os.system(f"which {player} >/dev/null 2>&1") == 0:
                await asyncio.create_subprocess_exec(
                    player, result.path,
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                return
        log.warning("TTS: no audio player found to play %s", result.path)

    def speak_async(self, text: str, voice: str = "", speed: float = 1.0, on_done=None) -> None:
        import threading
        def _run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(self.speak(text, voice, speed, play=True))
                if on_done:
                    on_done(result)
            finally:
                loop.close()
        threading.Thread(target=_run, daemon=True).start()

    def list_voices(self) -> dict:
        voices = dict(TTS_VOICES)
        for code, lv in LANGUAGE_VOICES.items():
            voices[lv.edge_voice] = f"EdgeTTS - {lv.name} ({lv.native_name})"
        voices["emoti_8044"] = "EmotiVoice - Speaker 8044"
        voices["emoti_8051"] = "EmotiVoice - Speaker 8051"
        voices["emoti_8051:happy"] = "EmotiVoice - Speaker 8051, happy"
        voices["emoti_8051:excited"] = "EmotiVoice - Speaker 8051, excited"
        voices["emoti_8051:sad"] = "EmotiVoice - Speaker 8051, sad"
        voices["emoti_8051:angry"] = "EmotiVoice - Speaker 8051, angry"
        voices["en_GB-alan-medium"] = "Piper - British male (Alan)"
        voices["en_US-amy-medium"] = "Piper - US female (Amy)"
        voices["en_US-lessac-medium"] = "Piper - US female (Lessac)"
        return voices


tts = TTSEngine()
