from __future__ import annotations

import time
from dataclasses import dataclass, field
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
    CV2_AVAILABLE = False

try:
    import face_recognition

    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False


class FaceError(Exception):
    ...


@dataclass
class Face:
    bbox: tuple[float, float, float, float]
    confidence: float = 0.0
    encoding: list[float] | None = None
    name: str | None = None
    landmarks: dict[str, list[tuple[float, float]]] | None = None
    emotion: str | None = None
    age: int | None = None
    gender: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "bbox": [round(v, 3) for v in self.bbox],
            "confidence": round(self.confidence, 3),
            "name": self.name,
            "emotion": self.emotion,
            "age": self.age,
            "gender": self.gender,
        }


@dataclass
class FaceResult:
    faces: list[Face] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    inference_ms: float = 0.0

    @property
    def count(self) -> int:
        return len(self.faces)

    def to_dict(self) -> dict[str, Any]:
        return {
            "faces": [f.to_dict() for f in self.faces],
            "count": self.count,
            "image_size": {"width": self.image_width, "height": self.image_height},
            "inference_ms": round(self.inference_ms, 1),
        }

    def summary(self) -> str:
        if not self.faces:
            return "No faces detected."
        names = [f.name or "Unknown" for f in self.faces if f.name]
        if names:
            return f"Found {len(self.faces)} face(s): {', '.join(names)}."
        return f"Found {len(self.faces)} face(s)."


class FaceDetector:
    def __init__(self):
        self._known_faces: dict[str, list[float]] = {}
        self._known_names: list[str] = []
        self._known_encodings: list[list[float]] = []
        self._backend = "opencv"
        if FACE_RECOGNITION_AVAILABLE:
            self._backend = "face_recognition"

    def add_known_face(self, name: str, encoding: list[float]) -> None:
        if name not in self._known_faces:
            self._known_faces[name] = encoding
            self._known_names.append(name)
            self._known_encodings.append(encoding)

    def remove_known_face(self, name: str) -> bool:
        if name in self._known_faces:
            idx = self._known_names.index(name)
            self._known_names.pop(idx)
            self._known_encodings.pop(idx)
            del self._known_faces[name]
            return True
        return False

    def clear_known_faces(self) -> None:
        self._known_faces.clear()
        self._known_names.clear()
        self._known_encodings.clear()

    async def detect(
        self,
        frame_np: np.ndarray,
    ) -> FaceResult:
        if not CV2_AVAILABLE or not NUMPY_AVAILABLE:
            return FaceResult()

        height, width = frame_np.shape[:2]
        start = time.time()

        if FACE_RECOGNITION_AVAILABLE and self._backend == "face_recognition":
            result = await self._detect_face_recognition(frame_np, width, height)
        else:
            result = await self._detect_opencv(frame_np, width, height)

        result.inference_ms = (time.time() - start) * 1000
        return result

    async def _detect_face_recognition(
        self, frame_np: np.ndarray,
        img_w: int, img_h: int,
    ) -> FaceResult:
        try:
            rgb = cv2.cvtColor(frame_np, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb, model="hog")
            encodings = face_recognition.face_encodings(rgb, locations)

            faces: list[Face] = []
            for loc, enc in zip(locations, encodings):
                top, right, bottom, left = loc
                norm_bbox = (
                    left / img_w, top / img_h,
                    (right - left) / img_w, (bottom - top) / img_h,
                )

                name = None
                if self._known_encodings:
                    matches = face_recognition.compare_faces(
                        self._known_encodings, enc, tolerance=0.6
                    )
                    if any(matches):
                        idx = matches.index(True)
                        name = self._known_names[idx]

                encoded_list = enc.tolist() if hasattr(enc, "tolist") else list(enc)
                faces.append(Face(bbox=norm_bbox, confidence=0.9, encoding=encoded_list, name=name))

            return FaceResult(faces=faces, image_width=img_w, image_height=img_h)
        except Exception as e:
            log.error("Vision: face_recognition error: %s", e)
            return FaceResult(image_width=img_w, image_height=img_h)

    async def _detect_opencv(
        self, frame_np: np.ndarray,
        img_w: int, img_h: int,
    ) -> FaceResult:
        gray = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces_rect = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
        )

        faces: list[Face] = []
        for x, y, w, h in faces_rect:
            norm_bbox = (x / img_w, y / img_h, w / img_w, h / img_h)
            faces.append(Face(bbox=norm_bbox, confidence=0.7))

        return FaceResult(faces=faces, image_width=img_w, image_height=img_h)
