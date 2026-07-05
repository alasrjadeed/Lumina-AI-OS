from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.app.services.developer.coding_agent import CodingAgentService
from backend.app.services.developer.terminal_service import TerminalService
from backend.app.services.ai.engine import AIEngine

router = APIRouter()
engine = AIEngine()
coding_agent = CodingAgentService(engine)
terminal = TerminalService()


class CodeRequest(BaseModel):
    specification: str
    language: str = "python"


class CodeReviewRequest(BaseModel):
    code: str
    language: str = ""


class DebugRequest(BaseModel):
    code: str
    error: str


class RefactorRequest(BaseModel):
    code: str
    target: str = "performance"


class TestRequest(BaseModel):
    code: str
    framework: str = "pytest"


class TerminalExecRequest(BaseModel):
    session_id: str
    command: str


@router.post("/generate")
async def generate_code(req: CodeRequest):
    return await coding_agent.generate_code(req.specification, req.language)


@router.post("/review")
async def review_code(req: CodeReviewRequest):
    return await coding_agent.review_code(req.code, req.language)


@router.post("/debug")
async def debug_code(req: DebugRequest):
    return await coding_agent.debug_error(req.code, req.error)


@router.post("/refactor")
async def refactor_code(req: RefactorRequest):
    return await coding_agent.refactor_code(req.code, req.target)


@router.post("/test")
async def generate_tests(req: TestRequest):
    return await coding_agent.generate_tests(req.code, req.framework)


@router.post("/terminal/create")
async def create_terminal(cwd: str = "."):
    return await terminal.create_session(cwd)


@router.post("/terminal/exec")
async def terminal_exec(req: TerminalExecRequest):
    return await terminal.execute(req.session_id, req.command)


@router.get("/terminal/sessions")
async def list_sessions():
    return await terminal.list_sessions()


@router.delete("/terminal/{session_id}")
async def delete_session(session_id: str):
    return {"deleted": await terminal.delete_session(session_id)}
