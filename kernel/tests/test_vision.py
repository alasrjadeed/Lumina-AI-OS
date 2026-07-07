"""Tests for core/vision module — camera, detection, face, description, and API."""

import os
import sys
import time

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from core.vision.camera import CameraInfo, CameraProperty, Frame, list_cameras
from core.vision.detector import Detection, DetectionResult, ObjectDetector
from core.vision.face import Face, FaceDetector, FaceResult
from core.vision.description import SceneDescriber, SceneDescription
from core.vision.memory import Observation, VisualShortTermMemory
from core.vision.cortex import VisualCortex, WatchMode


class TestCameraInfo:
    def test_device_id_default(self):
        info = CameraInfo()
        assert info.device_id == 0
        assert info.available is False

    def test_custom_info(self):
        info = CameraInfo(device_id=1, name="Test Cam", width=1280, height=720, fps=30, available=True)
        assert info.device_id == 1
        assert info.name == "Test Cam"
        assert info.width == 1280
        assert info.height == 720

    def test_to_dict(self):
        info = CameraInfo(device_id=2, available=True)
        d = info.to_dict()
        assert d["device_id"] == 2
        assert d["available"] is True
        assert "name" in d
        assert "backends" in d


class TestFrame:
    def test_frame_creation(self):
        f = Frame(data=b"test", width=320, height=240, format="png")
        assert f.data == b"test"
        assert f.width == 320
        assert f.height == 240
        assert f.format == "png"

    def test_frame_timestamp(self):
        f = Frame(data=b"", width=1, height=1, timestamp=1234567890.0)
        assert f.timestamp == 1234567890.0

    def test_frame_datetime(self):
        import datetime
        f = Frame(data=b"", width=1, height=1, timestamp=0)
        assert f.datetime.year >= 1970

    def test_frame_to_dict(self):
        f = Frame(data=b"abc", width=64, height=64, format="jpeg")
        d = f.to_dict()
        assert d["width"] == 64
        assert d["height"] == 64
        assert d["size_bytes"] == 3
        assert d["format"] == "jpeg"
        assert "timestamp" in d

    def test_frame_metadata(self):
        f = Frame(data=b"", width=1, height=1, metadata={"source": "test"})
        assert f.metadata["source"] == "test"


class TestCameraProperty:
    def test_enum_values(self):
        assert CameraProperty.BRIGHTNESS.value == "brightness"
        assert CameraProperty.CONTRAST.value == "contrast"
        assert CameraProperty.WIDTH.value == "width"
        assert CameraProperty.HEIGHT.value == "height"
        assert CameraProperty.FPS.value == "fps"
        assert CameraProperty.AUTO_FOCUS.value == "auto_focus"

    def test_all_properties_covered(self):
        props = set(CameraProperty)
        expected = {
            "brightness", "contrast", "saturation", "hue",
            "gain", "exposure", "width", "height", "fps",
            "auto_focus", "auto_white_balance",
        }
        assert {p.value for p in props} == expected


class TestListCameras:
    def test_list_cameras_no_cv(self):
        cameras = list_cameras(max_devices=3)
        assert isinstance(cameras, list)
        assert all(isinstance(c, CameraInfo) for c in cameras)


class TestDetection:
    def test_detection_creation(self):
        d = Detection(label="person", confidence=0.95, bbox=(0.1, 0.2, 0.5, 0.6))
        assert d.label == "person"
        assert d.confidence == 0.95
        assert d.x == 0.1
        assert d.y == 0.2

    def test_detection_center(self):
        d = Detection(label="car", confidence=0.8, bbox=(0.2, 0.3, 0.4, 0.2))
        assert abs(d.center_x - 0.4) < 0.01
        assert abs(d.center_y - 0.4) < 0.01

    def test_detection_area(self):
        d = Detection(label="dog", confidence=0.5, bbox=(0, 0, 0.5, 0.5))
        assert abs(d.area - 0.25) < 0.01

    def test_detection_to_dict(self):
        d = Detection(label="cat", confidence=0.9, bbox=(0.1, 0.1, 0.3, 0.3))
        dd = d.to_dict()
        assert dd["label"] == "cat"
        assert dd["confidence"] == 0.9
        assert len(dd["bbox"]) == 4

    def test_edge_case_zero_bbox(self):
        d = Detection(label="unknown", confidence=0.0, bbox=(0, 0, 0, 0))
        assert d.area == 0
        assert d.center_x == 0
        assert d.center_y == 0


