"""Desktop Control API — app/window management, file ops, clipboard, system stats, and AI agent."""

import asyncio
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.desktop.app_manager import AppManager
from core.desktop.clipboard import ClipboardManager
from core.desktop.notifications import NotificationManager
from core.desktop.os_automation import desktop
from core.desktop.window_manager import WindowManager
from core.log import log

router = APIRouter(prefix="/desktop", tags=["Desktop"])

app_manager = AppManager()
window_manager = WindowManager()
clipboard_manager = ClipboardManager()
notification_manager = NotificationManager()


# ── Models ──

class CommandRequest(BaseModel):
    command: str

class WriteFileRequest(BaseModel):
    path: str
    content: str

class CopyMoveRequest(BaseModel):
    src: str
    dst: str

class LaunchAppRequest(BaseModel):
    name: str
    path: str = ""
    args: list[str] = []

class AgentTaskRequest(BaseModel):
    task: str
    timeout: int = 60

class CompressRequest(BaseModel):
    source: str
    destination: str = ""
    format: str = "zip"

class ExtractRequest(BaseModel):
    archive: str
    destination: str = ""

class SearchRequest(BaseModel):
    pattern: str
    path: str = "."


# ── System Info ──

@router.get("/info")
async def system_info():
    return await desktop.system_info()


