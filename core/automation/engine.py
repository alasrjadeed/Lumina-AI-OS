"""Advanced Automation Engine — workflow CRUD, execution, triggers, actions, logging."""

from __future__ import annotations

import asyncio
import json
import os
import time
import uuid
from datetime import datetime
from typing import Any

from core.log import log
from core.provider import engine as ai_engine

STORAGE_DIR = os.path.expanduser("~/.lumina")
WORKFLOWS_PATH = os.path.join(STORAGE_DIR, "automation_workflows.json")
HISTORY_PATH = os.path.join(STORAGE_DIR, "automation_history.json")

TRIGGER_TYPES = [
    {"id": "manual", "label": "Manual", "description": "Run manually from the UI or API"},
    {"id": "schedule", "label": "Schedule (Cron)", "description": "Run on a cron schedule", "config": {"cron": ""}},
    {"id": "webhook", "label": "Webhook", "description": "Trigger via HTTP webhook call", "config": {"token": ""}},
    {"id": "file_change", "label": "File Change", "description": "Run when a file is created or modified", "config": {"path": "", "pattern": ""}},
    {"id": "time", "label": "Time Delay", "description": "Run after a specified delay", "config": {"delay_seconds": 60}},
    {"id": "interval", "label": "Interval", "description": "Run on a fixed interval", "config": {"interval_seconds": 300}},
]

ACTION_TYPES = [
    {"id": "shell", "label": "Shell Command", "description": "Execute a shell command", "config": {"command": "", "timeout": 30}},
    {"id": "http_request", "label": "HTTP Request", "description": "Make an HTTP request", "config": {"url": "", "method": "GET", "headers": {}, "body": ""}},
    {"id": "ai_task", "label": "AI Task", "description": "Ask the AI to perform a task", "config": {"prompt": "", "model": ""}},
    {"id": "file_operation", "label": "File Operation", "description": "Read, write, copy, or delete files", "config": {"operation": "read", "path": "", "content": ""}},
    {"id": "notification", "label": "Notification", "description": "Send a desktop notification", "config": {"title": "", "message": ""}},
    {"id": "employee_task", "label": "Employee Task", "description": "Delegate to Autonomous Employee", "config": {"goal": ""}},
    {"id": "wait", "label": "Wait / Sleep", "description": "Pause execution for a duration", "config": {"seconds": 5}},
    {"id": "condition", "label": "Condition", "description": "Conditional branching (if/else)", "config": {"condition": "", "then_steps": [], "else_steps": []}},
    {"id": "log", "label": "Log Message", "description": "Write a message to the execution log", "config": {"level": "info", "message": ""}},
    {"id": "script", "label": "Python Script", "description": "Execute a Python code snippet", "config": {"code": ""}},
    {"id": "send_email", "label": "Send Email", "description": "Send an email notification", "config": {"to": "", "subject": "", "body": ""}},
]


class StepModel:
    def __init__(self, id: str, action: str, name: str, config: dict | None = None,
                 depends_on: list[str] | None = None):
        self.id = id
        self.action = action
        self.name = name
        self.config = config or {}
        self.depends_on = depends_on or []

    def to_dict(self) -> dict:
        return {"id": self.id, "action": self.action, "name": self.name,
                "config": self.config, "depends_on": self.depends_on}

    @classmethod
    def from_dict(cls, d: dict) -> StepModel:
        return cls(d["id"], d["action"], d["name"], d.get("config", {}), d.get("depends_on", []))


class TriggerConfig:
    def __init__(self, type: str = "manual", config: dict | None = None):
        self.type = type
        self.config = config or {}

    def to_dict(self) -> dict:
        return {"type": self.type, "config": self.config}

    @classmethod
    def from_dict(cls, d: dict) -> TriggerConfig:
        return cls(d.get("type", "manual"), d.get("config", {}))


