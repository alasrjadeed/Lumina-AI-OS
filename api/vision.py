"""Vision API — camera capture, object detection, face recognition, scene description, and video streaming."""

import asyncio
import json
import time

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, Response, StreamingResponse
from pydantic import BaseModel

from core.log import log
from core.vision import (
    CameraDevice,
    CameraError,
    DetectionResult,
    FaceDetector,
    FaceResult,
    ObjectDetector,
    SceneDescriber,
    SceneDescription,
    VideoStream,
    list_cameras,
)
from core.provider import engine as ai_engine

router = APIRouter(prefix="/vision", tags=["Vision"])


camera_instance: CameraDevice | None = None
detector_instance: ObjectDetector | None = None
face_detector_instance: FaceDetector | None = None
describer_instance: SceneDescriber | None = None
stream_instance: VideoStream | None = None


def _get_camera() -> CameraDevice:
    global camera_instance
    if camera_instance is None:
        camera_instance = CameraDevice(device_id=0)
    return camera_instance


def _get_detector() -> ObjectDetector:
    global detector_instance
    if detector_instance is None:
        detector_instance = ObjectDetector()
    return detector_instance


def _get_face_detector() -> FaceDetector:
    global face_detector_instance
    if face_detector_instance is None:
        face_detector_instance = FaceDetector()
    return face_detector_instance


def _get_describer() -> SceneDescriber:
    global describer_instance
    if describer_instance is None:
        describer_instance = SceneDescriber(ai_engine=ai_engine)
    return describer_instance


def _get_stream() -> VideoStream:
    global stream_instance
    if stream_instance is None:
        camera = _get_camera()
        stream_instance = VideoStream(camera=camera, fps=15)
    return stream_instance


class CaptureResponse(BaseModel):
    width: int = 0
    height: int = 0
    format: str = ""
    size_bytes: int = 0
    timestamp: float = 0.0


@router.get("/cameras")
async def list_available_cameras():
    """List all available camera devices."""
    cameras = list_cameras()
    return {"cameras": [c.to_dict() for c in cameras]}


@router.post("/capture")
async def capture_image(
    width: int = Query(640, ge=64, le=4096),
    height: int = Query(480, ge=64, le=4096),
    format: str = Query("jpeg", pattern="^(jpeg|png|webp)$"),
):
    """Capture a single image from the camera."""
    camera = _get_camera()
    camera.set_resolution(width, height)
    frame = await camera.capture_frame(format=format)
    if frame is None:
        raise HTTPException(500, "Failed to capture frame from camera")

    return Response(
        content=frame.data,
        media_type=f"image/{frame.format}",
        headers={
            "X-Frame-Width": str(frame.width),
            "X-Frame-Height": str(frame.height),
            "X-Timestamp": str(frame.timestamp),
            "Content-Disposition": f"inline; filename=capture_{int(time.time())}.{frame.format}",
        },
    )


@router.post("/capture/json")
async def capture_json():
    """Capture an image and return metadata as JSON (without the image data)."""
    camera = _get_camera()
    frame = await camera.capture_frame()
    if frame is None:
        raise HTTPException(500, "Failed to capture frame")
    return frame.to_dict()


class DetectResponse(BaseModel):
    detections: list[dict]
    count: int
    labels: list[str]
    inference_ms: float
    provider: str


@router.post("/detect")
async def detect_objects(
    confidence: float = Query(0.25, ge=0.0, le=1.0),
):
    """Capture a frame and detect objects."""
    camera = _get_camera()
    detector = _get_detector()

    frame_np = await camera.capture_numpy()
    if frame_np is None:
        raise HTTPException(500, "Failed to capture frame")

    result = await detector.detect(frame_np, confidence=confidence)
    return result.to_dict()


@router.post("/detect/upload")
async def detect_objects_upload(
    file: UploadFile = File(...),
    confidence: float = Query(0.25, ge=0.0, le=1.0),
):
    """Upload an image and detect objects."""
    import numpy as np
    import cv2

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame_np is None:
        raise HTTPException(400, "Invalid image file")

    detector = _get_detector()
    result = await detector.detect(frame_np, confidence=confidence)
    return result.to_dict()


