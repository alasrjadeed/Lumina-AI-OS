from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field

import yaml

from core.log import log


@dataclass
class ServiceConfig:
    name: str
    image: str = ""
    build: str = ""
    ports: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    command: str = ""
    restart: str = "unless-stopped"
    replicas: int = 1
    healthcheck: dict | None = None


@dataclass
class ComposeConfig:
    version: str = "3.9"
    services: list[ServiceConfig] = field(default_factory=list)
    networks: list[str] = field(default_factory=lambda: ["lumina-network"])
    volumes: list[str] = field(default_factory=list)


class Compose:
    """Docker Compose file generation and management."""

    def __init__(self, config: ComposeConfig | None = None):
        self.config = config or ComposeConfig()

    def add_service(self, service: ServiceConfig) -> None:
        self.config.services.append(service)

    def generate(self, path: str = "docker-compose.yml") -> str:
        compose = {
            "version": self.config.version,
            "services": {},
        }
        for svc in self.config.services:
            svc_dict: dict = {}
            if svc.image:
                svc_dict["image"] = svc.image
            if svc.build:
                svc_dict["build"] = svc.build
            if svc.ports:
                svc_dict["ports"] = svc.ports
            if svc.env:
                svc_dict["environment"] = svc.env
            if svc.volumes:
                svc_dict["volumes"] = svc.volumes
            if svc.depends_on:
                svc_dict["depends_on"] = svc.depends_on
            if svc.command:
                svc_dict["command"] = svc.command
            if svc.restart:
                svc_dict["restart"] = svc.restart
            if svc.healthcheck:
                svc_dict["healthcheck"] = svc.healthcheck
            compose["services"][svc.name] = svc_dict
        if self.config.networks:
            compose["networks"] = {n: {"driver": "bridge"} for n in self.config.networks}
        if self.config.volumes:
            compose["volumes"] = {v: {} for v in self.config.volumes}
        with open(path, "w") as f:
            yaml.dump(compose, f, default_flow_style=False, sort_keys=False)
        log.info("Compose file generated: %s", path)
        return path

    def up(self, path: str = "docker-compose.yml", detach: bool = True,
           build: bool = False) -> dict:
        cmd = ["docker-compose", "-f", path, "up"]
        if detach:
            cmd.append("-d")
        if build:
            cmd.append("--build")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return {"success": result.returncode == 0, "output": result.stdout[-500:],
                    "error": result.stderr[-500:]}
        except FileNotFoundError:
            return {"success": False, "error": "docker-compose not found"}

    def down(self, path: str = "docker-compose.yml", volumes: bool = False) -> dict:
        cmd = ["docker-compose", "-f", path, "down"]
        if volumes:
            cmd.append("-v")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            return {"success": result.returncode == 0, "output": result.stdout.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "docker-compose not found"}

    def ps(self, path: str = "docker-compose.yml") -> list[dict]:
        try:
            result = subprocess.run(
                ["docker-compose", "-f", path, "ps", "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return []
            return [json.loads(line) for line in result.stdout.strip().split("\n") if line]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def logs(self, path: str = "docker-compose.yml", service: str = "",
             tail: int = 100) -> str:
        cmd = ["docker-compose", "-f", path, "logs", "--tail", str(tail)]
        if service:
            cmd.append(service)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            return result.stdout
        except FileNotFoundError:
            return ""

    @staticmethod
    def default_lumina() -> ComposeConfig:
        return ComposeConfig(
            services=[
                ServiceConfig(
                    name="api", build=".", ports=["8000:8000"],
                    env={"LUMINA_ENV": "production"},
                    depends_on=["redis"], healthcheck={
                        "test": ["CMD", "curl", "-f", "http://localhost:8000/health"],
                        "interval": "30s", "timeout": "10s", "retries": 3,
                    },
                ),
                ServiceConfig(
                    name="redis", image="redis:7-alpine", ports=["6379:6379"],
                ),
            ],
            volumes=["redis_data"],
        )
