from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Any, Callable

from core.log import log
from core.vision.camera import CameraDevice, Frame
from core.vision.description import SceneDescriber
from core.vision.detector import ObjectDetector
from core.vision.face import FaceDetector
from core.vision.memory import Observation, VisualShortTermMemory


class WatchMode(Enum):
    IDLE = "idle"
    WATCHING = "watching"
    DESCRIBING = "describing"
    ALERT = "alert"


class VisualCortex:
    """Continuous think-watch-talk pipeline.

    Captures frames at intervals, runs detection + description in background,
    stores observations in short-term memory, detects scene changes,
    and provides answers about what it's seeing.
    """

    def __init__(
        self,
        camera: CameraDevice | None = None,
        ai_engine: Any | None = None,
        watch_interval: float = 3.0,
        enable_detection: bool = True,
        enable_faces: bool = True,
        enable_description: bool = True,
        memory_capacity: int = 60,
        memory_ttl: float = 300.0,
        change_threshold: float = 0.3,
    ):
        self._camera = camera or CameraDevice(device_id=0)
        self._ai_engine = ai_engine
        self._watch_interval = watch_interval
        self._enable_detection = enable_detection
        self._enable_faces = enable_faces
        self._enable_description = enable_description
        self._change_threshold = change_threshold

        self._detector: ObjectDetector | None = None
        self._face_detector: FaceDetector | None = None
        self._describer: SceneDescriber | None = None
        self._memory = VisualShortTermMemory(capacity=memory_capacity, ttl_seconds=memory_ttl)

        self._mode = WatchMode.IDLE
        self._running = False
        self._watch_task: asyncio.Task | None = None
        self._on_change_callbacks: list[Callable[[str], None]] = []
        self._on_observation_callbacks: list[Callable[[Observation], None]] = []
        self._lock = asyncio.Lock()
        self._conversation_history: list[dict] = []
        self._proactive_narration = False

    @property
    def mode(self) -> WatchMode:
        return self._mode

    @property
    def memory(self) -> VisualShortTermMemory:
        return self._memory

    @property
    def is_watching(self) -> bool:
        return self._running

    @property
    def watch_interval(self) -> float:
        return self._watch_interval

    def set_watch_interval(self, interval: float) -> None:
        self._watch_interval = max(1.0, min(60.0, interval))

    def set_proactive_narration(self, enabled: bool) -> None:
        self._proactive_narration = enabled

    def on_change(self, callback: Callable[[str], None]) -> None:
        self._on_change_callbacks.append(callback)

    def on_observation(self, callback: Callable[[Observation], None]) -> None:
        self._on_observation_callbacks.append(callback)

    async def start_watching(self) -> None:
        if self._running:
            return

        if not self._camera.is_open:
            opened = self._camera.open()
            if not opened:
                raise RuntimeError("Failed to open camera")

        if self._enable_detection:
            self._detector = ObjectDetector()
            try:
                await self._detector.initialize()
            except Exception as e:
                log.warning("Vision: Detector init failed: %s", e)
                self._detector = None

        if self._enable_faces:
            self._face_detector = FaceDetector()

        if self._enable_description and self._ai_engine is not None:
            self._describer = SceneDescriber(ai_engine=self._ai_engine)

        self._running = True
        self._mode = WatchMode.WATCHING
        self._watch_task = asyncio.create_task(self._watch_loop())
        log.info("Vision: VisualCortex started watching (every %.1fs)", self._watch_interval)

    async def stop_watching(self) -> None:
        self._running = False
        self._mode = WatchMode.IDLE
        if self._watch_task:
            self._watch_task.cancel()
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass
            self._watch_task = None
        log.info("Vision: VisualCortex stopped watching")

    async def _watch_loop(self) -> None:
        while self._running:
            try:
                await self._observe()
                await asyncio.sleep(self._watch_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error("Vision: Watch loop error: %s", e)
                await asyncio.sleep(1.0)

    async def _observe(self) -> Observation:
        frame_np = await self._camera.capture_numpy()
        if frame_np is None:
            return Observation(timestamp=time.time(), summary="Failed to capture frame.")

        frame = await self._camera.capture_frame(format="jpeg", quality=70)
        obs = Observation(timestamp=time.time(), frame=frame)

        tasks = []

        if self._detector:
            tasks.append(self._observe_detections(frame_np, obs))
        if self._face_detector:
            tasks.append(self._observe_faces(frame_np, obs))
        if self._describer:
            tasks.append(self._observe_description(frame_np, obs))

        if tasks:
            await asyncio.gather(*tasks)

        obs.labels = []
        if obs.detections:
            obs.labels = obs.detections.labels
        if obs.faces:
            obs.people_count = obs.faces.count
            if "person" not in obs.labels and obs.faces.count > 0:
                obs.labels.append("person")
        if obs.description:
            obs.summary = obs.description.summary[:200]

        if not obs.summary and obs.labels:
            obs.summary = f"I see {', '.join(obs.labels)}."

        self._memory.push(obs)

        for cb in self._on_observation_callbacks:
            try:
                cb(obs)
            except Exception as e:
                log.error("Vision: Observation callback error: %s", e)

        change_msg = self._memory.change_detected(obs)
        if change_msg:
            self._mode = WatchMode.ALERT
            for cb in self._on_change_callbacks:
                try:
                    cb(change_msg)
                except Exception as e:
                    log.error("Vision: Change callback error: %s", e)
            if self._proactive_narration:
                log.info("Vision: Change detected: %s", change_msg)
            self._mode = WatchMode.WATCHING

        return obs

    async def _observe_detections(
        self, frame_np: Any, obs: Observation,
    ) -> None:
        if not self._detector:
            return
        try:
            obs.detections = await self._detector.detect(frame_np)
        except Exception as e:
            log.error("Vision: Detection error: %s", e)

    async def _observe_faces(self, frame_np: Any, obs: Observation) -> None:
        if not self._face_detector:
            return
        try:
            obs.faces = await self._face_detector.detect(frame_np)
        except Exception as e:
            log.error("Vision: Face detection error: %s", e)

    async def _observe_description(
        self, frame_np: Any, obs: Observation,
    ) -> None:
        if not self._describer:
            return
        try:
            obs.description = await self._describer.describe(
                frame_np, detail="brief",
            )
        except Exception as e:
            log.error("Vision: Description error: %s", e)

    async def what_do_you_see(self, context: str | None = None) -> str:
        current = self._memory.current
        if current is None or current.age_seconds > 10.0:
            obs = await self._observe()
            return self._summarize_observation(obs, context)
        return self._summarize_observation(current, context)

    async def capture_and_describe(self, detail: str = "normal") -> str:
        obs = await self._observe()
        if obs.description and obs.description.summary:
            return obs.description.summary
        return obs.summary or "I see nothing in particular."

    async def look_for(
        self, target: str, timeout: float = 30.0,
    ) -> str:
        target = target.lower()
        if not self._running:
            await self.start_watching()

        start = time.time()
        while time.time() - start < timeout:
            if self._memory.has_seen(target, within_seconds=5):
                return f"I see {target} right now."
            await asyncio.sleep(self._watch_interval)
            obs = await self._observe()
            if target in [l.lower() for l in obs.labels]:
                return f"I found {target}!"

        recent = self._memory.get_recent(seconds=30)
        seen_labels = set()
        for o in recent:
            seen_labels.update(o.labels)
        if seen_labels:
            return f"I looked but didn't see {target}. I have seen: {', '.join(sorted(seen_labels))}."
        return f"I searched for {target} but couldn't find it."

    async def describe_current_scene(self) -> str:
        obs = await self._observe()
        parts = []
        if obs.people_count > 0:
            parts.append(f"I see {obs.people_count} person{'s' if obs.people_count > 1 else ''}")
        if obs.labels:
            parts.append(f"Objects: {', '.join(obs.labels[:10])}")
        if obs.description and obs.description.summary:
            parts.append(obs.description.summary)
        return " ".join(parts) if parts else "I don't see anything specific."

    async def ask_about_scene(self, question: str) -> str:
        current = self._memory.current
        if current is None or current.age_seconds > 15.0:
            current = await self._observe()

        context_parts = []
        if current.summary:
            context_parts.append(f"Scene: {current.summary}")
        if current.labels:
            context_parts.append(f"Objects detected: {', '.join(current.labels)}")
        if current.people_count:
            context_parts.append(f"People: {current.people_count}")
        if current.description and current.description.lighting:
            context_parts.append(f"Lighting: {current.description.lighting}, Mood: {current.description.mood}")

        context_str = "\n".join(context_parts) if context_parts else "No visual data available."

        prompt = f"""You are looking through a camera. Here is your visual context:

{context_str}

The user asks: "{question}"

Answer conversationally based on what you can see. If you don't have enough visual info, say so."""

        try:
            resp = await self._ai_engine.chat([{"role": "user", "content": prompt}])
            return resp.get("message", {}).get("content", "I'm not sure what to say about that.")
        except Exception as e:
            return f"I couldn't analyze the scene: {e}"

    def _summarize_observation(self, obs: Observation, context: str | None = None) -> str:
        parts = []
        if obs.people_count > 0:
            parts.append(f"I can see {obs.people_count} person{'s' if obs.people_count > 1 else ''}")
        if obs.labels:
            parts.append(f"I notice {', '.join(obs.labels[:8])}")
        if obs.description and obs.description.summary:
            summary = obs.description.summary
            if len(summary) > 300:
                summary = summary[:300] + "..."
            parts.append(summary)
        if context:
            parts.append(f"(Context: {context})")
        return " ".join(parts) if parts else "I don't see anything at the moment."

    async def get_status(self) -> dict:
        current = self._memory.current
        recent = self._memory.get_recent(seconds=60)
        return {
            "mode": self._mode.value,
            "watching": self._running,
            "watch_interval": self._watch_interval,
            "memory_size": self._memory.size,
            "memory_capacity": self._memory.capacity,
            "recent_observations_minutes": len(recent),
            "current_observation": current.to_dict() if current else None,
            "detection_enabled": self._enable_detection,
            "faces_enabled": self._enable_faces,
            "description_enabled": self._enable_description,
            "proactive_narration": self._proactive_narration,
        }

    async def close(self) -> None:
        await self.stop_watching()
        if self._camera:
            self._camera.close()
