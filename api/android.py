import os
import shlex
import subprocess
import tempfile

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from core.android.device import android
from core.android.keyboard import LuminaADBKeyboard
from core.log import log

keyboard = LuminaADBKeyboard()

router = APIRouter(prefix="/android", tags=["Android"])


class ShellRequest(BaseModel):
    command: str


class InstallRequest(BaseModel):
    apk_path: str


class TapRequest(BaseModel):
    x: int
    y: int


class TextRequest(BaseModel):
    text: str


@router.get("/devices")
async def list_devices():
    return {"devices": android.detect_devices()}


@router.post("/connect")
async def connect(serial: str = ""):
    android.connect(serial if serial else None)
    return {"status": "connected", "device": android._serial}


@router.get("/info")
async def device_info():
    if not android.is_connected:
        android.connect()
    return android.get_device_info()


@router.post("/shell")
async def shell(req: ShellRequest):
    if not android.is_connected:
        android.connect()
    output = android.shell(req.command)
    return {"output": output}


@router.post("/install")
async def install_apk(req: InstallRequest):
    if not android.is_connected:
        android.connect()
    return android.install_apk(req.apk_path)


@router.post("/tap")
async def tap(req: TapRequest):
    if not android.is_connected:
        android.connect()
    android.input_tap(req.x, req.y)
    return {"status": "ok"}


@router.post("/text")
async def input_text(req: TextRequest):
    if not android.is_connected:
        android.connect()
    android.input_text(req.text)
    return {"status": "ok"}


@router.post("/screenshot")
async def screenshot():
    if not android.is_connected:
        android.connect()
    path = android.screenshot()
    return {"status": "ok", "path": path}


@router.get("/screenshot")
async def screenshot_get():
    """Take screenshot and return as PNG image (for <img> tags)."""
    if not android.is_connected:
        android.connect()
    if not android.is_connected:
        return JSONResponse({"error": "No device connected"}, status_code=400)
    path = android.screenshot()
    local = "/tmp/lumina_screen.png"
    android.pull(path, local)
    return FileResponse(local, media_type="image/png")


@router.get("/logcat")
async def logcat(lines: int = 50):
    if not android.is_connected:
        android.connect()
    return {"log": android.get_logcat(lines)}


@router.get("/packages")
async def list_packages(filter: str = ""):
    if not android.is_connected:
        android.connect()
    return {"packages": android.list_packages(filter)}


@router.post("/local/exec")
async def local_exec(command: str = "scrcpy"):
    """Run a command on the LOCAL machine (not via ADB)."""
    try:
        proc = subprocess.Popen(
            shlex.split(command), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return {"status": "started", "pid": proc.pid, "command": command}
    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/install/apk")
async def install_apk_upload(apk: UploadFile):
    """Upload and install an APK file via ADB."""
    if not android.is_connected:
        android.connect()
    if not android.is_connected:
        return {"success": False, "error": "No device connected"}
    path = os.path.join(tempfile.gettempdir(), apk.filename or "app.apk")
    content = await apk.read()
    with open(path, "wb") as f:
        f.write(content)
    result = android.install_apk(path)
    os.remove(path)
    if result["success"]:
        log.info("APK installed: %s", apk.filename)
    return result


# ── Lumina ADB Keyboard ──


class KeyPressRequest(BaseModel):
    key: str


class TypeTextRequest(BaseModel):
    text: str
    method: str = "adb_text"


@router.get("/keyboard/status")
async def keyboard_status():
    return {
        "connected": android.is_connected,
        "serial": android._serial,
    }


@router.get("/keyboard/keys")
async def list_keys():
    return {
        "keys": [
            {"name": "Home", "key": "home", "category": "nav"},
            {"name": "Back", "key": "back", "category": "nav"},
            {"name": "Menu", "key": "menu", "category": "nav"},
            {"name": "Search", "key": "search", "category": "nav"},
            {"name": "Enter", "key": "enter", "category": "input"},
            {"name": "Tab", "key": "tab", "category": "input"},
            {"name": "Space", "key": "space", "category": "input"},
            {"name": "Delete", "key": "del", "category": "input"},
            {"name": "Clear", "key": "clear", "category": "input"},
            {"name": "Power", "key": "power", "category": "system"},
            {"name": "Volume Up", "key": "volume_up", "category": "system"},
            {"name": "Volume Down", "key": "volume_down", "category": "system"},
            {"name": "Mute", "key": "mute", "category": "system"},
            {"name": "Up", "key": "up", "category": "dpad"},
            {"name": "Down", "key": "down", "category": "dpad"},
            {"name": "Left", "key": "left", "category": "dpad"},
            {"name": "Right", "key": "right", "category": "dpad"},
            {"name": "OK", "key": "ok", "category": "dpad"},
            {"name": "Play/Pause", "key": "play", "category": "media"},
            {"name": "Stop", "key": "stop", "category": "media"},
            {"name": "Next", "key": "next", "category": "media"},
            {"name": "Previous", "key": "prev", "category": "media"},
        ]
    }


@router.post("/keyboard/press")
async def press_key(req: KeyPressRequest):
    result = keyboard.press_key(req.key)
    return {"success": result.success, "message": result.message, "error": result.error}


@router.post("/keyboard/type")
async def type_text(req: TypeTextRequest):
    if req.method == "keyevent":
        result = keyboard.type_key_by_key(req.text)
    else:
        result = keyboard.type_text(req.text)
    return {"success": result.success, "message": result.message, "error": result.error}


@router.post("/keyboard/clear")
async def clear_text():
    result = keyboard.clear_text()
    return {"success": result.success, "message": result.message}


@router.get("/keyboard/ime")
async def list_ime():
    return {"imes": keyboard.get_ime_list()}


@router.post("/keyboard/ime")
async def set_ime(ime_id: str):
    result = keyboard.set_ime(ime_id)
    return {"success": result.success, "message": result.message}
