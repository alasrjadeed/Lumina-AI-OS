from __future__ import annotations

import asyncio
import time
from typing import Any, AsyncIterator, Callable

from core.log import log
from core.vision.camera import CameraDevice, Frame

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class FrameProcessor:
    async def process(self, frame: Frame) -> Frame:
        return frame


class VideoStream:
    def __init__(
        self,
        camera: CameraDevice,
        fps: int = 15,
        format: str = "jpeg",
        quality: int = 70,
    ):
        self._camera = camera
        self._fps = fps
        self._format = format
        self._quality = quality
        self._frame_interval = 1.0 / fps
        self._running = False
        self._subscribers: list[Callable[[Frame], None]] = []
        self._processors: list[FrameProcessor] = []
        self._frame_count = 0

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def fps(self) -> int:
        return self._fps

    @property
    def frame_count(self) -> int:
        return self._frame_count

    def subscribe(self, callback: Callable[[Frame], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Frame], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def add_processor(self, processor: FrameProcessor) -> None:
        self._processors.append(processor)

    async def start(self) -> None:
        if self._running:
            return

        if not self._camera.is_open:
            opened = self._camera.open()
            if not opened:
                raise RuntimeError("Failed to open camera for streaming")

        self._running = True
        log.info("Vision: Stream started at %d fps", self._fps)

    async def stop(self) -> None:
        self._running = False
        log.info("Vision: Stream stopped")

    async def stream_frames(self) -> AsyncIterator[Frame]:
        if not self._running:
            await self.start()

        while self._running:
            frame_start = time.time()

            frame = await self._camera.capture_frame(
                format=self._format, quality=self._quality,
            )

            if frame is not None:
                for processor in self._processors:
                    frame = await processor.process(frame)

                self._frame_count += 1
                for cb in self._subscribers:
                    try:
                        cb(frame)
                    except Exception as e:
                        log.error("Vision: Stream subscriber error: %s", e)

                yield frame

            elapsed = time.time() - frame_start
            sleep_time = self._frame_interval - elapsed
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)

    async def stream_jpeg(self) -> AsyncIterator[bytes]:
        async for frame in self.stream_frames():
            yield frame.data

    async def capture_burst(
        self, count: int = 5, interval: float = 0.1,
    ) -> list[Frame]:
        frames: list[Frame] = []
        for _ in range(count):
            frame = await self._camera.capture_frame(
                format=self._format, quality=self._quality,
            )
            if frame is not None:
                frames.append(frame)
            await asyncio.sleep(interval)
        return frames

    async def stream_mjpeg(
        self,
        boundary: str = "frame",
    ) -> AsyncIterator[bytes]:
        async for frame in self.stream_frames():
            yield (
                f"--{boundary}\r\n"
                f"Content-Type: image/jpeg\r\n"
                f"Content-Length: {len(frame.data)}\r\n"
                f"X-Timestamp: {frame.timestamp}\r\n"
                f"X-Frame: {frame.metadata.get('frame_number', 0)}\r\n"
                f"\r\n".encode()
            )
            yield frame.data
