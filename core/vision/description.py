from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from typing import Any

from core.log import log

try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    cv2 = None  # pyright: ignore[reportAssignmentType]
    CV2_AVAILABLE = False


class SceneDescriptionError(Exception): ...


@dataclass
class SceneDescription:
    summary: str
    objects: list[str]
    people_count: int = 0
    lighting: str = ""
    mood: str = ""
    text_detected: list[str] | None = None
    inference_ms: float = 0.0
    provider: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "summary": self.summary,
            "objects": self.objects,
            "people_count": self.people_count,
            "lighting": self.lighting,
            "mood": self.mood,
            "text_detected": self.text_detected or [],
            "inference_ms": round(self.inference_ms, 1),
            "provider": self.provider,
        }


class SceneDescriber:
    def __init__(self, ai_engine: Any | None = None):
        self._ai_engine = ai_engine
        self._provider = "none"

    def set_ai_engine(self, engine: Any) -> None:
        self._ai_engine = engine
        self._provider = "llm"

    async def describe(
        self,
        frame_np: np.ndarray,
        detail: str = "normal",
        context: str | None = None,
    ) -> SceneDescription:
        if not NUMPY_AVAILABLE:
            return SceneDescription(
                summary="NumPy not available for image processing.",
                objects=[],
                provider=self._provider,
            )

        start = time.time()

        if self._ai_engine is not None:
            return await self._describe_with_llm(frame_np, detail, context, start)
        elif CV2_AVAILABLE:
            return self._describe_basic(frame_np, start)
        else:
            return SceneDescription(
                summary=(
                    "No description engine available (install opencv-python "
                    "or configure AI engine)."
                ),
                objects=[],
                inference_ms=(time.time() - start) * 1000,
                provider=self._provider,
            )

    async def _describe_with_llm(
        self,
        frame_np: np.ndarray,
        detail: str,
        context: str | None,
        start: float,
    ) -> SceneDescription:
        try:
            img_bytes = self._frame_to_jpeg(frame_np)
            if img_bytes is None:
                return SceneDescription(
                    summary="Failed to encode image.",
                    objects=[],
                    inference_ms=(time.time() - start) * 1000,
                    provider=self._provider,
                )

            b64 = base64.b64encode(img_bytes).decode("utf-8")

            prompt = "Describe what you see in this image in detail."
            if context:
                prompt += f"\nContext: {context}"
            if detail == "brief":
                prompt = "Describe this image briefly in 1-2 sentences."

            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{b64}", "detail": detail},
                        },
                    ],
                }
            ]

            assert self._ai_engine is not None
            resp = await self._ai_engine.chat(messages)
            text = resp.get("message", {}).get("content", "")

            elapsed = (time.time() - start) * 1000
            return SceneDescription(
                summary=text,
                objects=[],
                inference_ms=elapsed,
                provider=self._provider,
            )

        except Exception as e:
            log.error("Vision: Scene description LLM error: %s", e)
            return SceneDescription(
                summary=f"Description failed: {e}",
                objects=[],
                inference_ms=(time.time() - start) * 1000,
                provider=self._provider,
            )

    def _describe_basic(
        self,
        frame_np: np.ndarray,
        start: float,
    ) -> SceneDescription:
        if not CV2_AVAILABLE:
            return SceneDescription(
                summary="OpenCV not available for basic description.",
                objects=[],
                provider="none",
            )

        height, width = frame_np.shape[:2]
        assert cv2 is not None
        gray = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
        brightness = float(gray.mean())
        std = float(gray.std())

        lighting = "bright" if brightness > 150 else "dim" if brightness < 50 else "normal"
        mood = "high contrast" if std > 60 else "low contrast" if std < 30 else "balanced"

        elapsed = (time.time() - start) * 1000
        return SceneDescription(
            summary=f"Image is {width}x{height} pixels, {lighting} lighting, {mood} mood.",
            objects=[],
            lighting=lighting,
            mood=mood,
            inference_ms=elapsed,
            provider="basic",
        )

    def _frame_to_jpeg(self, frame_np: np.ndarray, quality: int = 85) -> bytes | None:
        if not CV2_AVAILABLE:
            return None
        assert cv2 is not None
        ret, buf = cv2.imencode(".jpg", frame_np, [cv2.IMWRITE_JPEG_QUALITY, quality])
        if ret:
            return buf.tobytes()
        return None
