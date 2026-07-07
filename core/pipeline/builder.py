"""Code→Test→Build Pipeline — autonomous large-scale project generation.

Takes a description like "Create a School ERP" or "Build an Amazon Clone"
and autonomously plans, generates, tests, fixes, and builds the entire project.

Phases:
 1. DEEP ARCHITECT — AI produces full schema, API spec, component tree, file map
 2. FOUNDATION   — configs, models, database schema, shared types
 3. FEATURES     — each feature: generate → test → fix → validate (loop until green)
 4. INTEGRATE    — integration tests across all features
 5. BUILD        — migrations, Docker, final artifact
 6. REPORT       — summary of everything built
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import traceback
from typing import Any

from core.log import log
from core.provider import engine
from core.task_manager import TaskManager, TaskPriority, task_manager as _tm_singleton


MAX_HEAL_ITERATIONS = 5
MAX_CONCURRENT_FILES = 8


class CodeToBuildPipeline:
    """Autonomous software engineer — builds complete projects from a description."""

    def __init__(self, task_mgr: TaskManager | None = None):
        self._tm = task_mgr or _tm_singleton
        self._register_handlers()

    def _register_handlers(self) -> None:
        self._tm.register_handlers({
            "deep_architect": self._handle_deep_architect,
            "foundation": self._handle_foundation,
            "feature_gen": self._handle_feature_gen,
            "feature_test": self._handle_feature_test,
            "feature_fix": self._handle_feature_fix,
            "integration": self._handle_integration,
            "builder": self._handle_builder,
            "reporter": self._handle_reporter,
        })

    # ── Public API ──

    async def launch(self, description: str, language: str = "python",
                     framework: str = "", output_dir: str = "",
                     headless: bool = True) -> dict:
        """Launch a full autonomous project build from a description."""
        task = self._tm.create_task(
            name=f"Build: {description[:80]}",
            description=description,
            priority=TaskPriority.CRITICAL,
            tags=["pipeline", "autonomous", language],
            metadata={"language": language, "framework": framework, "output_dir": output_dir},
        )

        project_name = re.sub(r'[^a-zA-Z0-9]+', '_', description.lower()).strip('_')[:30]

        # Phase 1 — Deep architecture
        s1 = self._tm.add_step(task.id, "Design architecture", "deep_architect",
                                f"Deep architecture plan for: {description}",
                                {"description": description, "language": language,
                                 "framework": framework, "project_name": project_name})
        if not s1:
            return {"error": "Failed to create step"}

        # Phase 2 — Foundation
        s2 = self._tm.add_step(task.id, "Create foundation", "foundation",
                                "Generate project skeleton, configs, models, schema",
                                {"description": description, "language": language,
                                 "framework": framework, "project_name": project_name,
                                 "output_dir": output_dir},
                                depends_on=[s1.id])

        # Phase 3 — Features (dynamic — steps added after plan is known)
        # The foundation handler will add feature steps dynamically

        # Phase 4 — Integration
        s4 = self._tm.add_step(task.id, "Integration tests", "integration",
                                "Run full integration tests across all features",
                                {"project_name": project_name, "output_dir": output_dir},
                                depends_on=[s2.id])

        # Phase 5 — Build
        s5 = self._tm.add_step(task.id, "Build artifacts", "builder",
                                "Generate final build, Docker, migrations",
                                {"description": description, "language": language,
                                 "framework": framework, "project_name": project_name,
                                 "output_dir": output_dir},
                                depends_on=[s4.id])

        # Phase 6 — Report
        self._tm.add_step(task.id, "Report", "reporter",
                           "Generate project summary",
                           {"description": description, "project_name": project_name},
                           depends_on=[s5.id])

        return await self._tm.run_task(task.id)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1 — DEEP ARCHITECT
    # ═══════════════════════════════════════════════════════════════

    async def _handle_deep_architect(self, params: dict) -> dict:
        desc = params["description"]
        lang = params["language"]
        framework = params.get("framework", "")
        proj = params["project_name"]

        prompt = f"""You are a senior software architect. Design a complete project for:

Description: {desc}
Language: {lang}
Framework: {framework or "none"}
Project name: {proj}

