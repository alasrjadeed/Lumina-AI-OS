import pytest
import subprocess
import time
import httpx
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

BASE_URL = "http://127.0.0.1:9876"
SERVER_PROCESS = None


@pytest.fixture(scope="session", autouse=True)
def server():
    global SERVER_PROCESS
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_lumina.db"
    SERVER_PROCESS = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "9876"],
        cwd=os.path.join(os.path.dirname(__file__), "../.."),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(30):
        try:
            r = httpx.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.5)
    yield
    SERVER_PROCESS.terminate()
    SERVER_PROCESS.wait()
    try:
        os.remove("test_lumina.db")
    except FileNotFoundError:
        pass


@pytest.fixture
def client():
    return httpx.Client(base_url=BASE_URL, timeout=10)


@pytest.fixture
def auth_headers(client: httpx.Client) -> dict:
    client.post("/api/auth/register", json={"username": "testuser", "email": "test@test.com", "password": "test123"})
    resp = client.post("/api/auth/login", json={"username": "testuser", "password": "test123"})
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


class TestRoot:
    def test_root(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Lumina AI OS"

    def test_health(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"


class TestAuth:
    def test_register(self, client):
        resp = client.post("/api/auth/register", json={"username": "alice", "email": "alice@test.com", "password": "pass123"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["username"] == "alice"

    def test_register_duplicate(self, client):
        client.post("/api/auth/register", json={"username": "bob", "email": "bob@test.com", "password": "pass123"})
        resp = client.post("/api/auth/register", json={"username": "bob", "email": "bob@test.com", "password": "pass123"})
        assert resp.status_code == 400

    def test_login(self, client):
        client.post("/api/auth/register", json={"username": "carol", "email": "carol@test.com", "password": "pass123"})
        resp = client.post("/api/auth/login", json={"username": "carol", "password": "pass123"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_invalid(self, client):
        resp = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
        assert resp.status_code == 401

    def test_auth_me(self, client, auth_headers):
        resp = client.get("/api/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["username"] == "testuser"

    def test_auth_me_no_token(self, client):
        resp = client.get("/api/auth/me")
        assert resp.status_code in (401, 403)  # HTTPBearer returns 401

    def test_refresh(self, client):
        client.post("/api/auth/register", json={"username": "dave", "email": "dave@test.com", "password": "pass123"})
        login = client.post("/api/auth/login", json={"username": "dave", "password": "pass123"})
        refresh = login.json()["refresh_token"]
        resp = client.post("/api/auth/refresh", params={"refresh_token": refresh})
        assert resp.status_code == 200
        assert "access_token" in resp.json()


class TestCore:
    def test_dashboard(self, client):
        resp = client.get("/api/dashboard/")
        assert resp.status_code == 200

    def test_agents(self, client):
        resp = client.get("/api/agents/")
        assert resp.status_code == 200

    def test_settings(self, client, auth_headers):
        resp = client.get("/api/settings/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["app_name"] == "Lumina AI OS"

    def test_settings_update(self, client, auth_headers):
        resp = client.put("/api/settings/", json={"ai_provider": "openai", "llm_temperature": 0.5}, headers=auth_headers)
        assert resp.status_code == 200


class TestExplain:
    def test_explain_text(self, client):
        resp = client.post("/api/explain/text", json={"topic": "Python", "level": "beginner"})
        assert resp.status_code == 200
        assert resp.json()["topic"] == "Python"

    def test_explain_code(self, client):
        resp = client.post("/api/explain/code", json={"code": "print('hello')", "language": "python"})
        assert resp.status_code == 200

    def test_explain_document(self, client):
        resp = client.post("/api/explain/document", json={"content": "Once upon a time...", "filename": "story.txt"})
        assert resp.status_code == 200

    def test_explain_website(self, client):
        resp = client.post("/api/explain/website", json={"url": "https://example.com", "page_content": "Hello world"})
        assert resp.status_code == 200

    def test_explain_report(self, client):
        resp = client.post("/api/explain/report", json={"report_type": "SEO", "report_data": "Traffic: 1000 visitors"})
        assert resp.status_code == 200


class TestReader:
    def test_read_text(self, client):
        resp = client.post("/api/reader/read", json={"text": "Hello Lumina!"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "reading"

    def test_reader_command_pause(self, client):
        resp = client.post("/api/reader/command", json={"command": "pause"})
        assert resp.status_code == 200

    def test_reader_command_continue(self, client):
        resp = client.post("/api/reader/command", json={"command": "continue"})
        assert resp.status_code == 200

    def test_reader_command_faster(self, client):
        resp = client.post("/api/reader/command", json={"command": "faster"})
        assert resp.status_code == 200


class TestVoice:
    def test_speak(self, client):
        resp = client.post("/api/voice/speak", json={"text": "Hello Lumina"})
        assert resp.status_code == 200

    def test_list_voices(self, client):
        resp = client.get("/api/voice/voices")
        assert resp.status_code == 200


class TestTasks:
    def test_create_task(self, client, auth_headers):
        resp = client.post("/api/tasks/", json={"title": "Build app", "priority": "high"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["title"] == "Build app"

    def test_list_tasks(self, client, auth_headers):
        resp = client.get("/api/tasks/", headers=auth_headers)
        assert resp.status_code == 200


class TestMemory:
    def test_store(self, client):
        resp = client.post("/api/memory/", json={"key": "k1", "value": "v1", "namespace": "test"})
        assert resp.status_code == 200


class TestCRM:
    def test_create_lead(self, client, auth_headers):
        resp = client.post("/api/crm/leads", json={"company_name": "Acme Corp", "email": "acme@test.com", "industry": "Tech"}, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        assert resp.json()["status"] == "new"

    def test_list_leads(self, client, auth_headers):
        resp = client.get("/api/crm/leads", headers=auth_headers)
        assert resp.status_code == 200

    def test_generate_proposal(self, client):
        resp = client.post("/api/crm/proposals", json={"client": "Client", "scope": "Website", "pricing": "$5k", "timeline": "2w"})
        assert resp.status_code == 200

    def test_generate_quotation(self, client):
        resp = client.post("/api/crm/quotations", json={"client": "Client", "items": [{"description": "Design", "qty": 1, "price": 1000}]})
        assert resp.status_code == 200

    def test_calendar_create(self, client):
        resp = client.post("/api/crm/calendar", json={"title": "Meeting", "start": "2026-07-06T10:00", "end": "2026-07-06T11:00"})
        assert resp.status_code == 200

    def test_calendar_list(self, client):
        resp = client.get("/api/crm/calendar")
        assert resp.status_code == 200

    def test_followup_schedule(self, client):
        resp = client.post("/api/crm/followups", json={"lead_id": "lead_1", "days": 3, "note": "Follow up"})
        assert resp.status_code == 200

    def test_pipeline(self, client):
        resp = client.get("/api/crm/pipeline")
        assert resp.status_code == 200


class TestWhatsApp:
    def test_send(self, client, auth_headers):
        resp = client.post("/api/whatsapp/send", json={"to": "+97350000000", "message": "Hello!"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "sent" in resp.json()["status"]

    def test_conversations(self, client, auth_headers):
        resp = client.get("/api/whatsapp/conversations", headers=auth_headers)
        assert resp.status_code == 200


class TestEmail:
    def test_send(self, client, auth_headers):
        resp = client.post("/api/email/send", json={"to": "user@test.com", "subject": "Test", "body": "Body"}, headers=auth_headers)
        assert resp.status_code == 200
        assert "sent" in resp.json()["status"]

    def test_draft(self, client):
        resp = client.post("/api/email/draft", json={"prompt": "Follow up with client about proposal", "tone": "professional"})
        assert resp.status_code == 200
        assert "subject" in resp.json()


class TestDesktop:
    def test_list_files(self, client):
        resp = client.get("/api/desktop/files?path=.")
        assert resp.status_code == 200
        assert "items" in resp.json()

    def test_read_file(self, client):
        resp = client.post("/api/desktop/files/read", json={"path": "."})
        assert resp.status_code in (200, 422)

    def test_system_info(self, client):
        resp = client.get("/api/desktop/system")
        assert resp.status_code == 200
        assert "system" in resp.json()


class TestDeveloper:
    def test_generate_code(self, client):
        resp = client.post("/api/developer/generate", json={"specification": "hello world", "language": "python"})
        assert resp.status_code == 200

    def test_terminal_create(self, client):
        resp = client.post("/api/developer/terminal/create?cwd=.")
        assert resp.status_code == 200
        assert "session_id" in resp.json()


class TestBrowser:
    def test_navigate_no_init(self, client):
        resp = client.post("/api/browser/navigate", json={"url": "https://example.com"})
        assert resp.status_code in (200, 500)


class TestMarketing:
    def test_seo_keywords(self, client):
        resp = client.post("/api/marketing/seo/keywords?topic=python&niche=programming")
        assert resp.status_code == 200

    def test_blog(self, client):
        resp = client.post("/api/marketing/content/blog", json={"topic": "AI", "tone": "professional", "length": "short"})
        assert resp.status_code == 200

    def test_social_post(self, client):
        resp = client.post("/api/marketing/content/social", json={"platform": "twitter", "topic": "AI"})
        assert resp.status_code == 200

    def test_logo_design(self, client):
        resp = client.post("/api/marketing/design/logo", json={"brand": "Lumina", "industry": "Tech", "style": "modern"})
        assert resp.status_code == 200

    def test_analytics(self, client):
        resp = client.post("/api/marketing/analytics/report?report_data=Traffic:1000&report_type=seo")
        assert resp.status_code == 200


class TestMonitor:
    def test_monitor(self, client):
        resp = client.get("/monitor")
        assert resp.status_code == 200
        assert "total_requests" in resp.json()
