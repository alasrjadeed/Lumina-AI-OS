"""Process Manager — run and stop dev servers for projects."""

from __future__ import annotations

import asyncio
import os
import signal
import time
from dataclasses import dataclass, field

from core.log import log


@dataclass
class ServerProcess:
    project_id: str
    command: str
    process: asyncio.subprocess.Process | None = None
    started_at: float = 0.0
    output_lines: list[str] = field(default_factory=list)
    max_lines: int = 500
    status: str = "stopped"


class ProcessManager:
    """Manages running dev server subprocesses for projects."""

    def __init__(self):
        self._servers: dict[str, ServerProcess] = {}

    def get_presets(self, framework: str) -> list[dict]:
        presets = {
            "React + Vite": [
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "npm run build", "command": "npm run build"},
                {"label": "npm run preview", "command": "npm run preview"},
                {"label": "npx vite", "command": "npx vite"},
            ],
            "Next.js": [
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "npm run build", "command": "npm run build"},
                {"label": "npm start", "command": "npm start"},
            ],
            "Laravel": [
                {"label": "php artisan serve", "command": "php artisan serve"},
                {"label": "php artisan migrate", "command": "php artisan migrate"},
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "php artisan test", "command": "php artisan test"},
            ],
            "FastAPI": [
                {"label": "uvicorn main:app --reload", "command": "uvicorn main:app --reload --host 0.0.0.0 --port 8000"},
                {"label": "python main.py", "command": "python main.py"},
                {"label": "pytest", "command": "pytest"},
            ],
            "PHP/Laravel": [
                {"label": "php artisan serve", "command": "php artisan serve"},
                {"label": "php artisan migrate", "command": "php artisan migrate"},
                {"label": "composer install", "command": "composer install"},
            ],
            "PHP": [
                {"label": "php -S localhost:8000", "command": "php -S localhost:8000"},
                {"label": "composer install", "command": "composer install"},
            ],
            "Express": [
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "npm start", "command": "npm start"},
                {"label": "node server.js", "command": "node server.js"},
            ],
            "Python": [
                {"label": "python main.py", "command": "python main.py"},
                {"label": "uvicorn main:app --reload", "command": "uvicorn main:app --reload --host 0.0.0.0 --port 8000"},
                {"label": "pytest", "command": "pytest"},
                {"label": "pip install -r requirements.txt", "command": "pip install -r requirements.txt"},
            ],
            "Go": [
                {"label": "go run .", "command": "go run ."},
                {"label": "go build", "command": "go build"},
                {"label": "go test ./...", "command": "go test ./..."},
            ],
            "Rust": [
                {"label": "cargo run", "command": "cargo run"},
                {"label": "cargo build", "command": "cargo build"},
                {"label": "cargo test", "command": "cargo test"},
            ],
            "JavaScript/TypeScript": [
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "npm start", "command": "npm start"},
                {"label": "npm run build", "command": "npm run build"},
            ],
            "Vue": [
                {"label": "npm run dev", "command": "npm run dev"},
                {"label": "npm run build", "command": "npm run build"},
            ],
            "Angular": [
                {"label": "ng serve", "command": "ng serve"},
                {"label": "ng build", "command": "ng build"},
            ],
        }
        return presets.get(framework, [
            {"label": "npm run dev", "command": "npm run dev"},
            {"label": "npm start", "command": "npm start"},
            {"label": "npm run build", "command": "npm run build"},
            {"label": "python main.py", "command": "python main.py"},
        ])

    async def start(self, project_id: str, command: str, project_path: str) -> dict:
        if project_id in self._servers and self._servers[project_id].status == "running":
            return {"error": "Server already running", "status": "running"}

        cwd = os.path.expanduser(project_path)
        if not os.path.exists(cwd):
            return {"error": f"Project path does not exist: {cwd}"}

        server = ServerProcess(project_id=project_id, command=command)
        self._servers[project_id] = server

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                cwd=cwd,
                preexec_fn=os.setsid,
            )
            server.process = proc
            server.status = "running"
            server.started_at = time.time()
            log.info("Process: [%s] started '%s' in %s", project_id, command, cwd)

            asyncio.create_task(self._read_output(project_id, proc))
        except Exception as e:
            server.status = "failed"
            log.error("Process: [%s] failed to start: %s", project_id, e)
            return {"error": str(e)}

        return {
            "status": "running",
            "command": command,
            "project_id": project_id,
            "pid": proc.pid,
        }

    async def _read_output(self, project_id: str, proc: asyncio.subprocess.Process):
        server = self._servers.get(project_id)
        if not server:
            return

        try:
            while True:
                line = await proc.stdout.readline()
                if not line:
                    break
                decoded = line.decode("utf-8", errors="replace").rstrip()
                server.output_lines.append(decoded)
                if len(server.output_lines) > server.max_lines:
                    server.output_lines = server.output_lines[-server.max_lines:]
        except Exception:
            pass

        await proc.wait()
        server = self._servers.get(project_id)
        if server:
            server.status = "stopped" if proc.returncode == 0 else "crashed"
            server.output_lines.append(
                f"\n[Process exited with code {proc.returncode}]"
            )
            log.info("Process: [%s] exited with code %d", project_id, proc.returncode)

    async def stop(self, project_id: str) -> dict:
        server = self._servers.get(project_id)
        if not server or not server.process:
            return {"error": "No running server", "status": "stopped"}

        if server.status != "running":
            return {"status": server.status}

        try:
            pgid = os.getpgid(server.process.pid)
            os.killpg(pgid, signal.SIGTERM)
            try:
                await asyncio.wait_for(server.process.wait(), timeout=5)
            except asyncio.TimeoutError:
                os.killpg(pgid, signal.SIGKILL)
            server.status = "stopped"
            log.info("Process: [%s] stopped", project_id)
        except ProcessLookupError:
            server.status = "stopped"
        except Exception as e:
            log.error("Process: [%s] stop failed: %s", project_id, e)
            return {"error": str(e)}

        return {"status": "stopped", "command": server.command}

    def get_output(self, project_id: str, since_line: int = 0) -> dict:
        server = self._servers.get(project_id)
        if not server:
            return {"output": [], "status": "no_server", "since_line": 0}

        lines = server.output_lines[since_line:]
        return {
            "output": lines,
            "status": server.status,
            "command": server.command,
            "total_lines": len(server.output_lines),
            "since_line": since_line,
            "started_at": server.started_at,
        }

    def get_status(self, project_id: str) -> dict:
        server = self._servers.get(project_id)
        if not server:
            return {"status": "stopped", "running": False}

        return {
            "status": server.status,
            "running": server.status == "running",
            "command": server.command,
            "started_at": server.started_at,
            "output_lines": len(server.output_lines),
            "uptime_seconds": int(time.time() - server.started_at) if server.started_at else 0,
        }

    def get_running(self) -> list[dict]:
        return [
            {"project_id": pid, "command": s.command, "status": s.status,
             "uptime": int(time.time() - s.started_at) if s.started_at else 0}
            for pid, s in self._servers.items()
            if s.status == "running"
        ]


process_manager = ProcessManager()