class TestDetectionResult:
    def test_empty_result(self):
        r = DetectionResult()
        assert r.count == 0
        assert r.labels == []
        assert r.summary() == "No objects detected."

    def test_with_detections(self):
        r = DetectionResult(
            detections=[
                Detection(label="person", confidence=0.9, bbox=(0, 0, 0.1, 0.2)),
                Detection(label="person", confidence=0.8, bbox=(0.5, 0.5, 0.1, 0.1)),
                Detection(label="car", confidence=0.7, bbox=(0.2, 0.3, 0.3, 0.2)),
            ],
            image_width=640, image_height=480,
            inference_ms=45.0, provider="yolov8",
        )
        assert r.count == 3
        assert "person" in r.labels
        assert "car" in r.labels
        assert "2 persons" in r.summary() or "2 people" in r.summary() or "person" in r.summary()

    def test_to_dict(self):
        r = DetectionResult(detections=[Detection(label="face", confidence=0.7, bbox=(0, 0, 0.5, 0.5))])
        d = r.to_dict()
        assert d["count"] == 1
        assert "detections" in d
        assert "inference_ms" in d

    def test_provider(self):
        r = DetectionResult(provider="opencv_haar")
        assert r.provider == "opencv_haar"


class TestFace:
    def test_face_creation(self):
        f = Face(bbox=(0.1, 0.2, 0.3, 0.4), confidence=0.95)
        assert f.bbox == (0.1, 0.2, 0.3, 0.4)
        assert f.confidence == 0.95

    def test_face_with_name(self):
        f = Face(bbox=(0, 0, 0.1, 0.1), name="Alice", confidence=0.99)
        assert f.name == "Alice"

    def test_face_to_dict(self):
        f = Face(bbox=(0, 0, 0.5, 0.5), confidence=0.8, name="Bob")
        d = f.to_dict()
        assert d["name"] == "Bob"
        assert d["confidence"] == 0.8
        assert len(d["bbox"]) == 4

    def test_face_emotion(self):
        f = Face(bbox=(0, 0, 0.1, 0.1), emotion="happy")
        assert f.emotion == "happy"

    def test_face_gender_age(self):
        f = Face(bbox=(0, 0, 0.1, 0.1), gender="male", age=30)
        assert f.gender == "male"
        assert f.age == 30


class TestFaceResult:
    def test_empty(self):
        r = FaceResult()
        assert r.count == 0
        assert r.summary() == "No faces detected."

    def test_with_faces(self):
        r = FaceResult(faces=[Face(bbox=(0, 0, 0.1, 0.1)), Face(bbox=(0.5, 0.5, 0.2, 0.2))])
        assert r.count == 2
        assert "2" in r.summary()

    def test_with_named_faces(self):
        r = FaceResult(faces=[Face(bbox=(0, 0, 0.1, 0.1), name="Alice")])
        assert "Alice" in r.summary()

    def test_to_dict(self):
        r = FaceResult(faces=[Face(bbox=(0, 0, 0.1, 0.1))], image_width=640, image_height=480)
        d = r.to_dict()
        assert d["count"] == 1
        assert "inference_ms" in d
        assert d["image_size"] == {"width": 640, "height": 480}


class TestFaceDetector:
    def test_init(self):
        fd = FaceDetector()
        assert fd._backend in ("opencv", "face_recognition")

    def test_add_known_face(self):
        fd = FaceDetector()
        fd.add_known_face("Alice", [0.1, 0.2, 0.3])
        assert "Alice" in fd._known_faces

    def test_remove_known_face(self):
        fd = FaceDetector()
        fd.add_known_face("Bob", [0.1, 0.2])
        assert fd.remove_known_face("Bob") is True
        assert fd.remove_known_face("Nobody") is False

    def test_clear_known_faces(self):
        fd = FaceDetector()
        fd.add_known_face("Alice", [0.1])
        fd.add_known_face("Bob", [0.2])
        fd.clear_known_faces()
        assert len(fd._known_faces) == 0


class TestSceneDescription:
    def test_empty_creation(self):
        sd = SceneDescription(summary="test", objects=[])
        assert sd.summary == "test"
        assert sd.objects == []
        assert sd.people_count == 0

    def test_to_dict(self):
        sd = SceneDescription(
            summary="A sunny room",
            objects=["table", "chair"],
            people_count=2,
            lighting="bright",
            mood="cheerful",
            text_detected=["Hello"],
            inference_ms=150.0,
            provider="llm",
        )
        d = sd.to_dict()
        assert d["summary"] == "A sunny room"
        assert len(d["objects"]) == 2
        assert d["people_count"] == 2
        assert d["lighting"] == "bright"
        assert d["provider"] == "llm"

    def test_scene_describer_no_ai(self):
        sd = SceneDescriber()
        assert sd._provider == "none"

    def test_scene_describer_set_ai(self):
        sd = SceneDescriber()
        mock_engine = object()
        sd.set_ai_engine(mock_engine)
        assert sd._ai_engine is mock_engine
        assert sd._provider == "llm"