@router.get("/stats")
async def system_stats():
    disk = shutil.disk_usage("/")
    return {
        "platform": platform.system(),
        "release": platform.release(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "cpu_count": os.cpu_count(),
        "disk_total": disk.total,
        "disk_used": disk.used,
        "disk_free": disk.free,
        "disk_percent": round(disk.used / disk.total * 100, 1),
        "cwd": os.getcwd(),
    }


@router.get("/processes")
async def list_processes(limit: int = 30):
    try:
        result = subprocess.run(
            ["ps", "aux", "--sort=-%mem"],
            capture_output=True, text=True, timeout=5,
        )
        lines = result.stdout.strip().split("\n")
        headers = lines[0].split()
        processes = []
        for line in lines[1:limit + 1]:
            parts = line.split(None, len(headers) - 1)
            if len(parts) >= len(headers):
                processes.append({
                    "user": parts[0],
                    "pid": int(parts[1]),
                    "cpu": parts[2],
                    "mem": parts[3],
                    "command": parts[-1][:60],
                })
        return {"processes": processes, "count": len(processes)}
    except Exception as e:
        return {"error": str(e), "processes": []}


# ── File Operations ──

@router.get("/files", summary="List directory contents")
async def list_files(path: str = ".", sort_by: str = "name", ascending: bool = True):
    files = await desktop.list_files(path)
    reverse = not ascending
    if sort_by == "size":
        files.sort(key=lambda f: f.get("size", 0), reverse=reverse)
    elif sort_by == "type":
        files.sort(key=lambda f: (f.get("type", ""), f.get("name", "")), reverse=reverse)
    else:
        files.sort(key=lambda f: f.get("name", ""), reverse=reverse)
    return {"files": files, "count": len(files), "path": path}


@router.get("/files/read")
async def read_file(path: str):
    content = await desktop.read_file(path)
    if content is None:
        raise HTTPException(404, "File not found")
    return {"content": content, "path": path}


@router.post("/files/write")
async def write_file(req: WriteFileRequest):
    await desktop.write_file(req.path, req.content)
    return {"status": "ok", "path": req.path}


@router.post("/files/copy")
async def copy_file(req: CopyMoveRequest):
    await desktop.copy_file(req.src, req.dst)
    return {"status": "ok"}


@router.post("/files/move")
async def move_file(req: CopyMoveRequest):
    await desktop.move_file(req.src, req.dst)
    return {"status": "ok"}


@router.post("/files/rename")
async def rename_file(path: str = Query(...), new_name: str = Query(...)):
    src = Path(path).expanduser()
    dst = src.parent / new_name
    await desktop.move_file(str(src), str(dst))
    return {"status": "ok", "src": str(src), "dst": str(dst)}


@router.delete("/files/delete")
async def delete_file(path: str):
    await desktop.delete_file(path)
    return {"status": "ok"}


@router.post("/files/mkdir")
async def create_dir(path: str):
    await desktop.create_dir(path)
    return {"status": "ok", "path": path}


@router.post("/files/search", summary="Search files by glob pattern")
async def search_files(req: SearchRequest):
    p = Path(req.path).expanduser().resolve()
    if not p.exists():
        return {"files": [], "count": 0}
    matches = list(p.rglob(req.pattern))
    files = []
    for m in matches[:200]:
        try:
            stat = m.stat()
            files.append({
                "name": m.name,
                "path": str(m),
                "type": "dir" if m.is_dir() else "file",
                "size": stat.st_size if m.is_file() else 0,
                "modified": stat.st_mtime,
            })
        except OSError:
            pass
    return {"files": files, "count": len(files), "pattern": req.pattern}


@router.post("/files/compress", summary="Compress files/folders into an archive")
async def compress_files(req: CompressRequest):
    src = Path(req.source).expanduser()
    if not src.exists():
        raise HTTPException(404, f"Source not found: {req.source}")
    dst = req.destination or f"{src}.{req.format}"
    dst_path = Path(dst).expanduser()
    try:
        fmt = req.format.lower()
        if fmt == "zip":
            shutil.make_archive(str(dst_path.with_suffix("")), "zip", src.parent, src.name)
        elif fmt == "tar":
            shutil.make_archive(str(dst_path.with_suffix("")), "tar", src.parent, src.name)
        elif fmt == "gztar":
            shutil.make_archive(str(dst_path.with_suffix("")), "gztar", src.parent, src.name)
        else:
            raise HTTPException(400, f"Unsupported format: {fmt}")
        return {"status": "ok", "archive": str(dst_path) if dst_path.suffix else f"{dst}.{fmt}"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/files/extract", summary="Extract an archive")
async def extract_files(req: ExtractRequest):
    archive = Path(req.archive).expanduser()
    if not archive.exists():
        raise HTTPException(404, f"Archive not found: {req.archive}")
    dst = req.destination or archive.parent / archive.stem
    dst_path = Path(dst).expanduser()
    dst_path.mkdir(parents=True, exist_ok=True)
    try:
        shutil.unpack_archive(str(archive), str(dst_path))
        return {"status": "ok", "destination": str(dst_path)}
    except Exception as e:
        raise HTTPException(500, str(e))


# ── Application Management ──

@router.get("/apps", summary="List launched apps")
async def list_apps(running_only: bool = False):
    apps = app_manager.list_apps(running_only=running_only)
    return {
        "apps": [{
            "name": a.name, "path": a.path,
            "pid": a.pid, "running": a.running,
        } for a in apps],
        "count": len(apps),
    }


@router.post("/apps/launch", summary="Launch a desktop application")
async def launch_app(req: LaunchAppRequest):
    success = await app_manager.launch(req.name, req.path, req.args)
    if not success:
        found = shutil.which(req.name)
        if found:
            success = await app_manager.launch(req.name, found, req.args)
    if not success:
        raise HTTPException(400, f"Could not launch '{req.name}'. Is it installed?")
    app = app_manager.get_app(req.name)
    return {
        "status": "ok",
        "app": {"name": req.name, "pid": app.pid if app else 0, "running": True},
    }


@router.post("/apps/launch/terminal", summary="Open a terminal window")
async def launch_terminal(command: str = ""):
    shell = os.environ.get("SHELL", "bash")
    if command:
        args = ["-c", command]
    else:
        args = []
    term = shutil.which("gnome-terminal") or shutil.which("konsole") or shutil.which("xterm") or shutil.which("tmux")
    if not term:
        raise HTTPException(400, "No terminal emulator found")
    success = await app_manager.launch(f"terminal_{int(time.time())}", term, args)
    return {"status": "ok" if success else "error"}


@router.post("/apps/kill", summary="Kill a running application")
async def kill_app(name: str, force: bool = False):
    success = await app_manager.kill(name, force=force)
    return {"status": "ok" if success else "not_found"}


@router.get("/apps/check", summary="Check if an app is installed")
async def check_installed(name: str):
    found = shutil.which(name) is not None
    return {"name": name, "installed": found}


# ── Window Management ──

@router.get("/windows", summary="List all desktop windows")
async def list_windows():
    windows = await window_manager.list_windows()
    return {
        "windows": [{
            "id": w.id, "title": w.title, "process": w.process,
            "x": w.x, "y": w.y, "width": w.width, "height": w.height,
            "minimized": w.minimized, "maximized": w.maximized,
            "focused": w.focused,
        } for w in windows],
        "count": len(windows),
    }


@router.post("/windows/focus", summary="Focus a window by title pattern")
async def focus_window(title: str):
    success = await window_manager.focus(title)
    return {"status": "ok" if success else "not_found"}


@router.post("/windows/resize", summary="Resize a window")
async def resize_window(title: str, width: int = Query(800, ge=100), height: int = Query(600, ge=100)):
    success = await window_manager.resize(title, width, height)
    return {"status": "ok" if success else "not_found"}


@router.post("/windows/minimize", summary="Minimize a window")
async def minimize_window(title: str):
    success = await window_manager.minimize(title)
    return {"status": "ok" if success else "not_found"}


@router.post("/windows/maximize", summary="Maximize a window")
async def maximize_window(title: str):
    success = await window_manager.maximize(title)
    return {"status": "ok" if success else "not_found"}


@router.post("/windows/close", summary="Close a window")
async def close_window(title: str):
    success = await window_manager.close(title)
    return {"status": "ok" if success else "not_found"}


# ── Clipboard ──

@router.get("/clipboard", summary="Get clipboard content")
async def clipboard_paste():
    text = await clipboard_manager.paste()
    return {"content": text, "length": len(text)}


@router.post("/clipboard", summary="Set clipboard content")
async def clipboard_copy(text: str = Query("", max_length=100000)):
    success = await clipboard_manager.copy(text)
    return {"status": "ok" if success else "error", "length": len(text)}


@router.get("/clipboard/history", summary="Get clipboard history")
async def clipboard_history(limit: int = 10):
    history = clipboard_manager.get_history(limit=limit)
    return {"history": history, "count": len(history)}


# ── Notifications ──

@router.post("/notify", summary="Send a desktop notification")
async def send_notification(title: str, message: str, level: str = "info"):
    success = await notification_manager.send(title, message, level)
    return {"status": "ok" if success else "error"}


# ── Command Execution ──

@router.post("/execute", summary="Run a shell command")
async def execute_command(req: CommandRequest):
    result = await desktop.execute(req.command)
    return result


# ── AI Agent ──

@router.post("/agent", summary="Tell the AI what to do on your computer")
async def desktop_agent(req: AgentTaskRequest):
    """Take a natural-language task and execute it step-by-step.
    Uses keyword-based intent matching to coordinate app launches,
    file operations, window management, and shell commands.
    """
    task = req.task.lower()
    results: list[dict] = []
    errors: list[str] = []
    start = time.time()

    # ── detect intents ──
    intents: list[str] = []
    file_ops: list[dict] = []
    app_launches: list[str] = []

    # App launch detection
    app_map = {
        "vscode": "code", "vs code": "code",
        "chrome": "google-chrome", "google chrome": "google-chrome",
        "firefox": "firefox", "terminal": "gnome-terminal",
        "photoshop": "photoshop", "gimp": "gimp",
        "slack": "slack", "discord": "discord",
        "spotify": "spotify", "vlc": "vlc",
        "sublime": "sublime_text", "sublime text": "sublime_text",
        "notepad": "notepad", "notepad++": "notepad-plus-plus",
    }
    for label, cmd in app_map.items():
        if label in task:
            app_launches.append(cmd)
            intents.append(f"launch:{cmd}")

    # File operation detection
    if any(w in task for w in ["move file", "rename file", "move ", "rename "]):
        file_ops.append({"op": "move"})
        intents.append("file:move")
    if any(w in task for w in ["copy file", "duplicate", "backup"]):
        file_ops.append({"op": "copy"})
        intents.append("file:copy")
    if any(w in task for w in ["delete file", "remove file", "delete ", "remove "]):
        file_ops.append({"op": "delete"})
        intents.append("file:delete")
    if any(w in task for w in ["compress", "zip ", "archive"]):
        file_ops.append({"op": "compress"})
        intents.append("file:compress")
    if any(w in task for w in ["download", "upload"]):
        intents.append("web:transfer")
    if any(w in task for w in ["folder", "directory", "mkdir", "create dir"]):
        intents.append("file:mkdir")
    if any(w in task for w in ["system info", "what computer", "my system"]):
        intents.append("system:info")
    if any(w in task for w in ["notify", "send notification", "alert"]):
        intents.append("system:notify")

    # ── execute intents ──
    for intent in intents:
        try:
            if intent.startswith("launch:"):
                app_name = intent.split(":", 1)[1]
                success = await app_manager.launch(app_name, app_name)
                results.append({
                    "action": f"Launch {app_name}",
                    "status": "ok" if success else "failed",
                    "detail": f"Started {app_name}" if success else f"Could not launch {app_name}",
                })
                if success:
                    await asyncio.sleep(0.5)
                    await window_manager.focus(app_name)

            elif intent == "system:info":
                info = await desktop.system_info()
                results.append({
                    "action": "Get system info",
                    "status": "ok",
                    "data": info,
                })

            elif intent == "system:notify":
                parts = req.task.split("notify", 1)
                msg = parts[1].strip().strip('"').strip("'") if len(parts) > 1 else "Task completed"
                await notification_manager.send("Desktop Agent", msg)
                results.append({
                    "action": "Send notification",
                    "status": "ok",
                    "detail": msg[:100],
                })

            elif intent == "file:compress":
                results.append({
                    "action": "Compress",
                    "status": "pending",
                    "detail": "Automatic compress requires explicit source path. Use /desktop/files/compress directly.",
                })

            elif intent == "file:mkdir":
                dir_name = f"new_folder_{int(time.time())}"
                await desktop.create_dir(dir_name)
                results.append({
                    "action": "Create directory",
                    "status": "ok",
                    "detail": f"Created {dir_name}",
                })

        except Exception as e:
            errors.append(f"{intent}: {e}")
            results.append({"action": intent, "status": "error", "detail": str(e)})

    # ── fallback: shell execution for unrecognized tasks ──
    if not intents:
        shell_task = req.task
        # Clean up conversational prefix
        for prefix in ["run ", "execute ", "please ", "can you "]:
            if shell_task.lower().startswith(prefix):
                shell_task = shell_task[len(prefix):]
        try:
            result = await desktop.execute(shell_task)
            results.append({
                "action": "Shell command",
                "status": result.get("status", "ok"),
                "detail": (result.get("stdout", "") or result.get("stderr", "") or "").strip()[:500],
                "return_code": result.get("return_code"),
            })
        except Exception as e:
            errors.append(f"shell: {e}")

    elapsed = time.time() - start
    return {
        "task": req.task,
        "results": results,
        "errors": errors if errors else None,
        "duration_seconds": round(elapsed, 2),
        "intents_detected": intents or ["shell_fallback"],
    }
