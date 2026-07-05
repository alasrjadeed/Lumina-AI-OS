# Lumina AI OS

**The World's First Autonomous AI Employee Operating System**

Lumina AI OS is a complete AI Operating System that functions as a digital employee — software engineer, business manager, marketing manager, personal assistant, and more. It continuously plans, executes, tests, learns, and improves across 14 specialized AI agents.

## Architecture

```
┌─────────────────────────────────────┐
│         User Interface              │
│  (Dashboard / Desktop / Mobile)     │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         LUMINA KERNEL               │
│  EventBus · Scheduler · DI/Service  │
│  Plugin Loader · Interfaces         │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│      CEO AI Orchestrator            │
│   (12 specialized AI agents)        │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Services Layer                   │
│  Explain · Reader · Voice · Coding  │
│  Desktop · Browser · CRM · Email    │
│  WhatsApp · Marketing · Analytics   │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│    Memory & Knowledge Layer         │
│  PostgreSQL · ChromaDB · WorkMemory │
└─────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+ (for frontend)
- Docker & Docker Compose (optional, for full stack)

### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn sqlalchemy asyncpg pydantic pydantic-settings \
            python-jose passlib httpx websockets python-multipart python-dotenv

# Run with uvicorn
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 3. Full Stack (Docker)

```bash
docker compose up --build
```

### 4. AI Provider (Local)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama3

# Verify
ollama list
```

## API Endpoints (87 total)

| Module | Endpoints | Prefix |
|--------|-----------|--------|
| Auth | 4 | `/api/auth/` |
| Tasks | 4 | `/api/tasks/` |
| Agents | 3 | `/api/agents/` |
| Dashboard | 2 | `/api/dashboard/` |
| Memory | 4 | `/api/memory/` |
| Explain | 5 | `/api/explain/` |
| Reader | 2 | `/api/reader/` |
| Voice | 7 | `/api/voice/` |
| Settings | 3 | `/api/settings/` |
| Developer | 9 | `/api/developer/` |
| Desktop | 11 | `/api/desktop/` |
| Browser | 6 | `/api/browser/` |
| CRM | 17 | `/api/crm/` |
| Marketing | 10 | `/api/marketing/` |
| WhatsApp | 5 | `/api/whatsapp/` |
| Email | 5 | `/api/email/` |

## AI Agents (12)

| Agent | Role |
|-------|------|
| CEO AI | Master Orchestrator |
| Software Engineer AI | Code generation, review, debug |
| Business Manager AI | CRM, invoices, proposals |
| Marketing AI | Content, social media |
| Explain AI | Topic/code/doc/website/report explanations |
| Reader AI | Document reading (PDF, DOCX, EPUB) |
| Sales Manager AI | Lead management, pipeline |
| CRM Manager AI | Client workspaces, follow-ups |
| SEO Specialist AI | SEO analysis, audits, keywords |
| Browser Operator AI | Web automation (Playwright) |
| Desktop Operator AI | File ops, clipboard, screenshots |

## Project Structure

```
lumina-ai-os/
├── kernel/           # Core: EventBus, Scheduler, DI, Plugins
├── backend/
│   ├── app/
│   │   ├── api/      # 16 API modules
│   │   ├── core/     # Config, DB, Security, Middleware
│   │   ├── models/   # SQLAlchemy models
│   │   └── services/ # 12 service modules
│   └── main.py       # FastAPI entrypoint
├── frontend/         # React + Vite + Tailwind
├── desktop/          # Electron app
├── mobile/           # Flutter app
├── vscode-extension/ # VS Code extension (5 commands)
├── k8s/              # Kubernetes manifests
├── .github/          # CI/CD pipelines
├── docs/             # 8 engineering documents
└── docker-compose.yml
```

## Development

```bash
# Run tests
python -m pytest kernel/tests/ -v

# Check all imports
python -c "import sys; sys.path.insert(0, '.'); from backend.app.core.config import settings; print('OK')"

# Monitor
curl http://localhost:8000/monitor
```

## Sprint Progress

All 14 Sprints complete across 8 phases:

| Phase | Sprints | Status |
|-------|---------|--------|
| Foundation | Sprint 1-4 | ✅ |
| Developer Platform | Sprint 5-6 | ✅ |
| Desktop & Browser | Sprint 7 | ✅ |
| Business Platform | Sprint 8 | ✅ |
| Marketing | Sprint 9 | ✅ |
| Mobile & Desktop Apps | Sprint 10 | ✅ |
| Production Hardening | Sprint 11 | ✅ |
| WhatsApp, Email, CI/CD, VS Code | Sprint 12-14 | ✅ |

See `docs/SPRINTS.md` for details.

## License

Proprietary — All rights reserved.
