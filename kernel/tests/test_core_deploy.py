from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

from core.deploy.backups import BackupConfig, Backups
from core.deploy.cicd import CICD, CICDConfig
from core.deploy.compose import Compose, ServiceConfig
from core.deploy.docker import Docker, DockerConfig
from core.deploy.kubernetes import K8sConfig, Kubernetes
from core.deploy.monitoring import Monitoring


class TestDocker:
    def test_generate_dockerfile(self, tmp_path: Path):
        d = Docker()
        path = d.generate_dockerfile(str(tmp_path / "Dockerfile"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "FROM python:3.12-slim" in content
        assert "WORKDIR /app" in content

    def test_custom_config(self):
        config = DockerConfig(base_image="python:3.11", expose_port=8080,
                              entrypoint="python app.py")
        d = Docker(config)
        assert d.config.base_image == "python:3.11"
        assert d.config.expose_port == 8080

    def test_generate_with_env(self, tmp_path: Path):
        config = DockerConfig(env_vars={"MY_VAR": "value"})
        d = Docker(config)
        path = d.generate_dockerfile(str(tmp_path / "Dockerfile"))
        content = Path(path).read_text()
        assert "MY_VAR=value" in content

    def test_build_nodocker(self):
        d = Docker()
        result = d.build_image("test:latest", context="/nonexistent")
        assert not result["success"]

    def test_list_containers_nodocker(self):
        d = Docker()
        containers = d.list_containers()
        assert containers == []

    def test_image_exists_nodocker(self):
        d = Docker()
        assert not d.image_exists("nonexistent:latest")


class TestCompose:
    def test_generate_simple(self, tmp_path: Path):
        c = Compose()
        c.add_service(ServiceConfig(name="web", image="nginx:latest", ports=["80:80"]))
        path = c.generate(str(tmp_path / "docker-compose.yml"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "nginx:latest" in content

    def test_generate_with_healthcheck(self, tmp_path: Path):
        c = Compose()
        c.add_service(ServiceConfig(
            name="api", build=".", ports=["8000:8000"],
            healthcheck={"test": ["CMD", "curl", "-f", "http://localhost:8000/health"]},
        ))
        path = c.generate(str(tmp_path / "compose.yml"))
        content = Path(path).read_text()
        assert "healthcheck" in content

    def test_default_lumina(self):
        config = Compose.default_lumina()
        assert len(config.services) == 2
        assert config.services[0].name == "api"
        assert config.services[1].name == "redis"

    def test_up_nocompose(self):
        c = Compose()
        result = c.up(str(Path("/nonexistent/docker-compose.yml")))
        assert not result["success"]

    def test_down_nocompose(self):
        c = Compose()
        result = c.down(str(Path("/nonexistent/docker-compose.yml")))
        assert not result["success"]

    def test_ps_nocompose(self):
        c = Compose()
        result = c.ps(str(Path("/nonexistent/docker-compose.yml")))
        assert result == []


class TestKubernetes:
    def test_generate_deployment(self, tmp_path: Path):
        k = Kubernetes()
        path = k.generate_deployment(str(tmp_path / "deployment.yml"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "Deployment" in content

    def test_generate_service(self, tmp_path: Path):
        k = Kubernetes()
        path = k.generate_service(str(tmp_path / "service.yml"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "Service" in content

    def test_generate_configmap(self, tmp_path: Path):
        config = K8sConfig(env={"KEY": "VALUE"})
        k = Kubernetes(config)
        path = k.generate_configmap(str(tmp_path / "configmap.yml"))
        assert os.path.exists(path)

    def test_generate_ingress(self, tmp_path: Path):
        config = K8sConfig(ingress_host="myapp.example.com")
        k = Kubernetes(config)
        path = k.generate_ingress(str(tmp_path / "ingress.yml"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "Ingress" in content

    def test_generate_hpa(self, tmp_path: Path):
        k = Kubernetes()
        path = k.generate_hpa(str(tmp_path / "hpa.yml"))
        assert os.path.exists(path)
        content = Path(path).read_text()
        assert "HorizontalPodAutoscaler" in content

    def test_generate_all(self, tmp_path: Path):
        k = Kubernetes()
        files = k.generate_all(str(tmp_path / "k8s"))
        assert len(files) >= 2

    def test_apply_nokubectl(self):
        k = Kubernetes()
        result = k.apply(str(Path("/nonexistent")))
        assert not result["success"]

    def test_default_config(self):
        config = Kubernetes.default_config()
        assert config.name == "lumina"
        assert config.replicas == 2


class TestCICD:
    def test_generate_github(self, tmp_path: Path):
        c = CICD()
        path = c.generate(str(tmp_path))
        assert os.path.exists(path)
        assert ".github" in path

    def test_generate_gitlab(self, tmp_path: Path):
        c = CICD(config=CICDConfig(provider="gitlab"))
        path = c.generate(str(tmp_path))
        assert os.path.exists(path)
        assert ".gitlab-ci.yml" in path

    def test_unsupported_provider(self):
        c = CICD(config=CICDConfig(provider="circleci"))
        with pytest.raises(ValueError):
            c.generate()

    def test_github_workflow_content(self, tmp_path: Path):
        c = CICD()
        path = c.generate(str(tmp_path))
        content = Path(path).read_text()
        assert "Lumina CI" in content
        assert "ubuntu-latest" in content

    def test_gitlab_workflow_content(self, tmp_path: Path):
        c = CICD(config=CICDConfig(provider="gitlab"))
        path = c.generate(str(tmp_path))
        content = Path(path).read_text()
        assert "stages" in content

    def test_run_local(self):
        c = CICD(config=CICDConfig(test_command="echo ok"))
        result = c.run_local("test")
        assert result["success"]

    def test_run_local_unknown(self):
        c = CICD()
        result = c.run_local("nonexistent")
        assert not result["success"]


class TestMonitoring:
    def test_register_and_run_check(self):
        m = Monitoring()
        m.register_check("ping", lambda: True)
        result = asyncio.run(m.run_check("ping"))
        assert result.status == "healthy"

    def test_run_unregistered_check(self):
        m = Monitoring()
        result = asyncio.run(m.run_check("missing"))
        assert result.status == "unknown"

    def test_run_check_failure(self):
        m = Monitoring()
        def failing():
            raise RuntimeError("fail")
        m.register_check("fail", failing)
        result = asyncio.run(m.run_check("fail"))
        assert result.status == "unhealthy"

    def test_get_health(self):
        m = Monitoring()
        health = m.get_health("test")
        assert health.status == "unknown"

    def test_record_and_query_metrics(self):
        m = Monitoring()
        m.record_metric("cpu_usage", 45.2, {"host": "server1"})
        m.record_metric("cpu_usage", 50.1)
        m.record_metric("memory_usage", 1024)
        results = m.query_metrics("cpu_usage")
        assert len(results) == 2
        assert results[0].value == 45.2

    def test_alert_rules(self):
        m = Monitoring()
        m.add_alert_rule("cpu_usage", ">", 90, "critical", "CPU too high")
        m.record_metric("cpu_usage", 95)
        alerts = m.get_alerts()
        assert len(alerts) >= 1

    def test_acknowledge_alert(self):
        m = Monitoring()
        m.add_alert_rule("mem", ">", 1000, "warning")
        m.record_metric("mem", 2000)
        assert m.acknowledge_alert(0)
        assert not m.acknowledge_alert(99)

    def test_summary(self):
        m = Monitoring()
        summary = m.summary()
        assert "healthy_services" in summary

    def test_export_json(self, tmp_path: Path):
        m = Monitoring()
        path = m.export_json(str(tmp_path / "mon.json"))
        assert os.path.exists(path)


class TestBackups:
    def test_create_snapshot(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "file.txt").write_text("hello")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        snap = b.create_snapshot("test_backup", paths=[str(src)])
        assert snap.name == "test_backup"
        assert snap.size > 0

    def test_list_snapshots(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("a")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        b.create_snapshot("s1", paths=[str(src)])
        b.create_snapshot("s2", paths=[str(src)])
        snaps = b.list_snapshots()
        assert len(snaps) == 2

    def test_get_snapshot(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("a")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        b.create_snapshot("get_me", paths=[str(src)])
        snap = b.get_snapshot("get_me")
        assert snap is not None
        assert b.get_snapshot("nonexistent") is None

    def test_restore_snapshot(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "file.txt").write_text("backup content")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        b.create_snapshot("restore_test", paths=[str(src)])
        restore_dir = str(tmp_path / "restored")
        b.restore("restore_test", restore_dir)
        restored_file = os.path.join(restore_dir, "data", "file.txt")
        assert os.path.exists(restored_file), f"Expected {restored_file}"

    def test_delete_snapshot(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("a")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        b.create_snapshot("del_me", paths=[str(src)])
        assert b.delete_snapshot("del_me")
        assert not b.delete_snapshot("nonexistent")

    def test_verify_snapshot(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("stable content")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        b.create_snapshot("verify_me", paths=[str(src)])
        assert b.verify_snapshot("verify_me")
        assert not b.verify_snapshot("nonexistent")

    def test_rotate(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("a")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"), max_snapshots=2)
        b = Backups(config)
        b.create_snapshot("s1", paths=[str(src)])
        b.create_snapshot("s2", paths=[str(src)])
        b.create_snapshot("s3", paths=[str(src)])
        assert len(b.list_snapshots()) <= 2

    def test_on_hook(self, tmp_path: Path):
        src = tmp_path / "data"
        src.mkdir()
        (src / "f.txt").write_text("a")
        config = BackupConfig(backup_dir=str(tmp_path / "backups"))
        b = Backups(config)
        results = []
        b.on("after_backup", lambda s: results.append(s.name))
        b.create_snapshot("hooked", paths=[str(src)])
        assert "hooked" in results

    def test_default_config(self):
        config = Backups.default_config()
        assert config.max_snapshots == 10
        assert len(config.paths) >= 1