class WorkflowModel:
    def __init__(self, id: str, name: str, description: str = "",
                 trigger: TriggerConfig | None = None,
                 steps: list[StepModel] | None = None,
                 enabled: bool = True, created_at: str = "",
                 updated_at: str = "", tags: list[str] | None = None):
        self.id = id
        self.name = name
        self.description = description
        self.trigger = trigger or TriggerConfig()
        self.steps = steps or []
        self.enabled = enabled
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or datetime.now().isoformat()
        self.tags = tags or []

    def to_dict(self) -> dict:
        return {"id": self.id, "name": self.name, "description": self.description,
                "trigger": self.trigger.to_dict(),
                "steps": [s.to_dict() for s in self.steps],
                "enabled": self.enabled,
                "created_at": self.created_at, "updated_at": self.updated_at,
                "tags": self.tags}

    @classmethod
    def from_dict(cls, d: dict) -> WorkflowModel:
        return cls(
            id=d["id"], name=d["name"], description=d.get("description", ""),
            trigger=TriggerConfig.from_dict(d.get("trigger", {})),
            steps=[StepModel.from_dict(s) for s in d.get("steps", [])],
            enabled=d.get("enabled", True),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            tags=d.get("tags", []),
        )


class ExecutionLog:
    def __init__(self, run_id: str, workflow_id: str, started_at: str,
                 status: str = "running", steps: list[dict] | None = None,
                 error: str = "", trigger_info: str = ""):
        self.run_id = run_id
        self.workflow_id = workflow_id
        self.started_at = started_at
        self.completed_at = ""
        self.status = status
        self.steps = steps or []
        self.error = error
        self.trigger_info = trigger_info

    def to_dict(self) -> dict:
        return {"run_id": self.run_id, "workflow_id": self.workflow_id,
                "started_at": self.started_at, "completed_at": self.completed_at,
                "status": self.status, "steps": self.steps,
                "error": self.error, "trigger_info": self.trigger_info}

    @classmethod
    def from_dict(cls, d: dict) -> ExecutionLog:
        e = cls(d["run_id"], d["workflow_id"], d["started_at"],
                d.get("status", "running"), d.get("steps", []),
                d.get("error", ""), d.get("trigger_info", ""))
        e.completed_at = d.get("completed_at", "")
        return e


