import os
import platform
import shutil
import subprocess
from pathlib import Path

from core.log import log


class DesktopAutomation:
    async def execute(self, command: str) -> dict:
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            return {
                "status": "ok",
                "stdout": result.stdout[:1000],
                "stderr": result.stderr[:500],
                "return_code": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "error": "Command timed out"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def list_files(self, path: str = ".") -> list[dict]:
        p = Path(path).expanduser().resolve()
        if not p.exists():
            return []
        items = [
            {
                "name": entry.name,
                "path": str(entry),
                "type": "dir" if entry.is_dir() else "file",
                "size": entry.stat().st_size if entry.is_file() else 0,
                "modified": entry.stat().st_mtime,
            }
            for entry in p.iterdir()
        ]
        return sorted(items, key=lambda x: (x["type"], x["name"]))

    async def read_file(self, path: str) -> str | None:
        p = Path(path).expanduser()
        if p.exists() and p.is_file():
            return p.read_text()
        return None

    async def write_file(self, path: str, content: str):
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        log.info("Wrote file: %s (%d bytes)", path, len(content))

    async def copy_file(self, src: str, dst: str):
        shutil.copy2(src, dst)
        log.info("Copied %s -> %s", src, dst)

    async def move_file(self, src: str, dst: str):
        shutil.move(src, dst)
        log.info("Moved %s -> %s", src, dst)

    async def delete_file(self, path: str):
        p = Path(path).expanduser()
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
        log.info("Deleted: %s", path)

    async def create_dir(self, path: str):
        Path(path).expanduser().mkdir(parents=True, exist_ok=True)

    async def system_info(self) -> dict:
        return {
            "os": platform.system(),
            "release": platform.release(),
            "arch": platform.machine(),
            "hostname": platform.node(),
            "cwd": os.getcwd(),
            "cpu_count": os.cpu_count(),
        }


desktop = DesktopAutomation()
