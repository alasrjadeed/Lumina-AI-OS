import logging
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DesktopService:
    def __init__(self):
        self._clipboard_history: List[str] = []

    async def list_files(self, path: str = ".") -> Dict[str, Any]:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return {"error": f"Path not found: {path}"}
        items = []
        for entry in sorted(p.iterdir()):
            items.append({
                "name": entry.name,
                "path": str(entry),
                "type": "directory" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified": entry.stat().st_mtime,
            })
        return {"path": str(p), "items": items, "count": len(items)}

    async def read_file(self, path: str) -> Dict[str, Any]:
        p = Path(path).expanduser().resolve()
        if not p.exists() or not p.is_file():
            return {"error": f"File not found: {path}"}
        try:
            content = p.read_text(encoding="utf-8", errors="replace")
            return {"path": str(p), "content": content, "size": len(content)}
        except Exception as e:
            return {"error": f"Cannot read file: {e}"}

    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        p = Path(path).expanduser().resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return {"path": str(p), "size": len(content), "status": "written"}

    async def copy_file(self, src: str, dst: str) -> Dict[str, Any]:
        try:
            shutil.copy2(src, dst)
            return {"source": src, "destination": dst, "status": "copied"}
        except Exception as e:
            return {"error": str(e)}

    async def move_file(self, src: str, dst: str) -> Dict[str, Any]:
        try:
            shutil.move(src, dst)
            return {"source": src, "destination": dst, "status": "moved"}
        except Exception as e:
            return {"error": str(e)}

    async def delete_file(self, path: str) -> Dict[str, Any]:
        p = Path(path).expanduser().resolve()
        try:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return {"path": str(p), "status": "deleted"}
        except Exception as e:
            return {"error": str(e)}

    async def clipboard_copy(self, text: str) -> Dict[str, Any]:
        self._clipboard_history.append(text)
        return {"status": "copied", "length": len(text)}

    async def clipboard_paste(self) -> Dict[str, Any]:
        if not self._clipboard_history:
            return {"error": "Clipboard empty"}
        return {"content": self._clipboard_history[-1]}

    async def get_system_info(self) -> Dict[str, Any]:
        import platform
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "hostname": platform.node(),
        }

    async def get_process_list(self) -> List[Dict[str, Any]]:
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return sorted(processes, key=lambda p: p.get("cpu_percent", 0), reverse=True)[:50]
        except ImportError:
            return [{"error": "psutil not installed"}]

    async def take_screenshot(self) -> Dict[str, Any]:
        try:
            import pyautogui
            screenshot = pyautogui.screenshot()
            import io, base64
            buf = io.BytesIO()
            screenshot.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode()
            return {"image": b64, "format": "png", "size": len(b64)}
        except ImportError:
            return {"error": "pyautogui not installed"}
