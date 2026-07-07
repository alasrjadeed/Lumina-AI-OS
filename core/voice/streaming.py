from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum

from core.log import log
from core.voice.stt import STTEngine, STTResult
from core.voice.tts import TTSEngine
from core.voice.vad import EnergyVAD, SilenceBuffer


class AudioFormat(Enum):
    PCM16 = "pcm16"
    WAV = "wav"
    MP3 = "mp3"
    OGG = "ogg"


@dataclass
class AudioChunk:
    data: bytes
    format: AudioFormat = AudioFormat.PCM16
    sample_rate: int = 16000
    channels: int = 1
    timestamp: float = field(default_factory=time.time)
    is_end: bool = False


class AudioSource:
    def read_chunk(self, chunk_size: int = 4096) -> AudioChunk:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class MicrophoneSource(AudioSource):
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._stream = None
        self._pyaudio = None

    def _lazy_init(self):
        if self._stream is not None:
            return
        try:
            import pyaudio
            self._pyaudio = pyaudio.PyAudio()
            self._stream = self._pyaudio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=4096,
            )
        except ImportError:
            raise ImportError("pyaudio is required. Install with: pip install pyaudio")

    def read_chunk(self, chunk_size: int = 4096) -> AudioChunk:
        self._lazy_init()
        data = self._stream.read(chunk_size, exception_on_overflow=False)
        return AudioChunk(data=data, format=AudioFormat.PCM16, sample_rate=self.sample_rate)

    def close(self) -> None:
        if self._stream:
            self._stream.stop_stream()
            self._stream.close()
        if self._pyaudio:
            self._pyaudio.terminate()


class FileAudioSource(AudioSource):
    def __init__(self, path: str, chunk_size: int = 4096):
        self.path = path
        self.chunk_size = chunk_size
        self._file = open(path, "rb")

    def read_chunk(self, chunk_size: int | None = None) -> AudioChunk:
        size = chunk_size or self.chunk_size
        data = self._file.read(size)
        is_end = len(data) < size
        return AudioChunk(data=data, is_end=is_end)

    def close(self) -> None:
        self._file.close()


class StreamTranscriber:
    def __init__(
        self,
        stt_engine: STTEngine,
        source: AudioSource,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[STTResult], None] | None = None,
        silence_timeout: float = 1.5,
        vad: EnergyVAD | None = None,
    ):
        self.stt = stt_engine
        self.source = source
        self.on_partial = on_partial
        self.on_final = on_final
        self.silence_timeout = silence_timeout
        self.vad = vad or EnergyVAD()
        self._buffer = b""
        self._running = False
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            last_audio = time.time()
            sil = SilenceBuffer(sample_rate=16000, silence_sec=self.silence_timeout)
            while self._running:
                try:
                    chunk = self.source.read_chunk()
                    if chunk.is_end:
                        break
                    vad_result = self.vad.is_speech(chunk.data)
                    result = sil.add(chunk.data, vad_result.is_speech)
                    if result:
                        final = loop.run_until_complete(self.stt.transcribe(result))
                        if final.text and self.on_final:
                            self.on_final(final)
                        self._buffer = b""
                    elif vad_result.is_speech:
                        self._buffer += chunk.data
                        last_audio = time.time()
                        if len(self._buffer) >= 32000:
                            partial = loop.run_until_complete(self.stt.transcribe(self._buffer))
                            if partial.text and self.on_partial:
                                self.on_partial(partial.text)
                            self._buffer = b""
                except Exception:
                    break
            remaining = sil.flush()
            if remaining:
                final = loop.run_until_complete(self.stt.transcribe(remaining))
                if final.text and self.on_final:
                    self.on_final(final)
        finally:
            loop.close()
        self.source.close()


class StreamSynthesizer:
    def __init__(
        self,
        tts_engine: TTSEngine,
        on_audio: Callable[[AudioChunk], None] | None = None,
        on_done: Callable[[], None] | None = None,
    ):
        self.tts = tts_engine
        self.on_audio = on_audio
        self.on_done = on_done

    async def speak(self, text: str, chunk_size: int = 4096) -> list[AudioChunk]:
        result = await self.tts.speak(text, play=False)
        chunks: list[AudioChunk] = []
        fmt = AudioFormat.MP3
        if result.format == "wav":
            fmt = AudioFormat.WAV
        elif result.format == "ogg":
            fmt = AudioFormat.OGG
        data = result.audio_data
        for i in range(0, len(data), chunk_size):
            is_last = i + chunk_size >= len(data)
            chunk = AudioChunk(
                data=data[i:i + chunk_size],
                format=fmt,
                is_end=is_last,
            )
            chunks.append(chunk)
            if self.on_audio:
                self.on_audio(chunk)
        if self.on_done:
            self.on_done()
        return chunks

    async def speak_stream(self, text_stream: list[str], chunk_size: int = 4096) -> None:
        for text in text_stream:
            await self.speak(text, chunk_size)


class LiveTranscriber:
    def __init__(
        self,
        stt: STTEngine,
        vad: EnergyVAD | None = None,
        sample_rate: int = 16000,
    ):
        self.stt = stt
        self.vad = vad or EnergyVAD()
        self.sample_rate = sample_rate
        self._running = False
        self._on_final: Callable[[STTResult], None] | None = None
        self._source: AudioSource | None = None
        self._transcriber: StreamTranscriber | None = None

    def start(
        self,
        on_final: Callable[[STTResult], None],
        source: AudioSource | None = None,
    ) -> None:
        self._on_final = on_final
        self._source = source or MicrophoneSource(sample_rate=self.sample_rate)
        self._transcriber = StreamTranscriber(
            stt_engine=self.stt,
            source=self._source,
            on_final=on_final,
            vad=self.vad,
        )
        self._transcriber.start()
        self._running = True

    def stop(self) -> None:
        self._running = False
        if self._transcriber:
            self._transcriber.stop()

    @property
    def is_running(self) -> bool:
        return self._running
