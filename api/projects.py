"""Projects API — create, edit, import, manage code projects."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.projects import project_manager, PROJECT_TEMPLATES
from core.projects.process import process_manager
from core.projects.agent import ProjectAgent

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProject(BaseModel):
    name: str
    template: str = "blank"
    description: str = ""
    framework: str = ""
    language: str = ""
    save_to: str = ""


class UpdateProject(BaseModel):
    project_id: str
    name: str = ""
    description: str = ""
    framework: str = ""
    tags: list[str] | None = None


class ImportProject(BaseModel):
    source_path: str
    name: str = ""
    description: str = ""


class SaveAsRequest(BaseModel):
    project_id: str
    new_name: str
    new_path: str = ""


class FileWrite(BaseModel):
    project_id: str
    file_path: str
    content: str


class FileMove(BaseModel):
    project_id: str
    from_path: str
    to_path: str


class FileDelete(BaseModel):
    project_id: str
    file_path: str


class CreateDirectory(BaseModel):
    project_id: str
    dir_path: str


class RunServer(BaseModel):
    project_id: str
    command: str


class AskAI(BaseModel):
    project_id: str
    task: str
    agent_id: str = ""


# ── Project CRUD ──

@router.get("/templates")
async def list_templates():
    return {"templates": project_manager.get_templates()}

@router.get("/stats")
async def stats():
    return project_manager.get_stats()

@router.get("")
async def list_projects(query: str = Query("")):
    projects = project_manager.list(query)
    return {"projects": [p.to_dict() for p in projects], "total": len(projects)}


@router.post("/create")
async def create_project(req: CreateProject):
    proj = project_manager.create(
        req.name, req.template, req.description,
        req.framework, req.language, req.save_to,
    )
    return {"status": "created", "project": proj.to_dict()}


@router.put("/update")
async def update_project(req: UpdateProject):
    kwargs = {}
    if req.name:
        kwargs["name"] = req.name
    if req.description:
        kwargs["description"] = req.description
    if req.framework:
        kwargs["framework"] = req.framework
    if req.tags is not None:
        kwargs["tags"] = req.tags

    proj = project_manager.update(req.project_id, **kwargs)
    if not proj:
        return {"error": "Project not found"}, 404
    return {"status": "updated", "project": proj.to_dict()}


@router.get("/scan/vscode")
async def scan_vscode(base_dir: str = Query("")):
    projects = project_manager.scan_vscode_projects(base_dir)
    return {"projects": [p.to_dict() for p in projects], "total": len(projects)}


@router.get("/browse")
async def browse_filesystem(path: str = Query("~")):
    """Browse the filesystem — returns directories and files for project import navigation."""
    import os as _os
    full = _os.path.expanduser(path)
    if not _os.path.exists(full):
        full = _os.path.expanduser("~")
    if not _os.path.isdir(full):
        full = _os.path.dirname(full) or _os.path.expanduser("~")

    parent = _os.path.dirname(full)
    dirs = []
    files = []
    try:
        for entry in _os.scandir(full):
            if entry.name.startswith('.'):
                continue
            if entry.is_dir():
                dirs.append({"name": entry.name, "path": entry.path, "is_dir": True})
            else:
                files.append({"name": entry.name, "path": entry.path, "is_dir": False,
                              "size": entry.stat().st_size})
    except PermissionError:
        dirs = []
        files = []

    dirs.sort(key=lambda x: x["name"].lower())
    files.sort(key=lambda x: x["name"].lower())

    return {
        "current": full,
        "parent": parent if parent != full else "",
        "items": dirs,
        "files": files,
        "total_dirs": len(dirs),
        "total_files": len(files),
    }


@router.get("/{project_id}")
async def get_project(project_id: str):
    proj = project_manager.get(project_id)
    if not proj:
        return {"error": "Project not found"}, 404
    return {"project": proj.to_dict()}


@router.delete("/{project_id}")
async def delete_project(project_id: str, delete_files: bool = Query(False)):
    return project_manager.delete(project_id, delete_files)


@router.post("/save-as")
async def save_as(req: SaveAsRequest):
    proj = project_manager.save_as(req.project_id, req.new_name, req.new_path)
    return {"status": "saved", "project": proj.to_dict()}


# ── Import / Scan ──

@router.post("/import")
async def import_project(req: ImportProject):
    proj = project_manager.import_project(req.source_path, req.name, req.description)
    return {"status": "imported", "project": proj.to_dict()}


@router.get("/scan/vscode")
async def scan_vscode(base_dir: str = Query("")):
    projects = project_manager.scan_vscode_projects(base_dir)
    return {"projects": [p.to_dict() for p in projects], "total": len(projects)}


# ── Files ──

@router.get("/{project_id}/files")
async def list_files(project_id: str, path: str = Query("")):
    files = project_manager.list_files(project_id, path)
    return {"project_id": project_id, "path": path, "files": [f.to_dict() for f in files],
            "total": len(files)}


@router.get("/{project_id}/file")
async def read_file(project_id: str, path: str = Query("")):
    return project_manager.read_file(project_id, path)


@router.post("/file/write")
async def write_file(req: FileWrite):
    return project_manager.write_file(req.project_id, req.file_path, req.content)


@router.post("/file/move")
async def move_file(req: FileMove):
    return project_manager.move_file(req.project_id, req.from_path, req.to_path)


@router.delete("/{project_id}/file")
async def delete_file(project_id: str, path: str = Query("")):
    return project_manager.delete_file(project_id, path)


@router.post("/directory/create")
async def create_directory(req: CreateDirectory):
    return project_manager.create_directory(req.project_id, req.dir_path)


# ── AI / Agent ──

@router.post("/ai/ask")
async def ask_ai(req: AskAI):
    try:
        agent = ProjectAgent(req.project_id)
        return await agent.ask(req.task)
    except ValueError as e:
        return {"error": str(e)}, 404


@router.post("/ai/ask-agent")
async def ask_specific_agent(req: AskAI):
    if not req.agent_id:
        return {"error": "agent_id is required"}, 400
    try:
        agent = ProjectAgent(req.project_id)
        return await agent.ask_agent(req.agent_id, req.task)
    except ValueError as e:
        return {"error": str(e)}, 404


# ── Server / Dev Commands ──

@router.post("/server/run")
async def run_server(req: RunServer):
    proj = project_manager.get(req.project_id)
    if not proj:
        return {"error": "Project not found"}, 404
    return await process_manager.start(req.project_id, req.command, proj.path)


@router.post("/server/stop")
async def stop_server(project_id: str = Query("")):
    return await process_manager.stop(project_id)


@router.get("/server/output")
async def get_output(project_id: str = Query(""), since_line: int = Query(0)):
    return process_manager.get_output(project_id, since_line)


@router.get("/server/status")
async def server_status(project_id: str = Query("")):
    return process_manager.get_status(project_id)


@router.get("/server/presets")
async def get_presets(framework: str = Query("")):
    return {"presets": process_manager.get_presets(framework)}


@router.get("/server/running")
async def list_running():
    return {"servers": process_manager.get_running()}
