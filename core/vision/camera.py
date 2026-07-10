from __future__ import annotations

import asyncio
import contextlib
import time
from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import cv2
    import numpy as np

from core.log import log

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class CameraError(Exception): ...


class CameraProperty(Enum):
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    SATURATION = "saturation"
    HUE = "hue"
    GAIN = "gain"
    EXPOSURE = "exposure"
    WIDTH = "width"
    HEIGHT = "height"
    FPS = "fps"
    AUTO_FOCUS = "auto_focus"
    AUTO_WHITE_BALANCE = "auto_white_balance"


class CameraInfo:
    def __init__(
        self,
        device_id: int = 0,
        name: str = "",
        width: int = 640,
        height: int = 480,
        fps: int = 30,
        available: bool = False,
        backends: list[str] | None = None,
    ):
        self.device_id = device_id
        self.name = name or f"Camera {device_id}"
        self.width = width
        self.height = height
        self.fps = fps
        self.available = available
        self.backends = backends or []

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "available": self.available,
            "backends": self.backends,
        }


class Frame:
    def __init__(
        self,
        data: bytes,
        width: int,
        height: int,
        format: str = "jpeg",
        timestamp: float | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.data = data
        self.width = width
        self.height = height
        self.format = format
        self.timestamp = timestamp or time.time()
        self.metadata = metadata or {}

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=UTC)

    def to_dict(self) -> dict[str, Any]:
        return {
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "timestamp": self.timestamp,
            "size_bytes": len(self.data),
            "metadata": self.metadata,
        }


