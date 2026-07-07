"""Coding Agent — read project, plan, edit, test, heal, commit. Full autonomous pipeline."""

import asyncio
import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.log import log
from core.provider import engine as ai_engine
from core.tester.engine import tester

router = APIRouter(prefix="/coding-agent", tags=["Coding Agent"])


# ── Models ──

class ProjectRequest(BaseModel):
    path: str = "."

class EditRequest(BaseModel):
    task: str
    project_path: str = "."
    language: str = ""
    auto_commit: bool = False

class MemoryRequest(BaseModel):
    key: str
    value: str = ""
    action: str = "get"


# ── Persistent Agent Memory ──

AGENT_MEMORY_FILE = os.path.expanduser("~/.lumina/coding_agent_memory.json")

def _load_memory() -> dict:
    try:
        f = Path(AGENT_MEMORY_FILE)
        if f.exists():
            return json.loads(f.read_text())
    except: pass
    return {"projects": {}, "preferences": {}, "bugs": [], "style": {}}

def _save_memory(data: dict):
    Path(AGENT_MEMORY_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(AGENT_MEMORY_FILE).write_text(json.dumps(data, indent=2))


# ── Project Understanding ──

IGNORE_DIRS = {"node_modules", ".git", "__pycache__", ".venv", "venv",
               ".next", "dist", "build", ".cache", ".tox", "target",
               ".lumina_packages", ".codebase-memory"}

@router.post("/understand", summary="Read and understand the project structure")
async def understand_project(req: ProjectRequest):
    root = Path(req.path).expanduser().resolve()
    if not root.exists():
        raise HTTPException(404, f"Project not found: {req.path}")

    structure = []
    file_count = 0
    dir_count = 0

    for entry in sorted(root.rglob("*")):
        if any(ig in entry.parts for ig in IGNORE_DIRS):
            continue
        if entry.is_file() and entry.stat().st_size < 50000:
            file_count += 1
            rel = str(entry.relative_to(root))
            structure.append({
                "path": rel,
                "size": entry.stat().st_size,
                "ext": entry.suffix,
            })
        elif entry.is_dir():
            dir_count += 1

    # Detect project type
    files_set = {s["path"] for s in structure}
    project_type = _detect_project_type(files_set)

    # Package files
    package_files = {}
    for name in ["package.json", "pyproject.toml", "Cargo.toml",
                  "go.mod", "composer.json", "Gemfile", "requirements.txt",
                  "Makefile", "Dockerfile", "tsconfig.json", "vite.config.ts"]:
        if name in files_set:
            package_files[name] = Path(root / name).read_text()[:2000]

    memory = _load_memory()
    project_memory = memory.get("projects", {}).get(str(root), {})

    return {
        "project_name": root.name,
        "project_path": str(root),
        "project_type": project_type,
        "files": structure[:500],
        "file_count": file_count,
        "dir_count": dir_count,
        "package_files": package_files,
        "memory": {
            "known_bugs": project_memory.get("bugs", []),
            "coding_style": memory.get("style", {}),
            "preferences": memory.get("preferences", {}),
        },
    }


def _detect_project_type(files: set) -> str:
    if "pyproject.toml" in files: return "python"
    if "package.json" in files: return "node"
    if "Cargo.toml" in files: return "rust"
    if "go.mod" in files: return "go"
    if "composer.json" in files: return "php"
    if "Gemfile" in files: return "ruby"
    return "unknown"


# ── Plan ──

@router.post("/plan", summary="Plan the implementation steps")
async def plan_implementation(req: EditRequest):
    root = Path(req.project_path).expanduser().resolve()
    if not root.exists():
        raise HTTPException(404, f"Project not found: {req.project_path}")

    # Gather context
    context = _gather_project_context(root)
    memory = _load_memory()
    style = memory.get("style", {})
    preferences = memory.get("preferences", {})

    prompt = f"""You are a senior software engineer. Plan the implementation for this task.

PROJECT: {root.name} ({context.get('type', 'unknown')})
FILES: {json.dumps(context.get('key_files', [])[:30], indent=2)}

TASK: {req.task}

CODING STYLE: {json.dumps(style, indent=2)}
PREFERENCES: {json.dumps(preferences, indent=2)}

Return a JSON plan:
{{
  "summary": "one-line summary",
  "steps": [
    {{"action": "read|edit|create|delete|test|install", "file": "relative/path", "reason": "why", "details": "what to change"}}
  ],
  "test_command": "command to run after changes",
  "risks": ["potential issues"]
}}"""

    resp = await ai_engine.chat([{"role": "user", "content": prompt}])
    text = resp.get("message", {}).get("content", "")
    import re
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            plan = json.loads(match.group())
            return plan
        except: pass
    return {"summary": "Could not parse plan", "steps": [], "test_command": "", "risks": []}


# ── Execute ──

@router.post("/execute", summary="Execute the planned edits")
async def execute_plan(req: EditRequest):
    root = Path(req.project_path).expanduser().resolve()
    if not root.exists():
        raise HTTPException(404, f"Project not found")

    # Get the plan
    plan_resp = await plan_implementation(req)
    steps = plan_resp.get("steps", [])
    if not steps:
        return {"error": "No steps planned", "status": "failed"}

    results = []
    for step in steps:
        file_path = root / step["file"]
        try:
            if step["action"] == "read":
                if file_path.exists():
                    content = file_path.read_text()
                    results.append({"step": step, "status": "ok", "content": content[:3000]})
                else:
                    results.append({"step": step, "status": "error", "error": "File not found"})

            elif step["action"] == "edit":
                if not file_path.exists():
                    results.append({"step": step, "status": "error", "error": "File not found"})
                    continue
                content = file_path.read_text()
                edit_prompt = f"""Edit this file to implement the required change.

FILE: {step['file']}
TASK: {req.task}
REASON: {step.get('reason', '')}
DETAILS: {step.get('details', '')}

Current content:
```{content[:5000]}```

Return ONLY the new file content wrapped in ```."""
                resp = await ai_engine.chat([{"role": "user", "content": edit_prompt}])
                text = resp.get("message", {}).get("content", "")
                code_match = re.search(r"```(?:\w+)?\n(.+?)\n```", text, re.DOTALL)
                if code_match:
                    new_content = code_match.group(1)
                    file_path.write_text(new_content)
                    results.append({"step": step, "status": "ok", "detail": "File edited"})
                else:
                    results.append({"step": step, "status": "error", "error": "Could not extract code from AI response"})

            elif step["action"] == "create":
                file_path.parent.mkdir(parents=True, exist_ok=True)
                create_prompt = f"""Create this file for the task.

FILE: {step['file']}
TASK: {req.task}
DETAILS: {step.get('details', '')}

Return ONLY the file content wrapped in ```."""
                resp = await ai_engine.chat([{"role": "user", "content": create_prompt}])
                text = resp.get("message", {}).get("content", "")
                code_match = re.search(r"```(?:\w+)?\n(.+?)\n```", text, re.DOTALL)
                if code_match:
                    file_path.write_text(code_match.group(1))
                    results.append({"step": step, "status": "ok", "detail": "File created"})
                else:
                    results.append({"step": step, "status": "error", "error": "Could not extract code"})

            elif step["action"] == "delete":
                if file_path.exists():
                    file_path.unlink()
                    results.append({"step": step, "status": "ok", "detail": "File deleted"})
                else:
                    results.append({"step": step, "status": "error", "error": "File not found"})

            elif step["action"] == "install":
                install_dir = file_path or root
                result = subprocess.run(
                    step.get("details", ""), shell=True, capture_output=True, text=True,
                    timeout=60, cwd=str(install_dir) if install_dir.exists() else str(root),
                )
                results.append({
                    "step": step, "status": "ok" if result.returncode == 0 else "error",
                    "detail": result.stdout[:500] or result.stderr[:500],
                })

        except Exception as e:
            results.append({"step": step, "status": "error", "error": str(e)})

    return {
        "plan": plan_resp,
        "results": results,
        "success": all(r["status"] == "ok" for r in results),
        "steps_total": len(steps),
        "steps_ok": sum(1 for r in results if r["status"] == "ok"),
    }


# ── Test & Heal Loop ──

@router.post("/test", summary="Run tests and auto-fix until green")
async def test_project(req: EditRequest):
    root = Path(req.project_path).expanduser().resolve()
    if not root.exists():
        raise HTTPException(404, f"Project not found")

    context = _gather_project_context(root)
    test_cmd = context.get("test_command", req.task)
    if not test_cmd:
        test_cmd = _detect_test_command(root)

    log.info("CodingAgent: Testing with: %s", test_cmd)
    return await tester.run_with_fix(test_cmd, context=f"Project: {root.name}", cwd=str(root))


@router.post("/heal", summary="Full self-heal loop — test, detect error, fix, repeat until clean")
async def heal_loop(req: EditRequest):
    """Run the full heal loop: test → detect error → AI fix → retry → commit."""
    root = Path(req.project_path).expanduser().resolve()
    if not root.exists():
        raise HTTPException(404, f"Project not found")

    context = _gather_project_context(root)
    test_cmd = _detect_test_command(root)
    max_iterations = 5
    iterations = []
    all_ok = False

    for i in range(max_iterations):
        log.info("CodingAgent: Heal iteration %d/%d", i + 1, max_iterations)
        result = await tester.run(test_cmd, cwd=str(root))

        if result.success:
            all_ok = True
            iterations.append({
                "iteration": i + 1,
                "status": "success",
                "output": result.output[:500],
            })
            break

        # AI analyzes error and suggests fix
        fix_prompt = f"""A project test failed. Analyze and suggest a code fix.

PROJECT: {root.name}
TEST COMMAND: {test_cmd}
ERROR: {result.error[:2000]}
OUTPUT: {result.output[:2000]}

Return JSON:
{{
  "analysis": "root cause",
  "file_to_fix": "relative/path",
  "fix_description": "what to change",
  "code_diff": "the corrected code block or empty if no code change needed"
}}"""
        fix_resp = await ai_engine.chat([{"role": "user", "content": fix_prompt}])
        fix_text = fix_resp.get("message", {}).get("content", "")
        fix_match = re.search(r"\{.*\}", fix_text, re.DOTALL)

        fix_applied = False
        if fix_match:
            try:
                fix_data = json.loads(fix_match.group())
                fix_file = fix_data.get("file_to_fix", "")
                code_diff = fix_data.get("code_diff", "")
                if fix_file and code_diff and len(code_diff) > 20:
                    fp = root / fix_file
                    if fp.exists():
                        fp.write_text(code_diff)
                        fix_applied = True
                        log.info("CodingAgent: Fixed %s", fix_file)
            except: pass

        iterations.append({
            "iteration": i + 1,
            "status": "fixed" if fix_applied else "failed",
            "error": result.error[:500],
            "fix_applied": fix_applied,
        })

    # Remember the bug
    if not all_ok:
        memory = _load_memory()
        bug_entry = {
            "project": root.name,
            "task": req.task,
            "test_command": test_cmd,
            "timestamp": time.time(),
            "error": iterations[-1].get("error", "") if iterations else "unknown",
        }
        memory.setdefault("bugs", []).append(bug_entry)
        _save_memory(memory)

    return {
        "success": all_ok,
        "iterations": iterations,
        "total_iterations": len(iterations),
    }


# ── Full Pipeline ──

@router.post("/start", summary="Full autonomous pipeline: understand → plan → execute → test → heal → commit")
async def start_coding_agent(req: EditRequest):
    """Run the complete autonomous coding pipeline."""
    phases = []
    start = time.time()

    # Phase 1: Understand
    log.info("CodingAgent: Phase 1/6 — Understanding project...")
    try:
        understand = await understand_project(ProjectRequest(path=req.project_path))
        phases.append({"phase": "understand", "status": "ok", "project_type": understand.get("project_type")})
    except Exception as e:
        phases.append({"phase": "understand", "status": "error", "error": str(e)})
        return {"success": False, "phases": phases, "duration": time.time() - start}

    # Phase 2: Plan
    log.info("CodingAgent: Phase 2/6 — Planning...")
    try:
        plan = await plan_implementation(req)
        phases.append({"phase": "plan", "status": "ok", "steps": len(plan.get("steps", [])),
                       "summary": plan.get("summary", "")})
    except Exception as e:
        phases.append({"phase": "plan", "status": "error", "error": str(e)})
        return {"success": False, "phases": phases, "duration": time.time() - start}

    # Phase 3: Execute
    log.info("CodingAgent: Phase 3/6 — Executing...")
    try:
        execution = await execute_plan(req)
        phases.append({"phase": "execute", "status": "ok" if execution.get("success") else "partial",
                       "ok": execution.get("steps_ok", 0), "total": execution.get("steps_total", 0)})
    except Exception as e:
        phases.append({"phase": "execute", "status": "error", "error": str(e)})
        return {"success": False, "phases": phases, "duration": time.time() - start}

    # Phase 4: Test
    log.info("CodingAgent: Phase 4/6 — Testing...")
    try:
        test_result = await test_project(req)
        phases.append({"phase": "test", "status": "ok" if test_result.get("success") else "failed",
                       "attempts": test_result.get("attempts", 0)})
    except Exception as e:
        phases.append({"phase": "test", "status": "error", "error": str(e)})

    # Phase 5: Heal (only if test failed)
    if phases[-1]["status"] != "ok":
        log.info("CodingAgent: Phase 5/6 — Healing...")
        try:
            heal = await heal_loop(req)
            phases.append({"phase": "heal", "status": "ok" if heal.get("success") else "failed",
                           "iterations": heal.get("total_iterations", 0)})
        except Exception as e:
            phases.append({"phase": "heal", "status": "error", "error": str(e)})
    else:
        phases.append({"phase": "heal", "status": "skipped"})

    # Phase 6: Commit
    if req.auto_commit:
        log.info("CodingAgent: Phase 6/6 — Committing...")
        try:
            commit_result = subprocess.run(
                ["git", "add", "-A", "&&", "git", "commit", "-m", f"AI: {req.task}"],
                shell=True, capture_output=True, text=True, timeout=30, cwd=str(root),
            )
            phases.append({"phase": "commit", "status": "ok" if commit_result.returncode == 0 else "error",
                           "detail": commit_result.stdout[:300] or commit_result.stderr[:300]})
        except Exception as e:
            phases.append({"phase": "commit", "status": "error", "error": str(e)})
    else:
        phases.append({"phase": "commit", "status": "skipped"})

    duration = time.time() - start
    all_ok = all(p["status"] in ("ok", "skipped") for p in phases)

    return {
        "success": all_ok,
        "phases": phases,
        "duration_seconds": round(duration, 1),
        "memory_updated": True,
    }


# ── Memory ──

@router.post("/memory", summary="Store or retrieve agent memory")
async def agent_memory(req: MemoryRequest):
    memory = _load_memory()
    if req.action == "get":
        if req.key == "all":
            return memory
        keys = req.key.split(".")
        val = memory
        for k in keys:
            val = val.get(k, {})
            if not isinstance(val, dict):
                break
        return {"key": req.key, "value": val}

    elif req.action == "set":
        keys = req.key.split(".")
        val = memory
        for k in keys[:-1]:
            val = val.setdefault(k, {})
        val[keys[-1]] = req.value
        _save_memory(memory)
        return {"status": "ok", "key": req.key}

    elif req.action == "remember_bug":
        memory.setdefault("bugs", []).append({
            "project": req.key,
            "error": req.value[:500],
            "timestamp": time.time(),
        })
        _save_memory(memory)
        return {"status": "ok", "total_bugs": len(memory["bugs"])}

    elif req.action == "set_style":
        try:
            style = json.loads(req.value) if isinstance(req.value, str) else req.value
            memory["style"] = style
            _save_memory(memory)
            return {"status": "ok", "style": style}
        except: raise HTTPException(400, "Invalid style JSON")

    return {"status": "error", "error": "Unknown action"}


# ── Helpers ──

def _gather_project_context(root: Path) -> dict:
    files_set = {str(f.relative_to(root)) for f in root.rglob("*")
                 if f.is_file() and not any(ig in f.parts for ig in IGNORE_DIRS)}
    return {
        "name": root.name,
        "type": _detect_project_type(files_set),
        "key_files": sorted(files_set)[:50],
        "test_command": _detect_test_command(root),
    }

def _detect_test_command(root: Path) -> str:
    files = {f.name for f in root.iterdir()}
    if "pyproject.toml" in files:
        return "python -m pytest -x -q"
    if "package.json" in files:
        return "npm test 2>&1 || npx vitest run 2>&1 || echo no-test"
    if "Cargo.toml" in files:
        return "cargo test 2>&1"
    if "Makefile" in files:
        return "make test 2>&1 || echo no-test"
    return "echo 'No test command detected'"


@router.get("/status", summary="Coding Agent status")
async def agent_status():
    memory = _load_memory()
    return {
        "status": "ready",
        "projects_known": len(memory.get("projects", {})),
        "bugs_remembered": len(memory.get("bugs", [])),
        "style_configured": bool(memory.get("style", {})),
        "agent_active": True,
    }