class TestObjectDetector:
    def test_init(self):
        od = ObjectDetector()
        assert od._confidence_threshold == 0.25

    def test_custom_confidence(self):
        od = ObjectDetector(confidence_threshold=0.5)
        assert od._confidence_threshold == 0.5

    def test_disable_yolo(self):
        od = ObjectDetector(enable_yolo=False)
        assert od._yolo_enabled is False

    def test_close(self):
        od = ObjectDetector()
        import asyncio
        asyncio.run(od.close())
        assert od._model is None

    def test_coco_classes_length(self):
        assert len(ObjectDetector.COCO_CLASSES) == 80
        assert "person" in ObjectDetector.COCO_CLASSES
        assert "cell phone" in ObjectDetector.COCO_CLASSES
        assert "toothbrush" in ObjectDetector.COCO_CLASSES


class TestAPIEndpoints:
    @pytest.mark.asyncio
    async def test_vision_status(self):
        from api.vision import router
        assert router.prefix == "/vision"
        assert len(router.routes) > 0

    def test_routes_exist(self):
        from api.vision import router
        paths = [r.path for r in router.routes]
        assert "/vision/cameras" in paths
        assert "/vision/capture" in paths
        assert "/vision/detect" in paths
        assert "/vision/describe" in paths
        assert "/vision/face/detect" in paths
        assert "/vision/stream/mjpeg" in paths
        assert "/vision/stream/info" in paths
        assert "/vision/stream/ws" in paths
        assert "/vision/watch/start" in paths
        assert "/vision/status" in paths
        assert "/vision/reload" in paths
        assert "/vision/ui" in paths

    @pytest.mark.asyncio
    async def test_cameras_endpoint_response(self):
        from fastapi.testclient import TestClient
        from api.vision import router
        from fastapi import FastAPI

        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)

        resp = client.get("/vision/cameras")
        assert resp.status_code == 200
        data = resp.json()
        assert "cameras" in data
        assert len(data["cameras"]) > 0
        assert "device_id" in data["cameras"][0]


class TestConfigSettings:
    def test_vision_settings_defaults(self):
        from config.settings import settings
        assert hasattr(settings, "vision_camera_id")
        assert settings.vision_camera_id == 0
        assert settings.vision_camera_width == 640
        assert settings.vision_camera_height == 480
        assert settings.vision_detection_confidence == 0.25


class TestMainIntegration:
    def test_vision_router_registered(self):
        import main as main_module
        assert hasattr(main_module, "vision_router")
        assert main_module.vision_router.prefix == "/vision"

    def test_vision_imports_exist(self):
        import main as main_module
        assert hasattr(main_module, "CameraDevice")
        assert hasattr(main_module, "ObjectDetector")
        assert hasattr(main_module, "SceneDescriber")
        assert hasattr(main_module, "VideoStream")

    def test_vision_router_prefix(self):
        from api.vision import router
        assert router.prefix == "/vision"

    def test_vision_routes_count(self):
        from api.vision import router
        assert len(router.routes) >= 15


class TestAssistantIntegration:
    def test_vision_in_capabilities(self):
        from core.assistant.agent import CAPABILITIES
        assert "vision" in CAPABILITIES
        assert "camera" in CAPABILITIES["vision"]

    def test_vision_in_routing_prompt(self):
        from core.assistant.agent import CAPABILITIES
        assert "vision" in CAPABILITIES


class TestVoiceIntegration:
    def test_vision_in_intent_categories(self):
        from core.voice.controller import VoiceController
        vc = VoiceController()
        assert hasattr(vc, "_understand_intent")


