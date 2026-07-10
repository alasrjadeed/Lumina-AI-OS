from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass, field

import yaml

from core.log import log


@dataclass
class K8sConfig:
    name: str = "lumina"
    image: str = "lumina:latest"
    replicas: int = 2
    container_port: int = 8000
    service_port: int = 80
    namespace: str = "default"
    env: dict[str, str] = field(default_factory=dict)
    secrets: list[str] = field(default_factory=list)
    resources: dict | None = None
    ingress_host: str = ""


class Kubernetes:
    """Generate and manage Kubernetes manifests."""

    def __init__(self, config: K8sConfig | None = None):
        self.config = config or K8sConfig()

    def generate_all(self, output_dir: str = "k8s") -> list[str]:
        os.makedirs(output_dir, exist_ok=True)
        files = []
        files.append(self.generate_deployment(os.path.join(output_dir, "deployment.yml")))
        files.append(self.generate_service(os.path.join(output_dir, "service.yml")))
        if self.config.env:
            files.append(self.generate_configmap(os.path.join(output_dir, "configmap.yml")))
        if self.config.ingress_host:
            files.append(self.generate_ingress(os.path.join(output_dir, "ingress.yml")))
        log.info("K8s manifests generated in %s (%d files)", output_dir, len(files))
        return files

    def generate_deployment(self, path: str = "deployment.yml") -> str:
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": self.config.name,
                "namespace": self.config.namespace,
                "labels": {"app": self.config.name},
            },
            "spec": {
                "replicas": self.config.replicas,
                "selector": {"matchLabels": {"app": self.config.name}},
                "template": {
                    "metadata": {"labels": {"app": self.config.name}},
                    "spec": {
                        "containers": [self._container_spec()],
                    },
                },
            },
        }
        with open(path, "w") as f:
            yaml.dump(deployment, f, default_flow_style=False)
        return path

    def generate_service(self, path: str = "service.yml") -> str:
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": self.config.name, "namespace": self.config.namespace},
            "spec": {
                "selector": {"app": self.config.name},
                "ports": [
                    {
                        "protocol": "TCP",
                        "port": self.config.service_port,
                        "targetPort": self.config.container_port,
                    }
                ],
                "type": "ClusterIP",
            },
        }
        with open(path, "w") as f:
            yaml.dump(service, f, default_flow_style=False)
        return path

    def generate_configmap(self, path: str = "configmap.yml") -> str:
        cm = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {"name": f"{self.config.name}-config", "namespace": self.config.namespace},
            "data": self.config.env,
        }
        with open(path, "w") as f:
            yaml.dump(cm, f, default_flow_style=False)
        return path

    def generate_ingress(self, path: str = "ingress.yml") -> str:
        ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": self.config.name, "namespace": self.config.namespace},
            "spec": {
                "rules": [
                    {
                        "host": self.config.ingress_host,
                        "http": {
                            "paths": [
                                {
                                    "path": "/",
                                    "pathType": "Prefix",
                                    "backend": {
                                        "service": {
                                            "name": self.config.name,
                                            "port": {"number": self.config.service_port},
                                        },
                                    },
                                }
                            ],
                        },
                    }
                ],
            },
        }
        with open(path, "w") as f:
            yaml.dump(ingress, f, default_flow_style=False)
        return path

    def generate_hpa(
        self,
        path: str = "hpa.yml",
        min_replicas: int = 2,
        max_replicas: int = 10,
        cpu_percent: int = 70,
    ) -> str:
        hpa = {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": self.config.name, "namespace": self.config.namespace},
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": self.config.name,
                },
                "minReplicas": min_replicas,
                "maxReplicas": max_replicas,
                "metrics": [
                    {
                        "type": "Resource",
                        "resource": {
                            "name": "cpu",
                            "target": {"type": "Utilization", "averageUtilization": cpu_percent},
                        },
                    }
                ],
            },
        }
        with open(path, "w") as f:
            yaml.dump(hpa, f, default_flow_style=False)
        return path

    def apply(self, file_or_dir: str = "k8s") -> dict:
        try:
            result = subprocess.run(
                ["kubectl", "apply", "-f", file_or_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {"success": result.returncode == 0, "output": result.stdout.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "kubectl not found"}

    def delete(self, file_or_dir: str = "k8s") -> dict:
        try:
            result = subprocess.run(
                ["kubectl", "delete", "-f", file_or_dir],
                capture_output=True,
                text=True,
                timeout=120,
            )
            return {"success": result.returncode == 0, "output": result.stdout.strip()}
        except FileNotFoundError:
            return {"success": False, "error": "kubectl not found"}

    def get_status(self) -> list[dict]:
        try:
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", self.config.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            return [
                {
                    "name": item["metadata"]["name"],
                    "status": item["status"]["phase"],
                    "node": item["spec"].get("nodeName", ""),
                }
                for item in data.get("items", [])
            ]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _container_spec(self) -> dict:
        container = {
            "name": self.config.name,
            "image": self.config.image,
            "ports": [{"containerPort": self.config.container_port}],
        }
        if self.config.env:
            container["envFrom"] = [{"configMapRef": {"name": f"{self.config.name}-config"}}]
        if self.config.resources:
            container["resources"] = self.config.resources
        if self.config.secrets:
            container["envFrom"] = container.get("envFrom", []) + [
                {"secretRef": {"name": s}} for s in self.config.secrets
            ]
        container.setdefault("envFrom", [])
        return container

    @staticmethod
    def default_config() -> K8sConfig:
        return K8sConfig(
            name="lumina",
            image="lumina:latest",
            replicas=2,
            env={"LUMINA_ENV": "production"},
            ingress_host="lumina.example.com",
            resources={
                "requests": {"cpu": "250m", "memory": "256Mi"},
                "limits": {"cpu": "500m", "memory": "512Mi"},
            },
        )
