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
    from ultralytics import YOLO

    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


class DetectionError(Exception):
    ...


@dataclass
class Detection:
    label: str
    confidence: float
    bbox: tuple[float, float, float, float]
    x: float = 0.0
    y: float = 0.0
    width: float = 0.0
    height: float = 0.0

    def __post_init__(self):
        self.x = self.bbox[0]
        self.y = self.bbox[1]
        self.width = self.bbox[2]
        self.height = self.bbox[3]

    @property
    def center_x(self) -> float:
        return self.x + self.width / 2

    @property
    def center_y(self) -> float:
        return self.y + self.height / 2

    @property
    def area(self) -> float:
        return self.width * self.height

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 3),
            "bbox": [round(v, 3) for v in self.bbox],
            "center": [round(self.center_x, 3), round(self.center_y, 3)],
            "area": round(self.area, 3),
        }


@dataclass
class DetectionResult:
    detections: list[Detection] = field(default_factory=list)
    image_width: int = 0
    image_height: int = 0
    inference_ms: float = 0.0
    provider: str = ""

    @property
    def count(self) -> int:
        return len(self.detections)

    @property
    def labels(self) -> list[str]:
        return list({d.label for d in self.detections})

    def to_dict(self) -> dict[str, Any]:
        return {
            "detections": [d.to_dict() for d in self.detections],
            "count": self.count,
            "labels": self.labels,
            "image_size": {"width": self.image_width, "height": self.image_height},
            "inference_ms": round(self.inference_ms, 1),
            "provider": self.provider,
        }

    def summary(self) -> str:
        if not self.detections:
            return "No objects detected."
        parts: list[str] = []
        label_counts: dict[str, int] = {}
        for d in self.detections:
            label_counts[d.label] = label_counts.get(d.label, 0) + 1
        for label, count in sorted(label_counts.items()):
            parts.append(f"{count} {label}{'s' if count > 1 else ''}")
        return f"Detected: {', '.join(parts)}."


class ObjectDetector:
    COCO_CLASSES: list[str] = [
        "person", "bicycle", "car", "motorcycle", "airplane", "bus",
        "train", "truck", "boat", "traffic light", "fire hydrant",
        "stop sign", "parking meter", "bench", "bird", "cat", "dog",
        "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe",
        "backpack", "umbrella", "handbag", "tie", "suitcase", "frisbee",
        "skis", "snowboard", "sports ball", "kite", "baseball bat",
        "baseball glove", "skateboard", "surfboard", "tennis racket",
        "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl",
        "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
        "hot dog", "pizza", "donut", "cake", "chair", "couch",
        "potted plant", "bed", "dining table", "toilet", "tv", "laptop",
        "mouse", "remote", "keyboard", "cell phone", "microwave", "oven",
        "toaster", "sink", "refrigerator", "book", "clock", "vase",
        "scissors", "teddy bear", "hair drier", "toothbrush",
    ]

    def __init__(
        self,
        model_path: str | None = None,
        confidence_threshold: float = 0.25,
        enable_yolo: bool = True,
    ):
        self._model = None
        self._model_path = model_path
        self._confidence_threshold = confidence_threshold
        self._provider = "none"
        self._yolo_enabled = enable_yolo

    async def initialize(self) -> None:
        if not CV2_AVAILABLE:
            log.warning("Vision: OpenCV not available, detector disabled")
            return

        if ULTRALYTICS_AVAILABLE and self._yolo_enabled:
            try:
                model_path = self._model_path or "yolov8n.pt"
                self._model = YOLO(model_path)
                self._provider = f"yolov8"
                log.info("Vision: YOLOv8 detector loaded (%s)", model_path)
                return
            except Exception as e:
                log.warning("Vision: YOLOv8 load failed: %s", e)

        self._provider = "opencv_haar"
        log.info("Vision: Using OpenCV Haar cascade fallback")

    async def detect(
        self,
        frame_np: np.ndarray,
        confidence: float | None = None,
    ) -> DetectionResult:
        if not NUMPY_AVAILABLE:
            return DetectionResult(provider=self._provider)

        threshold = confidence or self._confidence_threshold
        height, width = frame_np.shape[:2]
        start = time.time()

        if self._model is not None and ULTRALYTICS_AVAILABLE:
            return await self._detect_yolo(frame_np, threshold, width, height, start)
        else:
            return await self._detect_haar(frame_np, width, height, start)

    async def _detect_yolo(
        self, frame_np: np.ndarray,
        threshold: float, img_w: int, img_h: int,
        start: float,
    ) -> DetectionResult:
        try:
            results = self._model(frame_np, verbose=False)
            elapsed = (time.time() - start) * 1000
            detections: list[Detection] = []

            for r in results:
                boxes = r.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    conf = float(box.conf[0])
                    if conf < threshold:
                        continue
                    cls_id = int(box.cls[0])
                    label = self.CLASS_MAP.get(cls_id, self.COCO_CLASSES[cls_id]) if cls_id < len(
                        self.COCO_CLASSES) else f"class_{cls_id}"
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    norm_bbox = (
                        x1 / img_w, y1 / img_h,
                        (x2 - x1) / img_w, (y2 - y1) / img_h,
                    )
                    detections.append(Detection(
                        label=label, confidence=conf, bbox=norm_bbox,
                    ))

            return DetectionResult(
                detections=detections,
                image_width=img_w, image_height=img_h,
                inference_ms=elapsed, provider=self._provider,
            )

        except Exception as e:
            log.error("Vision: YOLO detection error: %s", e)
            return DetectionResult(
                image_width=img_w, image_height=img_h,
                provider=self._provider,
            )

    async def _detect_haar(
        self, frame_np: np.ndarray,
        img_w: int, img_h: int, start: float,
    ) -> DetectionResult:
        detections: list[Detection] = []

        gray = cv2.cvtColor(frame_np, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        faces = face_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30),
        )

        for x, y, w, h in faces:
            norm_bbox = (x / img_w, y / img_h, w / img_w, h / img_h)
            detections.append(Detection(
                label="face", confidence=0.7, bbox=norm_bbox,
            ))

        elapsed = (time.time() - start) * 1000
        return DetectionResult(
            detections=detections,
            image_width=img_w, image_height=img_h,
            inference_ms=elapsed, provider=self._provider,
        )

    CLASS_MAP: dict[int, str] = {}

    async def close(self) -> None:
        self._model = None