class FaceResponse(BaseModel):
    faces: list[dict]
    count: int
    inference_ms: float


@router.post("/face/detect")
async def detect_faces():
    """Capture a frame and detect faces."""
    camera = _get_camera()
    detector = _get_face_detector()

    frame_np = await camera.capture_numpy()
    if frame_np is None:
        raise HTTPException(500, "Failed to capture frame")

    result = await detector.detect(frame_np)
    return result.to_dict()


@router.post("/face/detect/upload")
async def detect_faces_upload(file: UploadFile = File(...)):
    """Upload an image and detect faces."""
    import numpy as np
    import cv2

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame_np is None:
        raise HTTPException(400, "Invalid image file")

    detector = _get_face_detector()
    result = await detector.detect(frame_np)
    return result.to_dict()


class DescribeResponse(BaseModel):
    summary: str
    inference_ms: float
    provider: str


@router.post("/describe")
async def describe_scene(
    detail: str = Query("normal", pattern="^(brief|normal|high)$"),
    context: str = Query(None, max_length=500),
):
    """Capture a frame and describe the scene using AI."""
    camera = _get_camera()
    describer = _get_describer()

    frame_np = await camera.capture_numpy()
    if frame_np is None:
        raise HTTPException(500, "Failed to capture frame")

    result = await describer.describe(frame_np, detail=detail, context=context)
    return result.to_dict()


@router.post("/describe/upload")
async def describe_scene_upload(
    file: UploadFile = File(...),
    detail: str = Query("normal", pattern="^(brief|normal|high)$"),
    context: str = Query(None, max_length=500),
):
    """Upload an image and describe the scene using AI."""
    import numpy as np
    import cv2

    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame_np is None:
        raise HTTPException(400, "Invalid image file")

    describer = _get_describer()
    result = await describer.describe(frame_np, detail=detail, context=context)
    return result.to_dict()


@router.get("/stream/mjpeg")
async def stream_mjpeg():
    """MJPEG video stream from the camera."""
    camera = _get_camera()
    stream = VideoStream(camera=camera, fps=15, format="jpeg", quality=70)

    await stream.start()

    async def generate():
        try:
            async for chunk in stream.stream_mjpeg(boundary="frame"):
                yield chunk
        except Exception as e:
            log.error("Vision: MJPEG stream error: %s", e)
        finally:
            await stream.stop()

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


@router.get("/stream/info")
async def stream_info():
    """Get current stream status."""
    stream = _get_stream()
    return {
        "running": stream.is_running,
        "fps": stream.fps,
        "frame_count": stream.frame_count,
    }


@router.websocket("/stream/ws")
async def websocket_stream(websocket: WebSocket):
    """WebSocket video stream — sends JPEG frames as binary messages."""
    await websocket.accept()

    camera = _get_camera()
    stream = VideoStream(camera=camera, fps=10, format="jpeg", quality=60)

    try:
        await stream.start()
        async for frame in stream.stream_frames():
            try:
                metadata = json.dumps(frame.to_dict()).encode()
                await websocket.send_bytes(len(metadata).to_bytes(4, "big") + metadata + frame.data)
            except WebSocketDisconnect:
                break
    except Exception as e:
        log.error("Vision: WebSocket stream error: %s", e)
    finally:
        await stream.stop()
        try:
            await websocket.close()
        except Exception:
            pass


@router.post("/watch/start")
async def start_watching(
    interval: float = Query(5.0, ge=1.0, le=300.0),
    detect_objects_: bool = Query(True, alias="detect_objects"),
    detect_faces_: bool = Query(False, alias="detect_faces"),
    describe_scene_: bool = Query(True, alias="describe_scene"),
):
    """Start continuous monitoring — captures frames at interval and runs detection/description."""
    from core.vision import VideoStream

    camera = _get_camera()
    detector = _get_detector() if detect_objects_ else None
    face_det = _get_face_detector() if detect_faces_ else None
    describer = _get_describer() if describe_scene_ else None

    frame_np = await camera.capture_numpy()
    if frame_np is None:
        raise HTTPException(500, "Failed to capture frame")

    results: dict = {}

    if detector:
        results["detection"] = (await detector.detect(frame_np)).to_dict()

    if face_det:
        results["faces"] = (await face_det.detect(frame_np)).to_dict()

    if describer:
        results["description"] = (await describer.describe(frame_np)).to_dict()

    results["camera"] = camera.info.to_dict()
    return results