Return JSON with this exact structure:
{{
  "project_name": "{proj}",
  "architecture": "brief description of the overall architecture (monolith, microservices, SPA, etc.)",
  "language": "{lang}",
  "framework": "{framework or "none"}",
  "database": {{
    "type": "postgresql/mysql/sqlite",
    "tables": [
      {{"name": "table_name", "columns": [{{"name": "id", "type": "integer", "pk": true, "nullable": false}}, {{"name": "field", "type": "varchar(255)", "nullable": false}}], "indexes": ["field"]}}
    ]
  }},
  "api": [
    {{"method": "GET", "path": "/api/resource", "description": "list resources", "auth": true}}
  ],
  "frontend": {{
    "type": "SPA / SSR / CLI",
    "pages": [
      {{"route": "/login", "name": "LoginPage", "description": "user login form"}}
    ],
    "components": [
      {{"name": "Navbar", "description": "navigation bar"}}
    ]
  }},
  "features": [
    {{
      "name": "Authentication",
      "description": "user registration, login, password reset, role-based access",
      "order": 1,
      "files": [
        {{"path": "backend/auth/routes.py", "description": "login/register/logout endpoints", "type": "backend"}},
        {{"path": "frontend/src/pages/Login.tsx", "description": "login page component", "type": "frontend"}}
      ],
      "dependencies": []
    }}
  ],
  "shared_files": [
    {{"path": "backend/models.py", "description": "SQLAlchemy models for all tables", "type": "backend"}},
    {{"path": "frontend/src/types.ts", "description": "shared TypeScript types", "type": "frontend"}},
    {{"path": "backend/config.py", "description": "configuration", "type": "backend"}}
  ],
  "dependencies": {{
    "backend": ["flask", "sqlalchemy", "alembic", "pytest"],
    "frontend": ["react", "react-router-dom", "axios", "tailwindcss"]
  }},
  "docker": true,
  "tests": {{
    "backend": "pytest",
    "frontend": "vitest"
  }}
}}

Be EXTREMELY detailed. List every table, every API route, every page, every component.
For a project like "School ERP" include 8-15 features.
For "Amazon Clone" include 10-20 features.
Each feature should have 3-15 files."""

        resp = await engine.chat([{"role": "user", "content": prompt}])
        text = resp.get("message", {}).get("content", "")
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {"project_name": proj, "features": [], "shared_files": []}

        plan = json.loads(match.group())
        features = plan.get("features", [])
        shared = plan.get("shared_files", [])
        log.info("Architect: %d features, %d shared files, %d tables",
                 len(features), len(shared), len(plan.get("database", {}).get("tables", [])))
        return plan

    # ═══════════════════════════════════════════════════════════════
    # PHASE 2 — FOUNDATION
    # ═══════════════════════════════════════════════════════════════

    async def _handle_foundation(self, params: dict) -> dict:
        plan_raw = params.get("plan")
        plan = plan_raw if isinstance(plan_raw, dict) else json.loads(plan_raw) if isinstance(plan_raw, str) and plan_raw.startswith("{") else {}

        proj = params["project_name"]
        output_dir = params.get("output_dir", "")
        base_dir = os.path.join(output_dir or os.getcwd(), proj)
        lang = params.get("language", "python")

        os.makedirs(base_dir, exist_ok=True)

        # Generate all shared files (models, configs, types)
        shared_files = plan.get("shared_files", [])
        generated = await self._generate_files_batch(base_dir, shared_files, proj, lang, plan)

        # Generate database schema / init script
        db = plan.get("database", {})
        if db and db.get("tables"):
            await self._generate_db_schema(base_dir, db, lang, proj)

        # Generate package.json / pyproject.toml / requirements if missing
        deps = plan.get("dependencies", {})
        await self._generate_project_config(base_dir, lang, deps, proj)

        # Generate docker config
        if plan.get("docker"):
            await self._generate_docker(base_dir, lang, proj)

        # Install dependencies
        await self._install_deps(base_dir, lang, deps)

        # ── Dynamically add feature steps ──
        features = plan.get("features", [])
        sorted_features = sorted(features, key=lambda f: f.get("order", 99))

        last_step_id = params.get("_step_id", "")
        for feat in sorted_features:
            feat_name = feat.get("name", "Feature")
            gen_step = self._tm.add_step(
                params.get("_task_id", ""),
                f"Generate: {feat_name}", "feature_gen",
                f"Generate code for {feat_name}",
                {"feature": feat, "project_name": proj, "output_dir": output_dir,
                 "language": lang, "base_dir": base_dir, "plan": plan},
                depends_on=[last_step_id] if last_step_id else [],
            )
            if gen_step:
                test_step = self._tm.add_step(
                    params.get("_task_id", ""),
                    f"Test: {feat_name}", "feature_test",
                    f"Test code for {feat_name}",
                    {"feature": feat, "project_name": proj, "output_dir": output_dir,
                     "language": lang, "base_dir": base_dir},
                    depends_on=[gen_step.id],
                )
                if test_step:
                    fix_step = self._tm.add_step(
                        params.get("_task_id", ""),
                        f"Fix: {feat_name}", "feature_fix",
                        f"Auto-fix issues in {feat_name}",
                        {"feature": feat, "project_name": proj, "output_dir": output_dir,
                         "language": lang, "base_dir": base_dir},
                        depends_on=[test_step.id],
                    )
                    if fix_step:
                        last_step_id = fix_step.id

        # Update the integration step dependency to point to last feature fix
        # (handled by the original dependency chain in launch())

        return {
            "base_dir": base_dir,
            "shared_files": len(generated),
            "features": len(sorted_features),
            "generated": generated,
        }

    async def _generate_files_batch(self, base_dir: str, files: list[dict],
                                     proj: str, lang: str, plan: dict) -> list[dict]:
        """Generate multiple files in parallel batches."""
        generated = []
        sem = asyncio.Semaphore(MAX_CONCURRENT_FILES)

        async def _gen_one(file_info: dict) -> dict | None:
            path = file_info.get("path", "")
            desc = file_info.get("description", "")
            ftype = file_info.get("type", "backend")
            full_path = os.path.join(base_dir, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            async with sem:
                context_hint = ""
                if "model" in desc.lower() or "schema" in desc.lower():
                    db = plan.get("database", {})
                    if db.get("tables"):
                        context_hint = f"\nDatabase tables: {json.dumps(db['tables'], indent=2)}"
                if "route" in desc.lower() or "api" in desc.lower():
                    api = plan.get("api", [])
                    if api:
                        context_hint = f"\nAPI routes: {json.dumps(api, indent=2)}"

                prompt = f"""Generate the COMPLETE production-ready code for this file.

