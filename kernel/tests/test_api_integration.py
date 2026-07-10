"""Integration-style tests for API endpoints using FastAPI TestClient."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


class TestSystemAPI:
    def test_health(self):
        resp = client.get("/system/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data

    def test_config(self):
        resp = client.get("/system/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "app_name" in data

    def test_root(self):
        resp = client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data
        assert "version" in data

    def test_kernel_status(self):
        resp = client.get("/kernel/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "services" in data


class TestChatAPI:
    @pytest.mark.skip(reason="Requires live AI provider")
    def test_chat_endpoint(self):
        resp = client.post("/chat", json={"message": "hello", "timeout": 2})
        assert resp.status_code in (200, 422, 500)

    @pytest.mark.skip(reason="Requires live AI provider")
    def test_chat_empty_message(self):
        resp = client.post("/chat", json={"message": ""})
        assert resp.status_code in (200, 422)

    @pytest.mark.skip(reason="Requires live AI provider")
    def test_history(self):
        resp = client.get("/chat/history?limit=5")
        assert resp.status_code == 200


class TestCodeAPI:
    @pytest.mark.skip(reason="Requires live AI provider")
    def test_generate(self):
        resp = client.post(
            "/code/generate",
            json={
                "description": "print hello world",
                "language": "python",
            },
        )
        assert resp.status_code in (200, 422)
        if resp.status_code == 200:
            assert "code" in resp.json()

    @pytest.mark.skip(reason="Requires live AI provider")
    def test_generate_missing_description(self):
        resp = client.post("/code/generate", json={"language": "python"})
        assert resp.status_code in (200, 422)

    @pytest.mark.skip(reason="Requires live AI provider")
    def test_review(self):
        resp = client.post(
            "/code/review",
            json={
                "description": "def add(a, b): return a + b",
                "language": "python",
            },
        )
        assert resp.status_code in (200, 422)


class TestAgentsAPI:
    def test_list_agents(self):
        resp = client.get("/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents" in data

    def test_agent_categories(self):
        resp = client.get("/agents/categories")
        assert resp.status_code == 200

    def test_run_agent_missing_params(self):
        resp = client.post("/agents/run", json={})
        assert resp.status_code in (200, 422)


class TestCRMAPI:
    def test_summary(self):
        resp = client.get("/crm/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_deals" in data

    def test_list_contacts(self):
        resp = client.get("/crm/contacts")
        assert resp.status_code == 200

    def test_add_contact(self):
        resp = client.post(
            "/crm/contacts",
            json={
                "name": "Test User",
                "email": "test@example.com",
            },
        )
        assert resp.status_code == 200

    def test_list_deals(self):
        resp = client.get("/crm/deals")
        assert resp.status_code == 200

    def test_add_deal(self):
        resp = client.post(
            "/crm/deals",
            json={
                "title": "Test Deal",
                "value": 1000,
                "contact_id": "test-contact",
            },
        )
        assert resp.status_code == 200


class TestSEOAPI:
    def test_list_sites(self):
        resp = client.get("/seo/sites")
        assert resp.status_code == 200
        data = resp.json()
        assert "sites" in data

    def test_add_site(self):
        resp = client.post(
            "/seo/sites",
            json={
                "url": "https://example.com",
                "name": "Example",
            },
        )
        assert resp.status_code == 200


class TestDesktopAPI:
    def test_info(self):
        resp = client.get("/desktop/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "os" in data

    def test_list_files(self):
        resp = client.get("/desktop/files?path=.")
        assert resp.status_code == 200


class TestWhatsAppAPI:
    def test_status(self):
        resp = client.get("/whatsapp/status")
        assert resp.status_code == 200


class TestAndroidAPI:
    def test_devices(self):
        resp = client.get("/android/devices")
        assert resp.status_code == 200


class TestCoreAPI:
    @pytest.mark.skip(reason="Requires live AI provider")
    def test_heal(self):
        resp = client.post("/core/heal", json={"task": "list files"})
        assert resp.status_code == 200
        assert "status" in resp.json()