@router.post("/reload")
async def reload_camera():
    """Reload/reinitialize the camera device."""
    global camera_instance, detector_instance, stream_instance

    if camera_instance:
        camera_instance.close()
    if stream_instance:
        await stream_instance.stop()

    camera_instance = CameraDevice(device_id=0)
    detector_instance = None
    stream_instance = None

    opened = camera_instance.open()
    if not opened:
        raise HTTPException(500, "Failed to reopen camera")

    return {"status": "ok", "camera": camera_instance.info.to_dict()}


_cortex_instance: "VisualCortex | None" = None


def _get_cortex():
    global _cortex_instance
    if _cortex_instance is None:
        from core.vision.cortex import VisualCortex
        _cortex_instance = VisualCortex(
            camera=CameraDevice(device_id=0),
            ai_engine=ai_engine,
            enable_faces=True,
            enable_description=True,
        )
    return _cortex_instance


@router.post("/think")
async def think_about_scene(
    question: str = Query("", max_length=500),
    detail: str = Query("normal", pattern="^(brief|normal|high)$"),
):
    """Capture, think about the scene, and return a description. Optionally answer a question."""
    cortex = _get_cortex()
    if not cortex.is_watching:
        await cortex.start_watching()

    if question:
        text = await cortex.ask_about_scene(question)
    else:
        text = await cortex.capture_and_describe(detail=detail)

    return {
        "thought": text,
        "mode": "qa" if question else "describe",
        "cortex": await cortex.get_status(),
    }


@router.post("/watch")
async def start_cortex_watch(
    interval: float = Query(3.0, ge=1.0, le=60.0),
    proactive: bool = Query(False),
):
    """Start the VisualCortex continuous watch loop."""
    cortex = _get_cortex()
    cortex.set_watch_interval(interval)
    cortex.set_proactive_narration(proactive)

    if not cortex.is_watching:
        await cortex.start_watching()

    return {
        "status": "watching",
        "interval": interval,
        "proactive_narration": proactive,
        "cortex": await cortex.get_status(),
    }


@router.post("/watch/stop")
async def stop_cortex_watch():
    """Stop the VisualCortex watch loop."""
    cortex = _get_cortex()
    await cortex.stop_watching()
    return {"status": "stopped"}


@router.post("/what-do-you-see")
async def what_do_you_see():
    """Ask the AI what it currently sees (uses VisualCortex)."""
    cortex = _get_cortex()
    if not cortex.is_watching:
        await cortex.start_watching()
    text = await cortex.what_do_you_see()
    return {
        "response": text,
        "mode": "what_do_you_see",
    }


@router.post("/look-for")
async def look_for_object(
    target: str = Query(..., min_length=1, max_length=100),
    timeout: float = Query(15.0, ge=5.0, le=120.0),
):
    """Actively search for a specific object/person."""
    cortex = _get_cortex()
    text = await cortex.look_for(target, timeout=timeout)
    return {"response": text, "target": target, "timeout": timeout}


@router.post("/scene/memory")
async def scene_memory():
    """Get the VisualCortex's short-term visual memory."""
    cortex = _get_cortex()
    return {
        "summary": cortex.memory.summary(max_observations=10),
        "observations": [o.to_dict() for o in cortex.memory.get_all()[-10:]],
        "current": cortex.memory.current.to_dict() if cortex.memory.current else None,
    }


@router.get("/status")
async def vision_status():
    """Get the overall vision module status."""
    camera = _get_camera()
    cortex_status = {}
    if _cortex_instance is not None:
        cortex_status = await _cortex_instance.get_status()
    return {
        "camera": {
            "available": camera.info.available,
            "info": camera.info.to_dict(),
        },
        "detector": {
            "ready": detector_instance is not None,
        },
        "face_detector": {
            "ready": face_detector_instance is not None,
        },
        "describer": {
            "ready": describer_instance is not None,
        },
        "stream": {
            "running": stream_instance.is_running if stream_instance else False,
        },
        "cortex": cortex_status,
    }