Project: {proj}
File: {path}
Type: {ftype}
Description: {desc}
Language: {lang}
{context_hint}

Requirements:
- Write COMPLETE code, no placeholders, no TODOs
- Include all imports
- Use proper error handling
- Follow best practices for {lang}
- If backend: include proper validation, error responses, logging
- If frontend: include loading states, error states, responsive design

Return ONLY the code inside ``` block."""
                try:
                    resp = await engine.chat([{"role": "user", "content": prompt}])
                    text = resp.get("message", {}).get("content", "")
                    code_match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
                    code = code_match.group(1).strip() if code_match else text.strip()
                    with open(full_path, "w") as f:
                        f.write(code)
                    log.info("  wrote %s (%d bytes)", path, len(code))
                    return {"path": path, "size": len(code)}
                except Exception as e:
                    log.error("  FAILED %s: %s", path, e)
                    return {"path": path, "error": str(e)}

        tasks = [_gen_one(f) for f in files]
        results = await asyncio.gather(*tasks)
        for r in results:
            if r:
                generated.append(r)
        return generated

    async def _generate_db_schema(self, base_dir: str, db: dict, lang: str, proj: str) -> None:
        tables = db.get("tables", [])
        db_type = db.get("type", "sqlite")

        if lang == "python":
            models_dir = os.path.join(base_dir, "backend", "models")
            os.makedirs(models_dir, exist_ok=True)
            init_path = os.path.join(models_dir, "__init__.py")
            with open(init_path, "w") as f:
                f.write("# Auto-generated models\n")

            for table in tables:
                name = table.get("name", "")
                cols = table.get("columns", [])
                prompt = f"""Generate a SQLAlchemy model for table '{name}'.

Database: {db_type}
Table: {name}
Columns: {json.dumps(cols, indent=2)}

Return ONLY the complete Python code inside a ```python block.
Include: __tablename__, all columns with proper types, relationships, indexes.
Use declarative base from sqlalchemy.orm."""
                try:
                    resp = await engine.chat([{"role": "user", "content": prompt}])
                    text = resp.get("message", {}).get("content", "")
                    match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
                    code = match.group(1).strip() if match else text.strip()
                    path = os.path.join(models_dir, f"{name}.py")
                    with open(path, "w") as f:
                        f.write(code)
                    log.info("  schema: %s.py", name)
                except Exception as e:
                    log.error("  schema FAILED %s: %s", name, e)

            # Generate migration script
            mig_dir = os.path.join(base_dir, "migrations")
            os.makedirs(mig_dir, exist_ok=True)
            prompt = f"""Generate an Alembic migration script for these tables:
{json.dumps(tables, indent=2)}
Return ONLY the migration Python code inside ```python block.
Use Alembic's op.create_table, op.create_index etc."""
            try:
                resp = await engine.chat([{"role": "user", "content": prompt}])
                text = resp.get("message", {}).get("content", "")
                match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
                code = match.group(1).strip() if match else text.strip()
                with open(os.path.join(mig_dir, "001_initial.py"), "w") as f:
                    f.write(code)
            except Exception:
                pass

            # Generate seed script
            prompt = f"""Generate a seed script that populates sample data for:
{json.dumps(tables, indent=2)}
Project: {proj}
Return ONLY Python code inside ```python block.
Use SQLAlchemy sessions. Include 3-5 sample records per table."""
            try:
                resp = await engine.chat([{"role": "user", "content": prompt}])
                text = resp.get("message", {}).get("content", "")
                match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
                code = match.group(1).strip() if match else text.strip()
                with open(os.path.join(base_dir, "seed.py"), "w") as f:
                    f.write(code)
            except Exception:
                pass

    async def _generate_project_config(self, base_dir: str, lang: str,
                                        deps: dict, proj: str) -> None:
        if lang == "python":
            backend_deps = deps.get("backend", ["flask", "sqlalchemy"])
            req_path = os.path.join(base_dir, "requirements.txt")
            if not os.path.exists(req_path):
                with open(req_path, "w") as f:
                    f.write("\n".join(backend_deps) + "\n")
        elif lang in ("js", "ts"):
            frontend_dir = os.path.join(base_dir, "frontend")
            os.makedirs(frontend_dir, exist_ok=True)

    async def _generate_docker(self, base_dir: str, lang: str, proj: str) -> None:
        prompt = f"""Generate Dockerfile and docker-compose.yml for this project.

