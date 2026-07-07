from __future__ import annotations

import subprocess
from dataclasses import dataclass, field

from core.log import log


@dataclass
class DockerConfig:
    base_image: str = "python:3.12-slim"
    workdir: str = "/app"
    expose_port: int = 8000
    entrypoint: str = "python -m api.chat"
    env_vars: dict[str, str] = field(default_factory=dict)
    packages: list[str] = field(default_factory=list)
    copy_extra: list[str] = field(default_factory=list)


class Docker:
    """Dockerfile generation, image build, and container management."""

    def __init__(self, config: DockerConfig | None = None):
        self.config = config or DockerConfig()

    def generate_dockerfile(self, path: str = "Dockerfile") -> str:
        lines = [f"FROM {self.config.base_image}", f"WORKDIR {self.config.workdir}"]
        if self.config.packages:
            pkgs = " ".join(self.config.packages)
            lines.append(f"RUN pip install --no-cache-dir {pkgs}")
        lines.append("COPY . .")
        for key, val in self.config.env_vars.items():
            lines.append(f"ENV {key}={val}")
        lines.append(f"EXPOSE {self.config.expose_port}")
        lines.append(f"CMD {self.config.entrypoint}")
        content = "\n".join(lines) + "\n"
        with open(path, "w") as f:
            f.write(content)
        log.info("Dockerfile generated: %s", path)
        return path

    def build_image(self, tag: str = "lumina:latest", dockerfile: str = "Dockerfile",
                    context: str = ".") -> dict:
        try:
            result = subprocess.run(
                ["docker", "build", "-t", tag, "-f", dockerfile, context],
                capture_output=True, text=True, timeout=300,
            )
            ok = result.returncode == 0
            log.info("Docker build %s: %s", "succeeded" if ok else "failed", tag)
            return {"success": ok, "output": result.stdout[-500:], "error": result.stderr[-500:]}
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found"}

    def run_container(self, image: str = "lumina:latest", name: str = "lumina",
                      ports: dict[int, int] | None = None,
                      env: dict[str, str] | None = None,
                      detach: bool = True, remove: bool = True) -> dict:
        cmd = ["docker", "run"]
        if detach:
            cmd.append("-d")
        if remove:
            cmd.append("--rm")
        cmd.extend(["--name", name])
        ports = ports or {self.config.expose_port: self.config.expose_port}
        for host_port, container_port in ports.items():
            cmd.extend(["-p", f"{host_port}:{container_port}"])
        for key, val in (env or {}).items():
            cmd.extend(["-e", f"{key}={val}"])
        cmd.append(image)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            ok = result.returncode == 0
            return {"success": ok, "container_id": result.stdout.strip() if ok else "",
                    "error": result.stderr.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found"}

    def stop_container(self, name: str = "lumina") -> dict:
        try:
            result = subprocess.run(
                ["docker", "stop", name], capture_output=True, text=True, timeout=30,
            )
            return {"success": result.returncode == 0, "output": result.stdout.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found"}

    def list_containers(self, all: bool = False) -> list[dict]:
        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode != 0:
                return []
            lines = result.stdout.strip().split("\n")
            if len(lines) < 2:
                return []
            headers = [h.strip() for h in lines[0].split()]
            containers = []
            for line in lines[1:]:
                parts = line.split(maxsplit=len(headers) - 1)
                containers.append(dict(zip(headers, parts)))
            return containers
        except FileNotFoundError:
            return []

    def image_exists(self, tag: str) -> bool:
        try:
            result = subprocess.run(
                ["docker", "image", "inspect", tag],
                capture_output=True, text=True, timeout=30,
            )
            return result.returncode == 0
        except FileNotFoundError:
            return False

    def push_image(self, tag: str, registry: str = "") -> dict:
        full_tag = f"{registry}/{tag}" if registry else tag
        try:
            result = subprocess.run(
                ["docker", "push", full_tag],
                capture_output=True, text=True, timeout=300,
            )
            return {"success": result.returncode == 0, "output": result.stdout.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "Docker not found"}
