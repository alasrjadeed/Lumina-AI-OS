import asyncio
import logging
import os
import signal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TerminalSession:
    def __init__(self, session_id: str, cwd: str = "."):
        self.id = session_id
        self.cwd = cwd
        self.process: Optional[asyncio.subprocess.Process] = None
        self.output: List[str] = []
        self._running = False

    async def execute(self, command: str) -> Dict[str, Any]:
        self._running = True
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.cwd,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            out = stdout.decode(errors="replace") if stdout else ""
            err = stderr.decode(errors="replace") if stderr else ""
            self.output.append(out + err)
            self._running = False
            return {
                "stdout": out,
                "stderr": err,
                "exit_code": proc.returncode,
                "session_id": self.id,
            }
        except asyncio.TimeoutError:
            if proc:
                proc.kill()
            self._running = False
            return {"stdout": "", "stderr": "Command timed out (30s)", "exit_code": -1, "session_id": self.id}
        except Exception as e:
            self._running = False
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "session_id": self.id}


class TerminalService:
    def __init__(self):
        self._sessions: Dict[str, TerminalSession] = {}

    async def create_session(self, cwd: str = ".") -> Dict[str, Any]:
        session_id = f"term_{len(self._sessions) + 1}"
        self._sessions[session_id] = TerminalSession(session_id, cwd)
        return {"session_id": session_id, "cwd": cwd}

    async def execute(self, session_id: str, command: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            return {"error": "Session not found"}
        return await session.execute(command)

    async def list_sessions(self) -> List[Dict[str, Any]]:
        return [{"id": s.id, "cwd": s.cwd, "running": s._running} for s in self._sessions.values()]

    async def delete_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None