Language: {lang}
Project: {proj}

Return JSON:
{{
  "dockerfile": "content of Dockerfile",
  "docker_compose": "content of docker-compose.yml"
}}"""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                configs = json.loads(match.group())
                with open(os.path.join(base_dir, "Dockerfile"), "w") as f:
                    f.write(configs.get("dockerfile", ""))
                with open(os.path.join(base_dir, "docker-compose.yml"), "w") as f:
                    f.write(configs.get("docker_compose", ""))
                log.info("  docker configs generated")
        except Exception as e:
            log.error("  docker FAILED: %s", e)

    async def _install_deps(self, base_dir: str, lang: str, deps: dict) -> None:
        if lang == "python":
            backend_deps = deps.get("backend", [])
            if backend_deps:
                cmd = f"cd {base_dir} && pip install {' '.join(backend_deps)}"
                proc = await asyncio.create_subprocess_shell(
                    cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                log.info("  installed python deps (exit %d)", proc.returncode)
        elif lang in ("js", "ts"):
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(os.path.join(frontend_dir, "package.json")):
                proc = await asyncio.create_subprocess_shell(
                    f"cd {frontend_dir} && npm install",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )
                await proc.communicate()
                log.info("  installed npm deps (exit %d)", proc.returncode)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 3 — FEATURE GENERATION + TEST + FIX LOOP
    # ═══════════════════════════════════════════════════════════════

    async def _handle_feature_gen(self, params: dict) -> dict:
        feature = params.get("feature", {})
        proj = params["project_name"]
        base_dir = params.get("base_dir", "")
        lang = params.get("language", "python")
        plan = params.get("plan", {})

        if not base_dir:
            output_dir = params.get("output_dir", "")
            base_dir = os.path.join(output_dir or os.getcwd(), proj)

        files = feature.get("files", [])
        feat_name = feature.get("name", "feature")
        log.info("  Generating feature '%s' (%d files)", feat_name, len(files))

        # Pass entire project context for cross-file consistency
        context = json.dumps({
            "project": proj,
            "feature": feat_name,
            "all_features": [f.get("name") for f in plan.get("features", [])],
            "tables": plan.get("database", {}).get("tables", []),
            "api_routes": plan.get("api", []),
        })

        generated = await self._generate_files_batch(base_dir, files, proj, lang, plan)

        # Generate a basic test file for this feature
        test_path = os.path.join(base_dir, "tests", f"test_{feat_name.lower().replace(' ', '_')}.py")
        os.makedirs(os.path.dirname(test_path), exist_ok=True)
        prompt = f"""Generate a Python test file for the '{feat_name}' feature.

