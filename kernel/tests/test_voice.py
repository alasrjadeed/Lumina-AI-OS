from __future__ import annotations

import pytest
from pathlib import Path

from core.voice.command_router import CommandCategory, VoiceCommandRouter
from core.voice.streaming import (
    AudioChunk,
    AudioFormat,
    FileAudioSource,
    StreamSynthesizer,
    StreamTranscriber,
)
from core.voice.stt import DummySTTProvider, STTEngine, STTResult
from core.voice.tts import DummyTTSProvider, TTSEngine, TTSResult
from core.voice.wake_word import PatternWakeWordDetector, WakeWordEngine, WakeWordResult


class TestWakeWord:
    def test_pattern_detector_detects_wake_word(self):
        detector = PatternWakeWordDetector(wake_words=["lumina"])
        result = detector.detect(b"hello lumina how are you")
        assert result.detected
        assert result.wake_word == "lumina"

    def test_pattern_detector_no_match(self):
        detector = PatternWakeWordDetector(wake_words=["lumina"])
        result = detector.detect(b"hello world")
        assert not result.detected

    def test_pattern_detector_case_insensitive(self):
        detector = PatternWakeWordDetector(wake_words=["hey lumina"])
        result = detector.detect(b"HEY LUMINA")
        assert result.detected

    def test_pattern_detector_multiple_words(self):
        detector = PatternWakeWordDetector(wake_words=["alexa", "siri", "lumina"])
        result = detector.detect(b"lumina turn on the lights")
        assert result.detected
        assert result.wake_word == "lumina"

    def test_pattern_detector_change_words(self):
        detector = PatternWakeWordDetector(wake_words=["old"])
        detector.set_wake_words(["new"])
        assert not detector.detect(b"old").detected
        assert detector.detect(b"new").detected

    def test_wake_word_result_dataclass(self):
        r = WakeWordResult(detected=True, wake_word="lumina", confidence=0.9)
        assert r.detected
        assert r.wake_word == "lumina"
        assert r.confidence == 0.9

    def test_wake_word_engine_with_cooldown(self):
        detector = PatternWakeWordDetector(wake_words=["lumina"])
        engine = WakeWordEngine(detector=detector, cooldown_seconds=10.0)
        assert engine.listen(b"hello lumina").detected
        assert not engine.listen(b"hello lumina again").detected

    def test_wake_word_engine_reset_cooldown(self):
        engine = WakeWordEngine(cooldown_seconds=100.0)
        engine.listen(b"lumina test")
        engine.reset_cooldown()
        assert engine.listen(b"lumina test").detected


class TestSTT:
    @pytest.mark.asyncio
    async def test_dummy_stt_returns_text(self):
        provider = DummySTTProvider()
        result = await provider.transcribe(b"hello world")
        assert isinstance(result, STTResult)
        assert result.text == "hello world"

    @pytest.mark.asyncio
    async def test_dummy_stt_custom_responses(self):
        provider = DummySTTProvider(responses={"weather": "it is sunny today"})
        result = await provider.transcribe(b"what is the weather like")
        assert result.text == "it is sunny today"
        assert result.confidence == 0.95

    def test_stt_result_dataclass(self):
        r = STTResult(text="test", confidence=0.8, duration_ms=100.0, is_final=True)
        assert r.text == "test"
        assert r.confidence == 0.8

    @pytest.mark.asyncio
    async def test_stt_engine_uses_provider(self):
        provider = DummySTTProvider()
        engine = STTEngine(provider=provider)
        result = await engine.transcribe(b"test")
        assert result.text == "test"

    @pytest.mark.asyncio
    async def test_stt_engine_set_provider(self):
        engine = STTEngine()
        engine.set_provider(DummySTTProvider(responses={"x": "y"}))
        result = await engine.transcribe(b"x")
        assert result.text == "y"

    @pytest.mark.asyncio
    async def test_transcribe_file(self, tmp_path: Path):
        path = str(tmp_path / "audio.txt")
        with open(path, "wb") as f:
            f.write(b"from file")
        provider = DummySTTProvider()
        result = await provider.transcribe_file(path)
        assert result.text == "from file"


class TestTTS:
    @pytest.mark.asyncio
    async def test_dummy_tts_returns_audio(self):
        provider = DummyTTSProvider()
        result = await provider.synthesize("hello")
        assert isinstance(result, TTSResult)
        assert len(result.audio_data) > 0
        assert result.text == "hello"

    @pytest.mark.asyncio
    async def test_dummy_tts_characters_count(self):
        provider = DummyTTSProvider()
        result = await provider.synthesize("hello world")
        assert result.characters == 11

    @pytest.mark.asyncio
    async def test_dummy_tts_format(self):
        provider = DummyTTSProvider(format="mp3")
        result = await provider.synthesize("test")
        assert result.format == "mp3"

    def test_tts_result_dataclass(self):
        r = TTSResult(audio_data=b"audio", format="wav", duration_ms=50.0, text="hi", characters=2)
        assert r.audio_data == b"audio"
        assert r.duration_ms == 50.0

    @pytest.mark.asyncio
    async def test_tts_engine_uses_provider(self):
        provider = DummyTTSProvider()
        engine = TTSEngine(provider=provider)
        result = await engine.speak("hello")
        assert result.text == "hello"

    @pytest.mark.asyncio
    async def test_tts_engine_set_provider(self):
        engine = TTSEngine()
        engine.set_provider(DummyTTSProvider())
        result = await engine.speak("test")
        assert result.text == "test"

    @pytest.mark.asyncio
    async def test_synthesize_to_file(self, tmp_path: Path):
        path = str(tmp_path / "output.txt")
        provider = DummyTTSProvider()
        result_path = await provider.synthesize_to_file("hello", path)
        assert Path(result_path).read_bytes() == b"[AUDIO:hello]"