class CameraDevice:
    def __init__(self, device_id: int = 0, backend: Any = None):
        self.device_id = device_id
        self._backend = backend
        self._cap: cv2.VideoCapture | None = None
        self._open = False
        self._lock = asyncio.Lock()
        self._frame_count = 0
        self._info = CameraInfo(device_id=device_id)
        self._preferred_width = 640
        self._preferred_height = 480
        self._preferred_fps = 30

    @property
    def is_open(self) -> bool:
        return self._open and self._cap is not None

    @property
    def info(self) -> CameraInfo:
        return self._info

    def open(self) -> bool:
        if not CV2_AVAILABLE:
            log.warning("Vision: OpenCV not installed, cannot open camera")
            return False

        if self._open:
            return True

        try:
            if self._backend is not None:
                self._cap = cv2.VideoCapture(self.device_id, self._backend)
            else:
                self._cap = cv2.VideoCapture(self.device_id)

            if not self._cap.isOpened():
                self._cap = None
                return False

            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, self._preferred_width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self._preferred_height)
            self._cap.set(cv2.CAP_PROP_FPS, self._preferred_fps)

            actual_w = int(self._cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self._cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self._cap.get(cv2.CAP_PROP_FPS)

            self._info = CameraInfo(
                device_id=self.device_id,
                width=actual_w or self._preferred_width,
                height=actual_h or self._preferred_height,
                fps=int(actual_fps) or self._preferred_fps,
                available=True,
            )
            self._open = True
            log.info(
                "Vision: Camera %d opened (%dx%d @ %dfps)",
                self.device_id,
                actual_w,
                actual_h,
                int(actual_fps),
            )
            return True

        except Exception as e:
            log.error("Vision: Failed to open camera %d: %s", self.device_id, e)
            self._cap = None
            return False

    def close(self) -> None:
        if self._cap is not None:
            with contextlib.suppress(Exception):
                self._cap.release()
        self._cap = None
        self._open = False
        log.info("Vision: Camera %d closed", self.device_id)

    async def capture_frame(
        self,
        format: str = "jpeg",
        quality: int = 85,
    ) -> Frame | None:
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            log.warning("Vision: OpenCV or NumPy not available")
            return None

        async with self._lock:
            if not self.is_open:
                opened = self.open()
                if not opened:
                    return None

            try:
                assert self._cap is not None
                ret, frame_np = self._cap.read()
                if not ret or frame_np is None:
                    log.warning("Vision: Failed to capture frame from camera %d", self.device_id)
                    return None

                self._frame_count += 1
                height, width = frame_np.shape[:2]

                encode_params = self._encode_params(format, quality, frame_np)
                ret_bytes, buffer = cv2.imencode(f".{format}", frame_np, encode_params)
                if not ret_bytes:
                    return None

                data = buffer.tobytes()
                return Frame(
                    data=data,
                    width=width,
                    height=height,
                    format=format,
                    metadata={"frame_number": self._frame_count, "device_id": self.device_id},
                )
            except Exception as e:
                log.error("Vision: Capture error: %s", e)
                return None

    async def capture_numpy(self) -> np.ndarray | None:
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return None

        async with self._lock:
            if not self.is_open:
                opened = self.open()
                if not opened:
                    return None

            try:
                assert self._cap is not None
                ret, frame_np = self._cap.read()
                if not ret or frame_np is None:
                    return None
                self._frame_count += 1
                return frame_np
            except Exception:
                return None

    def _encode_params(
        self,
        format: str,
        quality: int,
        frame_np: np.ndarray,
    ) -> list[int]:
        if format == "jpg" or format == "jpeg":
            return [cv2.IMWRITE_JPEG_QUALITY, quality]
        elif format == "png":
            return [cv2.IMWRITE_PNG_COMPRESSION, min(9, quality // 10)]
        elif format == "webp":
            return [cv2.IMWRITE_WEBP_QUALITY, quality]
        return []

    async def get_frame_bytes(self, format: str = "jpeg", quality: int = 85) -> bytes | None:
        frame = await self.capture_frame(format=format, quality=quality)
        return frame.data if frame else None

    def set_resolution(self, width: int, height: int) -> None:
        self._preferred_width = width
        self._preferred_height = height
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def set_fps(self, fps: int) -> None:
        self._preferred_fps = fps
        if self._cap is not None:
            self._cap.set(cv2.CAP_PROP_FPS, fps)

    async def set_property(self, prop: CameraProperty, value: float) -> bool:
        if not CV2_AVAILABLE or self._cap is None:
            return False

        prop_map = {
            CameraProperty.BRIGHTNESS: cv2.CAP_PROP_BRIGHTNESS,
            CameraProperty.CONTRAST: cv2.CAP_PROP_CONTRAST,
            CameraProperty.SATURATION: cv2.CAP_PROP_SATURATION,
            CameraProperty.HUE: cv2.CAP_PROP_HUE,
            CameraProperty.GAIN: cv2.CAP_PROP_GAIN,
            CameraProperty.EXPOSURE: cv2.CAP_PROP_EXPOSURE,
            CameraProperty.WIDTH: cv2.CAP_PROP_FRAME_WIDTH,
            CameraProperty.HEIGHT: cv2.CAP_PROP_FRAME_HEIGHT,
            CameraProperty.FPS: cv2.CAP_PROP_FPS,
            CameraProperty.AUTO_FOCUS: cv2.CAP_PROP_AUTOFOCUS,
            CameraProperty.AUTO_WHITE_BALANCE: cv2.CAP_PROP_AUTO_WB,
        }

        cv_prop = prop_map.get(prop)
        if cv_prop is None:
            return False

        try:
            return self._cap.set(cv_prop, value)
        except Exception:
            return False

    async def __aenter__(self) -> CameraDevice:
        self.open()
        return self

    async def __aexit__(self, *args: Any) -> None:
        self.close()


def list_cameras(max_devices: int = 10) -> list[CameraInfo]:
    if not CV2_AVAILABLE:
        return [CameraInfo(available=False)]

    cameras = []
    for i in range(max_devices):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            cap.release()
            cameras.append(
                CameraInfo(
                    device_id=i,
                    width=w,
                    height=h,
                    fps=int(fps),
                    available=True,
                )
            )
        else:
            cap.release()
    return cameras or [CameraInfo(available=False)]