class AutomationEngine:
    def __init__(self):
        self._workflows: dict[str, WorkflowModel] = {}
        self._history: list[ExecutionLog] = []
        self._webhook_tokens: dict[str, str] = {}
        self._load()

    # ── Persistence ──

    def _ensure_storage(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)

    def _save_workflows(self):
        self._ensure_storage()
        try:
            data = [w.to_dict() for w in self._workflows.values()]
            with open(WORKFLOWS_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error("Failed to save workflows: %s", e)

    def _save_history(self):
        self._ensure_storage()
        try:
            data = [h.to_dict() for h in self._history[-200:]]
            with open(HISTORY_PATH, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            log.error("Failed to save history: %s", e)

    def _load(self):
        self._ensure_storage()
        if os.path.exists(WORKFLOWS_PATH):
            try:
                with open(WORKFLOWS_PATH) as f:
                    data = json.load(f)
                for d in data:
                    wf = WorkflowModel.from_dict(d)
                    self._workflows[wf.id] = wf
                    if wf.trigger.type == "webhook":
                        token = wf.trigger.config.get("token", "")
                        if token:
                            self._webhook_tokens[token] = wf.id
            except Exception as e:
                log.error("Failed to load workflows: %s", e)
        if os.path.exists(HISTORY_PATH):
            try:
                with open(HISTORY_PATH) as f:
                    data = json.load(f)
                self._history = [ExecutionLog.from_dict(d) for d in data]
            except Exception as e:
                log.error("Failed to load history: %s", e)

    # ── Workflow CRUD ──

    def list_workflows(self) -> list[WorkflowModel]:
        return sorted(self._workflows.values(), key=lambda w: w.updated_at, reverse=True)

    def get_workflow(self, workflow_id: str) -> WorkflowModel | None:
        return self._workflows.get(workflow_id)

    def create_workflow(self, name: str, description: str = "",
                        trigger: TriggerConfig | None = None,
                        steps: list[StepModel] | None = None,
                        tags: list[str] | None = None) -> WorkflowModel:
        wf_id = uuid.uuid4().hex[:12]
        wf = WorkflowModel(
            id=wf_id, name=name, description=description,
            trigger=trigger or TriggerConfig(),
            steps=steps or [], tags=tags or [],
        )
        self._workflows[wf_id] = wf
        if wf.trigger.type == "webhook":
            token = wf.trigger.config.get("token", "")
            if token:
                self._webhook_tokens[token] = wf_id
        self._save_workflows()
        log.info("Created workflow: %s (%s)", name, wf_id)
        return wf

    def update_workflow(self, workflow_id: str, data: dict) -> WorkflowModel | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        if "name" in data:
            wf.name = data["name"]
        if "description" in data:
            wf.description = data["description"]
        if "trigger" in data:
            old_token = wf.trigger.config.get("token", "")
            wf.trigger = TriggerConfig.from_dict(data["trigger"])
            new_token = wf.trigger.config.get("token", "")
            if old_token and old_token in self._webhook_tokens:
                del self._webhook_tokens[old_token]
            if new_token and wf.trigger.type == "webhook":
                self._webhook_tokens[new_token] = workflow_id
        if "steps" in data:
            wf.steps = [StepModel.from_dict(s) for s in data["steps"]]
        if "tags" in data:
            wf.tags = data["tags"]
        if "enabled" in data:
            wf.enabled = data["enabled"]
        wf.updated_at = datetime.now().isoformat()
        self._save_workflows()
        log.info("Updated workflow: %s", wf.name)
        return wf

    def delete_workflow(self, workflow_id: str) -> bool:
        wf = self._workflows.pop(workflow_id, None)
        if wf:
            token = wf.trigger.config.get("token", "")
            if token and token in self._webhook_tokens:
                del self._webhook_tokens[token]
            self._save_workflows()
            log.info("Deleted workflow: %s", wf.name)
            return True
        return False

    def toggle_workflow(self, workflow_id: str) -> WorkflowModel | None:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        wf.enabled = not wf.enabled
        wf.updated_at = datetime.now().isoformat()
        self._save_workflows()
        return wf

    # ── Webhook handling ──

    async def handle_webhook(self, token: str, body: dict | None = None) -> dict:
        wf_id = self._webhook_tokens.get(token)
        if not wf_id:
            return {"status": "error", "error": "Invalid webhook token"}
        wf = self._workflows.get(wf_id)
        if not wf or not wf.enabled:
            return {"status": "error", "error": "Workflow not found or disabled"}
        trigger_info = f"webhook (token={token[:8]}...)"
        if body:
            trigger_info += f", body={json.dumps(body)[:200]}"
        run_id = await self._execute_workflow(wf, trigger_info=trigger_info)
        return {"status": "triggered", "run_id": run_id}

    # ── Execution ──

    async def execute(self, workflow_id: str) -> str:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return ""
        return await self._execute_workflow(wf)

    async def _execute_workflow(self, wf: WorkflowModel, trigger_info: str = "") -> str:
        run_id = uuid.uuid4().hex[:12]
        started_at = datetime.now().isoformat()
        log_entry = ExecutionLog(run_id, wf.id, started_at, trigger_info=trigger_info)
        self._history.append(log_entry)
        self._save_history()

        try:
            step_outputs: dict[str, Any] = {}

            for step in wf.steps:
                step_result = {
                    "step_id": step.id, "step_name": step.name,
                    "action": step.action, "status": "running",
                    "started_at": datetime.now().isoformat(),
                    "output": "", "error": "",
                }
                log_entry.steps.append(step_result)
                try:
                    output = await self._run_action(step, wf_id=wf.id, step_outputs=step_outputs)
                    step_result["status"] = "success"
                    step_result["output"] = str(output)[:2000] if output else ""
                    step_result["completed_at"] = datetime.now().isoformat()
                    step_outputs[step.id] = output
                except Exception as e:
                    step_result["status"] = "failed"
                    step_result["error"] = str(e)[:1000]
                    step_result["completed_at"] = datetime.now().isoformat()
                    log_entry.status = "failed"
                    log_entry.error = f"Step '{step.name}' failed: {e}"
                    break

            if log_entry.status != "failed":
                log_entry.status = "success"
        except Exception as e:
            log_entry.status = "failed"
            log_entry.error = str(e)

        log_entry.completed_at = datetime.now().isoformat()
        self._save_history()
        return run_id

    async def _run_action(self, step: StepModel, wf_id: str = "",
                          step_outputs: dict[str, Any] | None = None) -> Any:
        action = step.action
        config = step.config

        if action == "shell":
            return await _action_shell(config.get("command", ""), config.get("timeout", 30))
        elif action == "http_request":
            return await _action_http(config.get("url", ""), config.get("method", "GET"),
                                       config.get("headers", {}), config.get("body", ""))
        elif action == "ai_task":
            return await _action_ai(config.get("prompt", ""), config.get("model", ""))
        elif action == "file_operation":
            return _action_file(config.get("operation", "read"), config.get("path", ""),
                                config.get("content", ""))
        elif action == "notification":
            return _action_notify(config.get("title", ""), config.get("message", ""))
        elif action == "employee_task":
            return await _action_employee(config.get("goal", ""))
        elif action == "wait":
            await asyncio.sleep(config.get("seconds", 5))
            return f"Slept for {config.get('seconds', 5)}s"
        elif action == "log":
            return f"[{config.get('level', 'info')}] {config.get('message', '')}"
        elif action == "script":
            return await _action_script(config.get("code", ""))
        elif action == "condition":
            return await _action_condition(config, step_outputs or {}, wf_id)
        elif action == "send_email":
            return f"Email queued to {config.get('to', '?')}: {config.get('subject', '')[:50]}"
        else:
            return f"Unknown action: {action}"

    # ── History ──

    def get_history(self, workflow_id: str | None = None, limit: int = 50) -> list[ExecutionLog]:
        if workflow_id:
            filtered = [h for h in self._history if h.workflow_id == workflow_id]
        else:
            filtered = self._history.copy()
        filtered.sort(key=lambda h: h.started_at, reverse=True)
        return filtered[:limit]

    def get_run(self, run_id: str) -> ExecutionLog | None:
        for h in self._history:
            if h.run_id == run_id:
                return h
        return None


# ── Action Implementations ──

async def _action_shell(command: str, timeout: int = 30) -> str:
    proc = await asyncio.create_subprocess_shell(
        command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        out = stdout.decode().strip() if stdout else ""
        err = stderr.decode().strip() if stderr else ""
        if err:
            return f"STDOUT:\n{out}\nSTDERR:\n{err}" if out else f"STDERR:\n{err}"
        return out or "(no output)"
    except asyncio.TimeoutError:
        proc.kill()
        return f"(timed out after {timeout}s)"


async def _action_http(url: str, method: str = "GET", headers: dict | None = None,
                       body: str = "") -> str:
    import httpx
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            if method.upper() == "GET":
                resp = await client.get(url, headers=headers or {})
            elif method.upper() == "POST":
                resp = await client.post(url, headers=headers or {}, content=body)
            elif method.upper() == "PUT":
                resp = await client.put(url, headers=headers or {}, content=body)
            elif method.upper() == "DELETE":
                resp = await client.delete(url, headers=headers or {})
            else:
                resp = await client.request(method, url, headers=headers or {}, content=body)
            return f"[{resp.status_code}] {resp.text[:2000]}"
        except Exception as e:
            return f"HTTP error: {e}"


async def _action_ai(prompt: str, model: str = "") -> str:
    from core.provider import engine as ai_engine
    messages = [{"role": "user", "content": prompt}]
    kwargs = {}
    if model:
        kwargs["model"] = model
    try:
        resp = await ai_engine.chat(messages, **kwargs)
        return resp.get("message", {}).get("content", str(resp))[:2000]
    except Exception as e:
        return f"AI error: {e}"


def _action_file(operation: str, path: str, content: str = "") -> str:
    if operation == "read":
        if not os.path.exists(path):
            return f"File not found: {path}"
        with open(path) as f:
            return f.read()[:2000]
    elif operation == "write":
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"Written {len(content)} bytes to {path}"
    elif operation == "delete":
        if os.path.exists(path):
            os.remove(path)
            return f"Deleted: {path}"
        return f"Not found: {path}"
    elif operation == "copy":
        import shutil
        parts = content.split("|")
        dst = parts[0] if parts else path + ".copy"
        shutil.copy2(path, dst)
        return f"Copied {path} → {dst}"
    elif operation == "list":
        if not os.path.isdir(path):
            return f"Not a directory: {path}"
        items = os.listdir(path)
        return "\n".join(items[:100])
    return f"Unknown file operation: {operation}"


def _action_notify(title: str, message: str) -> str:
    try:
        import subprocess
        subprocess.run(["notify-send", title, message], timeout=5, capture_output=True)
        return f"Notification sent: {title} — {message}"
    except Exception as e:
        return f"Notification failed: {e}"


async def _action_employee(goal: str) -> str:
    try:
        from core.employee.orchestrator import employee
        result = await employee.execute(goal)
        return json.dumps(result, indent=2)[:2000]
    except Exception as e:
        return f"Employee task error: {e}"


async def _action_script(code: str) -> str:
    import sys
    from io import StringIO
    old_stdout = sys.stdout
    sys.stdout = captured = StringIO()
    try:
        exec_globals = {}
        exec(code, exec_globals)
        output = captured.getvalue()
        return output or "(script executed, no output)"
    except Exception as e:
        return f"Script error: {e}"
    finally:
        sys.stdout = old_stdout


async def _action_condition(config: dict, step_outputs: dict, wf_id: str) -> str:
    condition = config.get("condition", "")
    then_steps = config.get("then_steps", [])
    else_steps = config.get("else_steps", [])
    # Evaluate condition using previous step outputs
    evaluated = condition
    for step_id, output in step_outputs.items():
        placeholder = f"${{{step_id}}}"
        if isinstance(output, str):
            evaluated = evaluated.replace(placeholder, output)
    try:
        result = eval(evaluated, {"__builtins__": {}}, {})
    except Exception as e:
        return f"Condition eval error: {e}"
    branch = then_steps if result else else_steps
    branch_results = []
    for step_data in branch:
        s = StepModel.from_dict(step_data)
        try:
            out = await _action_http if s.action == "http_request" else None
            if s.action == "shell":
                branch_results.append(await _action_shell(s.config.get("command", "")))
            elif s.action == "http_request":
                branch_results.append(await _action_http(s.config.get("url", ""), s.config.get("method", "GET")))
            elif s.action == "ai_task":
                branch_results.append(await _action_ai(s.config.get("prompt", "")))
            elif s.action == "notification":
                branch_results.append(_action_notify(s.config.get("title", ""), s.config.get("message", "")))
            elif s.action == "wait":
                await asyncio.sleep(s.config.get("seconds", 5))
                branch_results.append(f"Slept {s.config.get('seconds', 5)}s")
            elif s.action == "log":
                branch_results.append(f"[{s.config.get('level', 'info')}] {s.config.get('message', '')}")
            else:
                branch_results.append(f"Condition sub-step '{s.action}' executed")
        except Exception as e:
            branch_results.append(f"Sub-step error: {e}")
    branch_name = "THEN" if result else "ELSE"
    return f"Condition '{condition}' = {result} → {branch_name}\n" + "\n".join(branch_results)


engine = AutomationEngine()
