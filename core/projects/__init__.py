"""Project Manager — create, edit, import, save code projects. Shared between Lumina and VS Code."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import dataclass, field

from core.log import log

PROJECTS_DIR = os.path.expanduser("~/LuminaProjects")


@dataclass
class ProjectFile:
    path: str
    name: str
    type: str = "file"
    size: int = 0
    language: str = ""
    modified: float = 0.0

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "type": self.type,
            "size": self.size,
            "language": self.language,
            "modified": self.modified,
        }


@dataclass
class Project:
    id: str = ""
    name: str = ""
    description: str = ""
    path: str = ""
    framework: str = ""
    language: str = ""
    template: str = ""
    created_at: float = 0.0
    updated_at: float = 0.0
    file_count: int = 0
    total_size_kb: float = 0.0
    tags: list[str] = field(default_factory=list)
    is_vscode: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "path": self.path,
            "framework": self.framework,
            "language": self.language,
            "template": self.template,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "file_count": self.file_count,
            "total_size_kb": self.total_size_kb,
            "tags": self.tags,
            "is_vscode": self.is_vscode,
        }


PROJECT_TEMPLATES = {
    "laravel": {
        "name": "Laravel",
        "description": "PHP web application with Laravel framework",
        "framework": "Laravel",
        "language": "PHP",
        "structure": [
            "app/Models/",
            "app/Http/Controllers/",
            "app/Http/Middleware/",
            "routes/",
            "resources/views/",
            "resources/css/",
            "resources/js/",
            "database/migrations/",
            "database/seeders/",
            "config/",
            "public/",
            "tests/Feature/",
            "tests/Unit/",
        ],
        "files": {
            "composer.json": (
                '{"name": "lumina/laravel-project","require": {"laravel/framework": "^11.0"}}'
            ),
            ".env.example": (
                "APP_NAME=Lumina\nAPP_ENV=local\nAPP_KEY=\nAPP_DEBUG=true\nDB_CONNECTION=sqlite\n"
            ),
            "routes/web.php": (
                "<?php\n\nuse Illuminate\\Support\\Facades\\Route;\n\n"
                "Route::get('/', function () {\n"
                "    return view('welcome');\n});\n"
            ),
            "README.md": "# {{PROJECT_NAME}}\n\nBuilt with Laravel & Lumina AI.\n",
        },
    },
    "react": {
        "name": "React + Vite",
        "description": "React SPA with TypeScript and Vite",
        "framework": "React",
        "language": "TypeScript",
        "structure": [
            "src/components/",
            "src/pages/",
            "src/hooks/",
            "src/api/",
            "src/types/",
            "public/",
        ],
        "files": {
            "package.json": (
                '{"name": "{{PROJECT_NAME}}","private":true,"version":"0.1.0",'
                '"type":"module","scripts":{"dev":"vite","build":"tsc && vite build",'
                '"preview":"vite preview"},"dependencies":{"react":"^18.3",'
                '"react-dom":"^18.3"},"devDependencies":{"@types/react":"^18.3",'
                '"@vitejs/plugin-react":"^4.3","typescript":"^5.5","vite":"^5.4"}}'
            ),
            "vite.config.ts": (
                'import { defineConfig } from "vite";\n'
                'import react from "@vitejs/plugin-react";\n'
                "export default defineConfig({ plugins: [react()] });\n"
            ),
            "tsconfig.json": (
                '{"compilerOptions":{"target":"ES2020","useDefineForClassFields":true,'
                '"lib":["ES2020","DOM","DOM.Iterable"],"module":"ESNext",'
                '"skipLibCheck":true,"moduleResolution":"bundler",'
                '"allowImportingTsExtensions":true,"isolatedModules":true,'
                '"noEmit":true,"jsx":"react-jsx","strict":true},"include":["src"]}'
            ),
            "index.html": (
                '<!doctype html>\n<html lang="en">\n'
                '<head><meta charset="UTF-8"/><meta name="viewport" '
                'content="width=device-width,initial-scale=1"/>'
                "<title>{{PROJECT_NAME}}</title></head>\n"
                '<body><div id="root"></div>'
                '<script type="module" src="/src/main.tsx"></script></body>\n</html>\n'
            ),
            "src/main.tsx": (
                "import React from 'react';\nimport ReactDOM from 'react-dom/client';\n"
                "import App from './App';\n\n"
                "ReactDOM.createRoot(document.getElementById('root')!)"
                ".render(<React.StrictMode><App /></React.StrictMode>);\n"
            ),
            "src/App.tsx": (
                "export default function App() {\n"
                "  return <div className='app'><h1>Welcome</h1></div>;\n}\n"
            ),
            "README.md": "# {{PROJECT_NAME}}\n\nBuilt with React + Vite & Lumina AI.\n",
        },
    },
    "fastapi": {
        "name": "FastAPI",
        "description": "Python API with FastAPI and async support",
        "framework": "FastAPI",
        "language": "Python",
        "structure": [
            "api/",
            "core/",
            "config/",
            "models/",
            "services/",
            "tests/",
        ],
        "files": {
            "main.py": (
                "from fastapi import FastAPI\n\n"
                "app = FastAPI(title='{{PROJECT_NAME}}')\n\n"
                "@app.get('/')\nasync def root():\n"
                "    return {'status': 'ok'}\n"
            ),
            "requirements.txt": (
                "fastapi>=0.110\nuvicorn[standard]\npydantic\npydantic-settings\nhttpx\n"
            ),
            ".env": "APP_NAME={{PROJECT_NAME}}\nDEBUG=true\nHOST=0.0.0.0\nPORT=8000\n",
            "README.md": "# {{PROJECT_NAME}}\n\nBuilt with FastAPI & Lumina AI.\n",
        },
    },
    "nextjs": {
        "name": "Next.js",
        "description": "Full-stack React with Next.js App Router",
        "framework": "Next.js",
        "language": "TypeScript",
        "structure": [
            "src/app/",
            "src/components/",
            "src/lib/",
            "public/",
            "src/app/api/",
        ],
        "files": {
            "package.json": (
                '{"name":"{{PROJECT_NAME}}","version":"0.1.0","private":true,'
                '"scripts":{"dev":"next dev","build":"next build","start":"next start"},'
                '"dependencies":{"next":"^14.2","react":"^18.3","react-dom":"^18.3"},'
                '"devDependencies":{"typescript":"^5.5","@types/node":"^20",'
                '"@types/react":"^18.3"}}'
            ),
            "tsconfig.json": (
                '{"compilerOptions":{"target":"ES2017","lib":["dom","dom.iterable","esnext"],'
                '"allowJs":true,"skipLibCheck":true,"strict":true,"noEmit":true,'
                '"module":"esnext","moduleResolution":"bundler","jsx":"preserve",'
                '"incremental":true,"plugins":[{"name":"next"}],'
                '"paths":{"@/*":["./src/*"]}},"include":["next-env.d.ts","**/*.ts",'
                '"**/*.tsx",".next/types/**/*.ts"],"exclude":["node_modules"]}'
            ),
            "next.config.js": (
                "/** @type {import('next').NextConfig} */\n"
                "const nextConfig = {};\nmodule.exports = nextConfig;\n"
            ),
            "src/app/layout.tsx": (
                "export default function RootLayout({ children }: "
                "{ children: React.ReactNode }) {\n  return (\n"
                "    <html lang='en'><body>{children}</body></html>\n  );\n}\n"
            ),
            "src/app/page.tsx": (
                "export default function Home() {\n  return <main><h1>Welcome</h1></main>;\n}\n"
            ),
            "README.md": "# {{PROJECT_NAME}}\n\nBuilt with Next.js & Lumina AI.\n",
        },
    },
    "blank": {
        "name": "Blank Project",
        "description": "Empty project — start from scratch",
        "framework": "",
        "language": "",
        "structure": [],
        "files": {"README.md": "# {{PROJECT_NAME}}\n"},
    },
}


class ProjectManager:
    """Create, edit, import, save code projects. Shared filesystem = works with VS Code too."""

    def __init__(self):
        os.makedirs(PROJECTS_DIR, exist_ok=True)
        self._projects: dict[str, Project] = {}
        self._load()

    def _index_path(self) -> str:
        return os.path.join(PROJECTS_DIR, "projects.json")

    def _load(self):
        path = self._index_path()
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                for d in data:
                    proj = Project(**{k: d.get(k, "") for k in Project.__dataclass_fields__})
                    self._projects[proj.id] = proj
            except Exception:
                pass

    def _save_index(self):
        with open(self._index_path(), "w") as f:
            json.dump([p.to_dict() for p in self._projects.values()], f, indent=2)

    # ── Project CRUD ──

    def create(
        self,
        name: str,
        template: str = "blank",
        description: str = "",
        framework: str = "",
        language: str = "",
        save_to: str = "",
    ) -> Project:
        import uuid

        pid = uuid.uuid4().hex[:12]
        target_dir = save_to or os.path.join(PROJECTS_DIR, name.replace(" ", "_"))

        os.makedirs(target_dir, exist_ok=True)

        tpl = PROJECT_TEMPLATES.get(template, PROJECT_TEMPLATES["blank"])

        for dir_path in tpl["structure"]:
            os.makedirs(os.path.join(target_dir, dir_path), exist_ok=True)

        for file_path, content in tpl["files"].items():
            full = os.path.join(target_dir, file_path)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            rendered = content.replace("{{PROJECT_NAME}}", name)
            with open(full, "w") as f:
                f.write(rendered)

        proj = Project(
            id=pid,
            name=name,
            description=description,
            path=os.path.abspath(target_dir),
            framework=framework or tpl["framework"],
            language=language or tpl["language"],
            template=template,
            created_at=time.time(),
            updated_at=time.time(),
            tags=[template] if template != "blank" else [],
            file_count=len(tpl["files"]) + len(tpl["structure"]),
            is_vscode=False,
        )

        self._projects[pid] = proj
        self._refresh_stats(proj)
        self._save_index()
        log.info("Project: created '%s' (%s) at %s", name, template, target_dir)
        return proj

    def get(self, project_id: str) -> Project | None:
        return self._projects.get(project_id)

    def list(self, query: str = "") -> list[Project]:
        projects = list(self._projects.values())
        if query:
            q = query.lower()
            projects = [
                p
                for p in projects
                if q in p.name.lower()
                or q in p.framework.lower()
                or q in p.language.lower()
                or any(q in t for t in p.tags)
            ]
        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def update(self, project_id: str, **kwargs) -> Project | None:
        proj = self._projects.get(project_id)
        if not proj:
            return None
        for k, v in kwargs.items():
            if hasattr(proj, k):
                setattr(proj, k, v)
        proj.updated_at = time.time()
        self._save_index()
        return proj

    def delete(self, project_id: str, delete_files: bool = False) -> dict:
        proj = self._projects.pop(project_id, None)
        if not proj:
            return {"error": "Project not found"}

        if delete_files and os.path.exists(proj.path):
            shutil.rmtree(proj.path)

        self._save_index()
        log.info("Project: deleted '%s' (files=%s)", proj.name, delete_files)
        return {"status": "deleted", "project": proj.to_dict()}

    def save_as(self, project_id: str, new_name: str, new_path: str = "") -> Project:
        proj = self._projects.get(project_id)
        if not proj:
            raise ValueError(f"Project not found: {project_id}")

        import uuid

        target_path = new_path or os.path.join(PROJECTS_DIR, new_name.replace(" ", "_"))

        if os.path.exists(proj.path):
            shutil.copytree(proj.path, target_path, dirs_exist_ok=True)

        new_proj = Project(
            id=uuid.uuid4().hex[:12],
            name=new_name,
            description=f"Copy of {proj.name}",
            path=os.path.abspath(target_path),
            framework=proj.framework,
            language=proj.language,
            template=proj.template,
            created_at=time.time(),
            updated_at=time.time(),
            tags=list(proj.tags),
            is_vscode=False,
        )

        self._projects[new_proj.id] = new_proj
        self._refresh_stats(new_proj)
        self._save_index()
        log.info("Project: saved '%s' as '%s' at %s", proj.name, new_name, target_path)
        return new_proj

    # ── Import ──

    def import_project(self, source_path: str, name: str = "", description: str = "") -> Project:
        abs_path = os.path.abspath(os.path.expanduser(source_path))
        if not os.path.exists(abs_path):
            raise ValueError(f"Path does not exist: {abs_path}")

        proj_name = name or os.path.basename(abs_path)

        import uuid

        pid = uuid.uuid4().hex[:12]
        proj = Project(
            id=pid,
            name=proj_name,
            description=description,
            path=abs_path,
            framework=self._detect_framework(abs_path),
            language=self._detect_language(abs_path),
            template="imported",
            created_at=time.time(),
            updated_at=time.time(),
            is_vscode=self._is_vscode_project(abs_path),
        )
        self._refresh_stats(proj)
        self._projects[pid] = proj
        self._save_index()
        log.info("Project: imported '%s' from %s (vscode=%s)", proj_name, abs_path, proj.is_vscode)
        return proj

    def scan_vscode_projects(self, base_dir: str = "") -> list[Project]:
        search_dirs = [
            os.path.expanduser("~/Documents"),
            os.path.expanduser("~/Projects"),
            os.path.expanduser("~/workspace"),
            os.path.expanduser("~/code"),
        ]
        if base_dir:
            search_dirs.insert(0, os.path.expanduser(base_dir))

        found = []
        seen = set(p.path for p in self._projects.values())

        for base in search_dirs:
            if not os.path.exists(base):
                continue
            try:
                for entry in os.scandir(base):
                    if entry.is_dir() and not entry.name.startswith("."):
                        project_path = entry.path
                        if project_path not in seen and os.path.exists(
                            os.path.join(project_path, ".git")
                        ):
                            proj = self.import_project(project_path)
                            found.append(proj)
            except PermissionError:
                continue

        return found

    # ── File Operations ──

    def list_files(self, project_id: str, sub_path: str = "") -> list[ProjectFile]:
        proj = self._projects.get(project_id)
        if not proj:
            return []

        base = os.path.join(proj.path, sub_path) if sub_path else proj.path
        if not os.path.exists(base):
            return []

        files = []
        try:
            for entry in os.scandir(base):
                stat = entry.stat()
                ftype = "directory" if entry.is_dir() else "file"
                ft = ProjectFile(
                    path=os.path.relpath(entry.path, proj.path),
                    name=entry.name,
                    type=ftype,
                    size=stat.st_size if entry.is_file() else 0,
                    language=self._guess_language(entry.name),
                    modified=stat.st_mtime,
                )
                files.append(ft)
        except PermissionError:
            pass

        dirs = sorted([f for f in files if f.type == "directory"], key=lambda f: f.name.lower())
        regular = sorted([f for f in files if f.type == "file"], key=lambda f: f.name.lower())
        return dirs + regular

    def read_file(self, project_id: str, file_path: str) -> dict:
        proj = self._projects.get(project_id)
        if not proj:
            return {"error": "Project not found"}

        full = os.path.join(proj.path, file_path)
        if not os.path.exists(full) or not os.path.isfile(full):
            return {"error": "File not found"}

        try:
            with open(full, errors="replace") as f:
                content = f.read()
            stat = os.stat(full)
            return {
                "path": file_path,
                "content": content,
                "size": stat.st_size,
                "language": self._guess_language(file_path),
                "modified": stat.st_mtime,
            }
        except Exception as e:
            return {"error": str(e)}

    def write_file(self, project_id: str, file_path: str, content: str) -> dict:
        proj = self._projects.get(project_id)
        if not proj:
            return {"error": "Project not found"}

        full = os.path.join(proj.path, file_path)
        os.makedirs(os.path.dirname(full), exist_ok=True)

        try:
            with open(full, "w") as f:
                f.write(content)
            proj.updated_at = time.time()
            self._refresh_stats(proj)
            self._save_index()
            return {"status": "saved", "path": file_path, "size": len(content)}
        except Exception as e:
            return {"error": str(e)}

    def delete_file(self, project_id: str, file_path: str) -> dict:
        proj = self._projects.get(project_id)
        if not proj:
            return {"error": "Project not found"}

        full = os.path.join(proj.path, file_path)
        if not os.path.exists(full):
            return {"error": "File not found"}

        try:
            if os.path.isdir(full):
                shutil.rmtree(full)
            else:
                os.remove(full)
            proj.updated_at = time.time()
            self._refresh_stats(proj)
            self._save_index()
            return {"status": "deleted", "path": file_path}
        except Exception as e:
            return {"error": str(e)}

    def create_directory(self, project_id: str, dir_path: str) -> dict:
        proj = self._projects.get(project_id)
        if not proj:
            return {"error": "Project not found"}

        full = os.path.join(proj.path, dir_path)
        try:
            os.makedirs(full, exist_ok=True)
            proj.updated_at = time.time()
            self._refresh_stats(proj)
            self._save_index()
            return {"status": "created", "path": dir_path}
        except Exception as e:
            return {"error": str(e)}

    def move_file(self, project_id: str, from_path: str, to_path: str) -> dict:
        proj = self._projects.get(project_id)
        if not proj:
            return {"error": "Project not found"}

        full_from = os.path.join(proj.path, from_path)
        full_to = os.path.join(proj.path, to_path)
        if not os.path.exists(full_from):
            return {"error": "Source not found"}

        try:
            os.makedirs(os.path.dirname(full_to), exist_ok=True)
            shutil.move(full_from, full_to)
            proj.updated_at = time.time()
            self._save_index()
            return {"status": "moved", "from": from_path, "to": to_path}
        except Exception as e:
            return {"error": str(e)}

    # ── Helpers ──

    def _refresh_stats(self, proj: Project):
        if not os.path.exists(proj.path):
            return
        file_count = 0
        total_size = 0
        for root, dirs, files in os.walk(proj.path):
            for fn in files:
                fp = os.path.join(root, fn)
                try:
                    total_size += os.path.getsize(fp)
                    file_count += 1
                except OSError:
                    pass
        proj.file_count = file_count
        proj.total_size_kb = round(total_size / 1024, 2)

    def _detect_framework(self, path: str) -> str:
        checks = {
            "composer.json": "PHP/Laravel"
            if self._file_contains(os.path.join(path, "composer.json"), "laravel")
            else "PHP",
            "package.json": self._detect_js_framework(path),
            "requirements.txt": "Python"
            if self._file_contains(os.path.join(path, "requirements.txt"), "fastapi")
            else "Python",
            "Cargo.toml": "Rust",
            "go.mod": "Go",
        }
        for filename, fw in checks.items():
            if os.path.exists(os.path.join(path, filename)):
                return fw
        return ""

    def _detect_js_framework(self, path: str) -> str:
        pkg = os.path.join(path, "package.json")
        if not os.path.exists(pkg):
            return ""
        content = self._read_text(pkg)
        if "next" in content:
            return "Next.js"
        if "react" in content and "vite" in content:
            return "React + Vite"
        if "vue" in content:
            return "Vue"
        if "angular" in content:
            return "Angular"
        if "express" in content:
            return "Express"
        return "JavaScript/TypeScript"

    def _detect_language(self, path: str) -> str:
        exts = {
            "php": 0,
            "py": 0,
            "ts": 0,
            "js": 0,
            "rs": 0,
            "go": 0,
            "java": 0,
            "kt": 0,
            "swift": 0,
            "dart": 0,
            "cs": 0,
            "cpp": 0,
            "c": 0,
        }
        for root, dirs, files in os.walk(path):
            for fn in files:
                ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
                if ext in exts:
                    exts[ext] += 1
        if not any(exts.values()):
            return ""
        best = max(exts, key=lambda k: exts.get(k, 0))
        lang_map = {
            "php": "PHP",
            "py": "Python",
            "ts": "TypeScript",
            "js": "JavaScript",
            "rs": "Rust",
            "go": "Go",
            "java": "Java",
            "kt": "Kotlin",
            "swift": "Swift",
            "dart": "Dart",
            "cs": "C#",
            "cpp": "C++",
            "c": "C",
        }
        result: str | None = lang_map.get(best)
        return result or best

    def _is_vscode_project(self, path: str) -> bool:
        return os.path.exists(os.path.join(path, ".vscode"))

    def _guess_language(self, filename: str) -> str:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        lang_map = {
            "py": "python",
            "js": "javascript",
            "ts": "typescript",
            "tsx": "tsx",
            "jsx": "jsx",
            "vue": "vue",
            "php": "php",
            "rs": "rust",
            "go": "go",
            "java": "java",
            "kt": "kotlin",
            "swift": "swift",
            "dart": "dart",
            "cs": "csharp",
            "cpp": "cpp",
            "c": "c",
            "h": "c",
            "css": "css",
            "scss": "scss",
            "html": "html",
            "json": "json",
            "xml": "xml",
            "yaml": "yaml",
            "yml": "yaml",
            "md": "markdown",
            "sql": "sql",
            "sh": "bash",
            "bat": "bash",
            "dockerfile": "dockerfile",
            "toml": "toml",
            "env": "plaintext",
            "gitignore": "plaintext",
        }
        return lang_map.get(ext, "")

    def _file_contains(self, path: str, text: str) -> bool:
        return text in self._read_text(path)

    def _read_text(self, path: str) -> str:
        try:
            with open(path, errors="replace") as f:
                return f.read()
        except Exception:
            return ""

    def get_templates(self) -> list[dict]:
        return [
            {
                "id": tid,
                "name": t["name"],
                "description": t["description"],
                "framework": t["framework"],
                "language": t["language"],
            }
            for tid, t in PROJECT_TEMPLATES.items()
        ]

    def get_stats(self) -> dict:
        return {
            "total_projects": len(self._projects),
            "by_framework": {
                p.framework: sum(1 for x in self._projects.values() if x.framework == p.framework)
                for p in self._projects.values()
            },
            "vscode_projects": sum(1 for p in self._projects.values() if p.is_vscode),
            "total_files": sum(p.file_count for p in self._projects.values()),
        }


project_manager = ProjectManager()