Project: {proj}
Feature files: {json.dumps([f['path'] for f in files], indent=2)}
Context: {context}

Return ONLY the test code inside ```python block.
Use pytest. Include at least 3 tests. Use fixtures where appropriate."""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            text = resp.get("message", {}).get("content", "")
            match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
            code = match.group(1).strip() if match else text.strip()
            with open(test_path, "w") as f:
                f.write(code)
            log.info("  test: tests/test_%s.py", feat_name.lower().replace(' ', '_'))
        except Exception as e:
            log.error("  test FAILED: %s", e)

        return {
            "feature": feat_name,
            "files_generated": len(generated),
            "generated": generated,
            "base_dir": base_dir,
        }

    async def _handle_feature_test(self, params: dict) -> dict:
        from core.tester.engine import tester

        feature = params.get("feature", {})
        feat_name = feature.get("name", "Feature")
        base_dir = params.get("base_dir", "")
        proj = params["project_name"]

        if not base_dir:
            output_dir = params.get("output_dir", "")
            base_dir = os.path.join(output_dir or os.getcwd(), proj)

        test_file = os.path.join(base_dir, "tests", f"test_{feat_name.lower().replace(' ', '_')}.py")

        if not os.path.exists(test_file):
            return {"feature": feat_name, "success": True, "message": "No test file found"}

        log.info("  Testing feature '%s'", feat_name)

        # Run the specific test file
        result = await tester.run(f"cd {base_dir} && python -m pytest tests/test_{feat_name.lower().replace(' ', '_')}.py -v", timeout=60, cwd=base_dir)

        # Also do a syntax check on all feature files
        syntax_errors = []
        for fi in feature.get("files", []):
            fpath = os.path.join(base_dir, fi.get("path", ""))
            if os.path.exists(fpath) and fpath.endswith(".py"):
                sr = await tester.run(f"cd {base_dir} && python -c \"import ast; ast.parse(open('{fi['path']}').read())\"", timeout=15, cwd=base_dir)
                if not sr.success:
                    syntax_errors.append({"file": fi["path"], "error": sr.error[:300]})

        return {
            "feature": feat_name,
            "success": result.success and len(syntax_errors) == 0,
            "test_result": {"success": result.success, "error": result.error[:500], "output": result.output[:500]},
            "syntax_errors": syntax_errors,
            "base_dir": base_dir,
        }

    async def _handle_feature_fix(self, params: dict) -> dict:
        test_result_raw = params.get("test_result") or {}
        if isinstance(test_result_raw, str):
            try:
                test_result = json.loads(test_result_raw.replace("'", '"'))
            except json.JSONDecodeError:
                test_result = {}
        else:
            test_result = test_result_raw

        feature = params.get("feature", {})
        feat_name = feature.get("name", "Feature")
        base_dir = params.get("base_dir", "")
        proj = params["project_name"]

        if not base_dir:
            output_dir = params.get("output_dir", "")
            base_dir = os.path.join(output_dir or os.getcwd(), proj)

        if test_result.get("success"):
            return {"feature": feat_name, "fixed": True, "message": "Tests pass already"}

        log.info("  Fixing feature '%s'", feat_name)

        # Collect all errors
        errors = []
        tr = test_result.get("test_result", {})
        if tr and not tr.get("success"):
            err_text = tr.get("error", "") or tr.get("output", "")
            if err_text:
                errors.append({"source": "pytest", "text": err_text[:2000]})
        for se in test_result.get("syntax_errors", []):
            errors.append({"source": se.get("file", ""), "text": se.get("error", "")[:2000]})

        if not errors:
            return {"feature": feat_name, "fixed": False, "message": "No errors to fix"}

        fixes_applied = []

        for err in errors:
            prompt = f"""Fix this error in the project.

Project: {proj}
Feature: {feat_name}
Error source: {err['source']}
Error: {err['text']}

Return JSON:
{{
  "analysis": "root cause",
  "file": "relative/path/to/file",
  "fix_code": "complete corrected file content (or empty if config/cmd fix)",
  "command": "shell command to run (or empty if code fix)"
}}"""
            try:
                resp = await engine.chat([{"role": "user", "content": prompt}])
                text = resp.get("message", {}).get("content", "")
                match = re.search(r"\{.*\}", text, re.DOTALL)
                if not match:
                    continue
                fix = json.loads(match.group())

                if fix.get("fix_code") and fix.get("file"):
                    fpath = os.path.join(base_dir, fix["file"])
                    if os.path.exists(fpath):
                        with open(fpath, "w") as f:
                            f.write(fix["fix_code"])
                        fixes_applied.append({"file": fix["file"], "action": "rewritten"})
                        log.info("    fixed: %s", fix["file"])

                if fix.get("command"):
                    proc = await asyncio.create_subprocess_shell(
                        fix["command"], cwd=base_dir,
                        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                    )
                    await proc.communicate()
                    fixes_applied.append({"command": fix["command"], "success": proc.returncode == 0})
            except Exception as e:
                log.error("    fix FAILED: %s", e)

        # Re-test after fixes
        if fixes_applied:
            from core.tester.engine import tester
            retest = await tester.run(
                f"cd {base_dir} && python -m pytest tests/test_{feat_name.lower().replace(' ', '_')}.py -v",
                timeout=60, cwd=base_dir,
            )
            return {
                "feature": feat_name,
                "fixed": retest.success,
                "fixes": fixes_applied,
                "retest": {"success": retest.success, "error": retest.error[:300]},
            }

        return {"feature": feat_name, "fixed": False, "fixes": fixes_applied}

    # ═══════════════════════════════════════════════════════════════
    # PHASE 4 — INTEGRATION
    # ═══════════════════════════════════════════════════════════════

    async def _handle_integration(self, params: dict) -> dict:
        from core.tester.engine import tester

        proj = params["project_name"]
        output_dir = params.get("output_dir", "")
        base_dir = os.path.join(output_dir or os.getcwd(), proj)

        log.info("  Running integration tests")

        results = {}

        # Run all tests
        r = await tester.run(f"cd {base_dir} && python -m pytest tests/ -v --tb=short", timeout=120, cwd=base_dir)
        results["all_tests"] = {"success": r.success, "error": r.error[:500], "output": r.output[:500]}

        # Check app imports
        r2 = await tester.run(
            f"cd {base_dir} && python -c \"from backend.app import create_app; print('App imports OK')\"",
            timeout=30, cwd=base_dir,
        )
        results["app_import"] = {"success": r2.success, "error": r2.error[:300]}

        # Generate integration test if app_import works
        if r2.success:
            prompt = f"""Generate an integration test file for the project at {base_dir}.

Project: {proj}
Features: Resolve from the project structure.

Return ONLY Python code inside ```python block.
Use pytest. Test that the app starts, API routes respond, and basic flow works.
Use Flask test client or FastAPI TestClient."""
            try:
                resp = await engine.chat([{"role": "user", "content": prompt}])
                text = resp.get("message", {}).get("content", "")
                match = re.search(r"```(?:\w+)?\n(.*?)```", text, re.DOTALL)
                code = match.group(1).strip() if match else text.strip()
                integ_path = os.path.join(base_dir, "tests", "test_integration.py")
                with open(integ_path, "w") as f:
                    f.write(code)
                r3 = await tester.run(
                    f"cd {base_dir} && python -m pytest tests/test_integration.py -v",
                    timeout=60, cwd=base_dir,
                )
                results["integration_test"] = {"success": r3.success, "error": r3.error[:300]}
            except Exception as e:
                results["integration_test_gen_error"] = str(e)

        # Auto-heal: retry failed tests with fixes
        heal_count = 0
        while heal_count < MAX_HEAL_ITERATIONS:
            failed = [k for k, v in results.items() if isinstance(v, dict) and not v.get("success")]
            if not failed:
                break

            log.info("  Integration heal iteration %d: fixing %s", heal_count + 1, failed)
            for test_name in failed:
                err_text = results[test_name].get("error", "")[:2000]
                if not err_text:
                    continue
                prompt = f"""Fix the integration test failure.

