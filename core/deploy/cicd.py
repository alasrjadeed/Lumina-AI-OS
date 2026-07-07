from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field

import yaml

from core.log import log


@dataclass
class CICDConfig:
    provider: str = "github"
    python_version: str = "3.12"
    docker_registry: str = ""
    test_command: str = "pytest"
    lint_command: str = "ruff check"
    build_command: str = ""
    deploy_command: str = ""
    branches: list[str] = field(default_factory=lambda: ["main"])
    node_version: str = ""
    extra_steps: list[dict] = field(default_factory=list)


class CICD:
    """CI/CD pipeline configuration generation and execution."""

    def __init__(self, config: CICDConfig | None = None):
        self.config = config or CICDConfig()

    def generate(self, output_dir: str = ".") -> str:
        if self.config.provider == "github":
            return self._generate_github(output_dir)
        elif self.config.provider == "gitlab":
            return self._generate_gitlab(output_dir)
        raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _github_workflow(self) -> dict:
        steps = [
            {"uses": "actions/checkout@v4"},
        ]
        if self.config.node_version:
            steps.append({
                "name": "Setup Node",
                "uses": "actions/setup-node@v4",
                "with": {"node-version": self.config.node_version},
            })
        steps.append({
            "name": "Setup Python",
            "uses": "actions/setup-python@v5",
            "with": {"python-version": self.config.python_version},
        })
        steps.append({
            "name": "Install dependencies",
            "run": "pip install -e .",
        })
        if self.config.lint_command:
            steps.append({"name": "Lint", "run": self.config.lint_command})
        if self.config.test_command:
            steps.append({"name": "Test", "run": self.config.test_command})
        if self.config.build_command:
            steps.append({"name": "Build", "run": self.config.build_command})
        if self.config.docker_registry:
            steps.append({
                "name": "Docker Login",
                "uses": "docker/login-action@v3",
                "with": {"registry": self.config.docker_registry},
            })
            steps.append({
                "name": "Build and push",
                "uses": "docker/build-push-action@v5",
                "with": {
                    "push": True,
                    "tags": f"{self.config.docker_registry}/lumina:${{{{ github.sha }}}}",
                },
            })
        steps.extend(self.config.extra_steps)
        if self.config.deploy_command:
            steps.append({"name": "Deploy", "run": self.config.deploy_command})
        return {
            "name": "Lumina CI",
            "on": {"push": {"branches": self.config.branches}},
            "jobs": {
                "build": {
                    "runs-on": "ubuntu-latest",
                    "steps": steps,
                },
            },
        }

    def _generate_github(self, output_dir: str) -> str:
        workflow = self._github_workflow()
        gh_dir = os.path.join(output_dir, ".github", "workflows")
        os.makedirs(gh_dir, exist_ok=True)
        path = os.path.join(gh_dir, "ci.yml")
        with open(path, "w") as f:
            yaml.dump(workflow, f, default_flow_style=False, sort_keys=False)
        log.info("GitHub Actions workflow generated: %s", path)
        return path

    def _gitlab_config(self) -> dict:
        stages = ["test", "build", "deploy"]
        jobs = {
            "variables": {"PIP_CACHE_DIR": "$CI_PROJECT_DIR/.cache/pip"},
            "cache": {"paths": [".cache/pip"]},
            "stages": stages,
            "lint": {
                "stage": "test",
                "script": self.config.lint_command or "echo 'No lint configured'",
            },
            "test": {
                "stage": "test",
                "script": self.config.test_command or "echo 'No tests configured'",
            },
        }
        if self.config.build_command:
            jobs["build"] = {
                "stage": "build",
                "script": [self.config.build_command],
            }
        if self.config.deploy_command:
            jobs["deploy"] = {
                "stage": "deploy",
                "script": [self.config.deploy_command],
                "only": self.config.branches,
            }
        return jobs

    def _generate_gitlab(self, output_dir: str) -> str:
        config = self._gitlab_config()
        path = os.path.join(output_dir, ".gitlab-ci.yml")
        with open(path, "w") as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        log.info("GitLab CI config generated: %s", path)
        return path

    def run_local(self, step: str = "test") -> dict:
        commands = {
            "test": self.config.test_command,
            "lint": self.config.lint_command,
            "build": self.config.build_command,
        }
        cmd = commands.get(step)
        if not cmd:
            return {"success": False, "error": f"Unknown step: {step}"}
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
            return {"success": result.returncode == 0, "output": result.stdout[-1000:],
                    "error": result.stderr[-500:]}
        except Exception as e:
            return {"success": False, "error": str(e)}