@router.get("/ui", response_class=HTMLResponse)
async def vision_ui():
    """Simple browser-based camera viewer UI."""
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Lumina Vision</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                background: #0f0f13; color: #e0e0e0;
                display: flex; flex-direction: column; align-items: center;
                min-height: 100vh; padding: 20px;
            }
            h1 { margin: 20px 0; font-size: 1.5rem; color: #8b8bfa; }
            #viewfinder {
                width: 100%; max-width: 800px; border-radius: 12px;
                overflow: hidden; box-shadow: 0 0 30px rgba(139,139,250,0.15);
            }
            #viewfinder img {
                width: 100%; display: block;
                image-rendering: auto;
            }
            .controls {
                display: flex; gap: 12px; margin: 20px 0; flex-wrap: wrap;
                justify-content: center;
            }
            button {
                padding: 10px 24px; border: none; border-radius: 8px;
                background: #2a2a3e; color: #e0e0e0; cursor: pointer;
                font-size: 0.9rem; transition: all 0.2s;
            }
            button:hover { background: #3a3a5e; transform: translateY(-1px); }
            button.primary { background: #6c6cf0; }
            button.primary:hover { background: #8b8bfa; }
            button.danger { background: #e04444; }
            button.danger:hover { background: #ff5555; }
            #info {
                width: 100%; max-width: 800px; margin-top: 12px;
                padding: 16px; background: #1a1a2e; border-radius: 8px;
                font-family: monospace; font-size: 0.85rem; line-height: 1.6;
                white-space: pre-wrap; min-height: 60px;
            }
            .badge {
                display: inline-block; padding: 2px 8px; border-radius: 4px;
                font-size: 0.75rem; margin: 2px;
            }
            .badge.object { background: #2d4a2d; color: #8f8; }
            .badge.face { background: #4a3d2d; color: #ff8; }
        </style>
    </head>
    <body>
        <h1>Lumina Vision</h1>
        <div id="viewfinder">
            <img id="live" src="/vision/stream/mjpeg" alt="Camera feed">
        </div>
        <div class="controls">
            <button class="primary" onclick="capture()">Capture</button>
            <button onclick="detect()">Detect Objects</button>
            <button onclick="detectFaces()">Find Faces</button>
            <button onclick="describe()">Describe Scene</button>
            <button onclick="watch()">Watch</button>
            <button onclick="stopWatch()">Stop Watch</button>
            <button onclick="ask()">What Do You See?</button>
            <button onclick="memory()">Memory</button>
        </div>
        <div id="status-bar" style="margin-bottom:8px;font-size:0.8rem;color:#888;text-align:center"></div>
        <div id="info">Ready. Click a button to analyze the camera feed.</div>
        <script>
            async function api(path, opts={}) {
                try {
                    const r = await fetch(path, { method: 'POST', ...opts });
                    const data = await r.json();
                    document.getElementById('info').textContent = JSON.stringify(data, null, 2);
                    return data;
                } catch(e) {
                    document.getElementById('info').textContent = 'Error: ' + e.message;
                }
            }
            function capture() { api('/vision/capture/json'); }
            function detect() { api('/vision/detect'); }
            function detectFaces() { api('/vision/face/detect'); }
            function describe() { api('/vision/describe?detail=normal'); }
            async function watch() {
                const r = await api('/vision/watch?interval=3&proactive=true');
                if (r && r.status === 'watching') document.getElementById('status-bar').textContent = 'Watching...';
            }
            async function stopWatch() {
                const r = await api('/vision/watch/stop');
                if (r && r.status === 'stopped') document.getElementById('status-bar').textContent = '';
            }
            function ask() { api('/vision/what-do-you-see'); }
            function memory() { api('/vision/scene/memory'); }
        </script>
    </body>
    </html>
    """)