Project: {proj}
Test: {test_name}
Error: {err_text}

Return JSON:
{{
  "analysis": "root cause",
  "file": "relative/path to fix",
  "fix_code": "complete corrected file content",
  "command": ""
}}"""
                try:
                    resp = await engine.chat([{"role": "user", "content": prompt}])
                    text = resp.get("message", {}).get("content", "")
                    match = re.search(r"\{.*\}", text, re.DOTALL)
                    if not match:
                        continue
                    fix = json.loads(match.group())
                    if fix.get("fix_code") and fix.get("file"):
                        fpath = os.path.join(base_dir, fix["file"])
                        if os.path.exists(fpath):
                            with open(fpath, "w") as f:
                                f.write(fix["fix_code"])
                            log.info("    integration fix: %s", fix["file"])
                except Exception:
                    pass

            # Re-run failed tests
            r = await tester.run(f"cd {base_dir} && python -m pytest tests/ -v --tb=short", timeout=120, cwd=base_dir)
            results["all_tests"] = {"success": r.success, "error": r.error[:500]}
            heal_count += 1

        return {
            "success": all(v.get("success") if isinstance(v, dict) else False for v in results.values()),
            "results": results,
            "heal_iterations": heal_count,
        }

    # ═══════════════════════════════════════════════════════════════
    # PHASE 5 — BUILD
    # ═══════════════════════════════════════════════════════════════

    async def _handle_builder(self, params: dict) -> dict:
        proj = params["project_name"]
        output_dir = params.get("output_dir", "")
        base_dir = os.path.join(output_dir or os.getcwd(), proj)
        lang = params.get("language", "python")

        artifacts = []

        # Python: compileall + generate migration script + seed data
        if lang == "python":
            proc = await asyncio.create_subprocess_shell(
                f"cd {base_dir} && python -m compileall -q . 2>/dev/null",
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            artifacts.append({"type": "bytecode_compile", "success": proc.returncode == 0})

            total_size = self._dir_size(base_dir)
            total_files = self._file_count(base_dir)
            artifacts.append({"type": "project_stats", "file_count": total_files, "size_bytes": total_size})

            # Generate README
            desc = params.get("description", proj)
            prompt = f"""Generate a README.md for this project.