class TestVisualShortTermMemory:
    def test_empty_memory(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        assert mem.size == 0
        assert mem.current is None
        assert mem.summary() == "I haven't seen anything yet."

    def test_push_observation(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        obs = Observation(timestamp=time.time(), summary="a person walking", labels=["person"])
        mem.push(obs)
        assert mem.size == 1
        assert mem.current is not None
        assert mem.current.summary == "a person walking"

    def test_get_recent(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), summary="obs1"))
        mem.push(Observation(timestamp=time.time() - 120, summary="obs2"))
        recent = mem.get_recent(seconds=60)
        assert len(recent) == 1
        assert recent[0].summary == "obs1"

    def test_has_seen(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), labels=["person", "car"]))
        assert mem.has_seen("person", within_seconds=30) is True
        assert mem.has_seen("dog", within_seconds=30) is False

    def test_clear(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), summary="test"))
        mem.clear()
        assert mem.size == 0
        assert mem.current is None

    def test_capacity_limit(self):
        mem = VisualShortTermMemory(capacity=3, ttl_seconds=999)
        for i in range(5):
            mem.push(Observation(timestamp=time.time() + i, summary=f"obs{i}"))
        assert mem.size <= 3

    def test_change_detected_new_labels(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), labels=["chair", "table"]))
        result = mem.change_detected(Observation(timestamp=time.time(), labels=["chair", "table", "person"]))
        assert result is not None
        assert "person" in result

    def test_change_detected_disappeared(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), labels=["person", "chair"]))
        result = mem.change_detected(Observation(timestamp=time.time(), labels=["chair"]))
        assert result is not None
        assert "gone" in result or "person" in result

    def test_change_detected_no_change(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        mem.push(Observation(timestamp=time.time(), labels=["chair"]))
        result = mem.change_detected(Observation(timestamp=time.time(), labels=["chair"]))
        assert result is None

    def test_change_detected_needs_two_observations(self):
        mem = VisualShortTermMemory(capacity=10, ttl_seconds=60)
        assert mem.change_detected(Observation(timestamp=time.time(), labels=["person"])) is None

    def test_observation_age(self):
        obs = Observation(timestamp=time.time() - 10, summary="old")
        assert abs(obs.age_seconds - 10) < 1

    def test_observation_to_dict(self):
        obs = Observation(
            timestamp=1234567890, summary="test scene",
            labels=["person", "car"], people_count=1,
        )
        d = obs.to_dict()
        assert d["summary"] == "test scene"
        assert d["labels"] == ["person", "car"]
        assert d["people_count"] == 1


class TestVisualCortex:
    def test_init(self):
        cortex = VisualCortex(enable_faces=False, enable_description=False)
        assert cortex.mode == WatchMode.IDLE
        assert cortex.is_watching is False
        assert cortex.watch_interval == 3.0

    def test_set_watch_interval(self):
        cortex = VisualCortex()
        cortex.set_watch_interval(5.0)
        assert cortex.watch_interval == 5.0

    def test_set_watch_interval_clamps(self):
        cortex = VisualCortex()
        cortex.set_watch_interval(0.1)
        assert cortex.watch_interval >= 1.0
        cortex.set_watch_interval(100.0)
        assert cortex.watch_interval <= 60.0

    def test_proactive_narration(self):
        cortex = VisualCortex()
        assert cortex._proactive_narration is False
        cortex.set_proactive_narration(True)
        assert cortex._proactive_narration is True

    def test_callbacks(self):
        cortex = VisualCortex()
        called = []

        def on_change(msg):
            called.append(msg)

        def on_obs(obs):
            called.append("obs")

        cortex.on_change(on_change)
        cortex.on_observation(on_obs)
        assert len(cortex._on_change_callbacks) == 1
        assert len(cortex._on_observation_callbacks) == 1

    def test_status(self):
        import asyncio
        cortex = VisualCortex(enable_faces=False, enable_description=False)
        status = asyncio.run(cortex.get_status())
        assert status["mode"] == "idle"
        assert status["watching"] is False
        assert status["memory_size"] == 0

    def test_summarize_no_observation(self):
        cortex = VisualCortex()
        assert cortex.memory.summary() == "I haven't seen anything yet."


class TestCortexAPIEndpoints:
    def test_cortex_routes_exist(self):
        from api.vision import router
        paths = [r.path for r in router.routes]
        assert "/vision/think" in paths
        assert "/vision/watch" in paths
        assert "/vision/watch/stop" in paths
        assert "/vision/what-do-you-see" in paths
        assert "/vision/look-for" in paths
        assert "/vision/scene/memory" in paths


class TestWatchMode:
    def test_enum_values(self):
        assert WatchMode.IDLE.value == "idle"
        assert WatchMode.WATCHING.value == "watching"
        assert WatchMode.DESCRIBING.value == "describing"
        assert WatchMode.ALERT.value == "alert"

    def test_enum_all_covered(self):
        modes = {m.value for m in WatchMode}
        assert modes == {"idle", "watching", "describing", "alert"}


class TestMainCortexIntegration:
    def test_visual_cortex_imported(self):
        import main as main_module
        assert hasattr(main_module, "VisualCortex")

    def test_visual_cortex_constructable(self):
        from core.vision.cortex import VisualCortex
        vc = VisualCortex(enable_detection=False, enable_faces=False, enable_description=False)
        assert vc is not None
        assert vc.mode == WatchMode.IDLE


class TestEdgeCases:
    def test_detection_negative_bbox(self):
        d = Detection(label="test", confidence=0.5, bbox=(-1, -1, 2, 2))
        assert d.x == -1
        assert d.y == -1

    def test_frame_empty_data(self):
        f = Frame(data=b"", width=0, height=0)
        assert len(f.data) == 0

    def test_detection_result_no_provider(self):
        r = DetectionResult()
        assert r.provider == ""

    def test_face_no_bbox(self):
        with pytest.raises(TypeError):
            Face()