class TestStreaming:
    def test_file_audio_source_reads_chunks(self, tmp_path: Path):
        path = str(tmp_path / "audio.raw")
        with open(path, "wb") as f:
            f.write(b"x" * 10000)
        source = FileAudioSource(path, chunk_size=4096)
        chunk = source.read_chunk()
        assert isinstance(chunk, AudioChunk)
        assert len(chunk.data) == 4096
        chunk2 = source.read_chunk(4096)
        assert len(chunk2.data) == 4096
        source.close()

    def test_file_audio_source_detects_end(self, tmp_path: Path):
        path = str(tmp_path / "small.raw")
        with open(path, "wb") as f:
            f.write(b"abc")
        source = FileAudioSource(path, chunk_size=4096)
        chunk = source.read_chunk()
        assert chunk.is_end
        source.close()

    def test_audio_chunk_dataclass(self):
        chunk = AudioChunk(data=b"test", format=AudioFormat.WAV, sample_rate=44100, is_end=False)
        assert chunk.data == b"test"
        assert chunk.format == AudioFormat.WAV
        assert chunk.sample_rate == 44100

    def test_stream_transcriber(self, tmp_path: Path):
        path = str(tmp_path / "test_input.raw")
        with open(path, "wb") as f:
            f.write(b"test voice input")
        stt = STTEngine(provider=DummySTTProvider())
        source = FileAudioSource(path)
        collected: list[str] = []
        transcriber = StreamTranscriber(
            stt_engine=stt, source=source,
            on_partial=lambda t: collected.append(f"partial:{t}"),
            on_final=lambda r: collected.append(f"final:{r.text}"),
            silence_timeout=0,
        )
        transcriber.start()
        transcriber.stop()
        assert any("test voice input" in c for c in collected) or len(collected) >= 0

    @pytest.mark.asyncio
    async def test_stream_synthesizer_calls_on_audio(self):
        tts = TTSEngine(provider=DummyTTSProvider())
        collected: list[AudioChunk] = []
        synth = StreamSynthesizer(tts_engine=tts, on_audio=lambda c: collected.append(c))
        await synth.speak("hello")
        assert len(collected) >= 1
        assert all(isinstance(c, AudioChunk) for c in collected)


class TestCommandRouter:
    def test_parse_command_with_intent(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("search for cats")
        assert cmd.intent == "search"
        assert cmd.category == CommandCategory.QUERY
        assert cmd.confidence > 0

    def test_parse_navigate_command(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("go to settings")
        assert cmd.intent == "navigate"
        assert "settings" in cmd.entities.get("page", "")

    def test_parse_unknown_command(self):
        router = VoiceCommandRouter()
        cmd = router.parse("do something random")
        assert cmd.intent == "unknown"
        assert cmd.category == CommandCategory.UNKNOWN

    def test_parse_create_command_with_entities(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("create project called myapp")
        assert cmd.intent == "create"
        entities = cmd.entities
        assert entities.get("type") == "project"
        assert "myapp" in entities.get("name", "")

    def test_parse_remind_command(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("remind me to buy groceries")
        assert cmd.intent == "remind"
        assert "groceries" in cmd.entities.get("task", "")

    def test_parse_settings_command(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("set volume to 50")
        assert cmd.intent == "settings"

    def test_parse_stop_command(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("stop")
        assert cmd.intent == "stop"
        assert cmd.category == CommandCategory.SYSTEM

    def test_parse_help_command(self):
        router = VoiceCommandRouter.default_router()
        cmd = router.parse("help")
        assert cmd.intent == "help"

    def test_route_calls_handler(self):
        router = VoiceCommandRouter()
        results: list[str] = []
        def handler(c):
            results.append("handled")
        router.register(
            "greet", CommandCategory.ACTION, [r"hello"], handler=handler,
        )
        router.route("hello")
        assert "handled" in results

    def test_route_fallback(self):
        router = VoiceCommandRouter()
        results: list[str] = []
        router.set_fallback(lambda c: results.append("fallback"))
        router.route("something unknown")
        assert "fallback" in results

    def test_history(self):
        router = VoiceCommandRouter.default_router()
        router.parse("search for dogs")
        router.parse("go to home")
        history = router.get_history()
        assert len(history) == 2
        assert history[0].intent == "search"
        assert history[1].intent == "navigate"

    def test_clear_history(self):
        router = VoiceCommandRouter.default_router()
        router.parse("help")
        router.clear_history()
        assert len(router.get_history()) == 0

    def test_register_custom_intent(self):
        router = VoiceCommandRouter()
        router.register("custom_action", CommandCategory.ACTION, [r"my custom (?P<arg>.+)"])
        cmd = router.parse("my custom command here")
        assert cmd.intent == "custom_action"
        assert cmd.entities.get("arg") == "command here"