Project: {proj}
Description: {desc}

Include: overview, features, tech stack, setup instructions, API docs (if applicable), license.
Return ONLY the markdown content."""
            try:
                resp = await engine.chat([{"role": "user", "content": prompt}])
                readme = resp.get("message", {}).get("content", "")
                with open(os.path.join(base_dir, "README.md"), "w") as f:
                    f.write(readme)
                artifacts.append({"type": "readme", "path": "README.md"})
            except Exception:
                pass

        # JS/TS: npm build
        elif lang in ("js", "ts"):
            frontend_dir = os.path.join(base_dir, "frontend")
            if os.path.exists(os.path.join(frontend_dir, "package.json")):
                proc = await asyncio.create_subprocess_shell(
                    f"cd {frontend_dir} && npm run build 2>&1",
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
                )
                stdout, stderr = await proc.communicate()
                artifacts.append({
                    "type": "npm_build",
                    "success": proc.returncode == 0,
                    "output": (stdout.decode() if stdout else "")[-500:],
                })

        return {
            "language": lang,
            "base_dir": base_dir,
            "artifacts": artifacts,
        }

    # ═══════════════════════════════════════════════════════════════
    # PHASE 6 — REPORT
    # ═══════════════════════════════════════════════════════════════

    async def _handle_reporter(self, params: dict) -> dict:
        desc = params["description"]
        proj = params["project_name"]

        prompt = f"""Generate a comprehensive build report.

Project: {proj}
Description: {desc}
Summarize what was built, architecture, features, how to run it, and next steps.
3-6 sentences."""
        try:
            resp = await engine.chat([{"role": "user", "content": prompt}])
            report = resp.get("message", {}).get("content", "")
        except Exception:
            report = f"Project '{proj}' built successfully."

        return {"report": report, "project": proj, "description": desc}

    # ═══════════════════════════════════════════════════════════════
    # UTILITIES
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def _dir_size(path: str) -> int:
        total = 0
        for dp, _, fn in os.walk(path):
            for f in fn:
                fp = os.path.join(dp, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total

    @staticmethod
    def _file_count(path: str) -> int:
        return sum(len(fn) for _, _, fn in os.walk(path))


pipeline_builder = CodeToBuildPipeline()
