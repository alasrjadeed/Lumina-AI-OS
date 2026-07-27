# Lumina AI OS

> The World's First Autonomous AI Employee Operating System

[![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/Tests-1112+-passed-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Production%20Ready-success.svg)]()

---

Lumina is a unified AI automation platform that combines conversational AI, workflow automation, browser control, voice interaction, business tools (CRM, SEO, marketing), and an extensible plugin ecosystem — all running locally, in the cloud, or hybrid.

## Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+ (for web UI)
- Ollama (optional, for local AI)

### One-Command Start

```bash
# Backend
cd workspace
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend (optional)
cd lumina-ui && npm install && npm run dev -- --host 0.0.0.0
```

### Docker

```bash
docker compose up -d
```

### CLI

```bash
lumina status
lumina chat "Hello, what can you do?"
lumina code "sort a list" -l python
lumina agent lead_gen "Find restaurants in Bahrain"
```

### URLs
- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health**: http://localhost:8000/system/health

---

## Features

### AI Core
- **8 AI Providers**: Ollama → OpenRouter → Groq → Gemini → DeepSeek → OpenAI → Cloudflare → NVIDIA with automatic fallback
- **19 Specialized Agents**: Software engineer, lead gen, CRM, content writer, designer, and more
- **8-Layer Memory Engine**: Working, Short-Term, Long-Term, Episodic, Semantic, Vector, Embeddings, Recall
- **Self-Healing Loop**: Autonomous PLAN → EXECUTE → VERIFY → FIX → RETRY cycle

### Automation
- **Browser** (Playwright): Navigate, click, fill forms, extract data, screenshots, multi-tab
- **Desktop**: File operations, shell commands, app management, clipboard
- **Android**: ADB device control, APK install, screen tap, logcat
- **WhatsApp**: Cloud API messaging (text, templates, images, documents)
- **Email**: Automated email campaigns and management

### Business Modules
- **CRM Pipeline**: Contacts, deals, stages (Lead → Qualified → Proposal → Negotiation → Closed)
- **SEO Toolkit**: Page analysis, meta generation, keyword tracking, competitor analysis
- **Marketing**: Campaign management, content calendar, multi-channel
- **Lead Management**: Capture, scoring, tracking, source attribution
- **Reporting**: Charts, CSV/JSON/HTML export

### Voice & Vision
- **Voice (Jarvis)**: Wake word detection, STT (Whisper/Google), TTS (ElevenLabs/gTTS)
- **Vision**: Camera abstraction, object detection, face recognition, scene description

### Developer Tools
- **CLI**: 12+ commands (`lumina chat`, `lumina code`, `lumina agent`, etc.)
- **VS Code Extension**: 8 commands with keyboard shortcuts
- **MCP Server**: 14 tools exposed to MCP-compatible AI clients
- **Plugin SDK**: Build, package, and publish custom plugins
- **7 Built-in Plugins**: SEO, CRM, WhatsApp, Email, Leads, Marketing, Reporting

### Security
- PBKDF2-SHA256 password hashing (100k iterations)
- JWT + API key authentication
- RBAC with role inheritance and policies
- Fernet encryption at rest
- Tamper-evident audit chain (SHA-256 chained)

---

## Architecture

```
Interfaces (Dashboard · CLI · VSCode · Flutter · MCP)
         │
    API Layer (FastAPI, 80+ endpoints)
         │
    Kernel (Event Bus · DI · Scheduler · Service Registry · Plugin Loader)
         │
    AI Core (Provider Chain 8x · 19 Agents · Memory Engine 8-layer)
         │
    Core Services (Voice · Browser · Desktop · Android · CRM · SEO · WhatsApp · ...)
         │
    Security (Auth · RBAC · Encryption · Secrets Vault · Audit Chain)
```

---

## Project Structure

```
workspace/
├── main.py                 # FastAPI entry point
├── api/                    # 39 API routers
├── core/                   # Business logic (20+ modules)
│   ├── provider.py         # 8-provider AI chain
│   ├── orchestrator.py     # CEO orchestrator agent
│   ├── agents/             # 19 specialized agents
│   ├── memory/             # 8-layer memory engine
│   ├── browser/            # Playwright automation
│   ├── desktop/            # OS automation
│   ├── voice/              # Voice pipeline (Jarvis)
│   ├── vision/             # Camera + detection
│   ├── security/           # Auth, RBAC, encryption, audit
│   └── ...
├── kernel/                 # Microkernel
│   ├── events/             # Event bus (pub/sub, DLQ, retry)
│   ├── dependency/         # DI container
│   ├── scheduler/          # Job scheduler
│   ├── plugins/            # Plugin system
│   └── tests/              # 69+ test files
├── cli/                    # CLI tool
├── mcp_server/             # MCP server (14 tools)
├── lumina-ui/              # React web dashboard
├── lumina-vscode/          # VS Code extension
├── lumina_app/             # Flutter mobile app
└── jarvis/                 # Voice assistant overlay
```

---

## Documentation

| # | Document | Description |
|---|----------|-------------|
| 0 | [Blueprint.md](Blueprint.md) | High-level vision and architecture |
| 1 | [PRD.md](PRD.md) | Product requirements and user stories |
| 2 | [Architecture.md](Architecture.md) | Detailed system design |
| 3 | [Rules.md](Rules.md) | Coding standards and conventions |
| 4 | [Phases.md](Phases.md) | Development roadmap |
| 5 | [Design.md](Design.md) | UI/UX design system |
| 6 | [Security.md](Security.md) | Security architecture |
| 7 | [README.md](README.md) | This document |
| — | [USER_MANUAL.md](USER_MANUAL.md) | Full user manual |
| — | [BLUEPRINT.md](BLUEPRINT.md) | Original blueprint |

---

## Commands

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Testing
make test          # All kernel tests
make lint          # Ruff check
make fmt           # Ruff format

# Docker
docker compose up -d
docker compose down
docker compose logs -f lumina-api

# CLI
lumina status
lumina chat "Hello"
lumina agent software_engineer "Write a function"
lumina heal "Fix bugs in app.py"
lumina crm summary
lumina files /home
```

---

## Environment Variables

See `.env.example` for the full template.

```env
# Local AI (free)
OLLAMA_BASE_URL=http://localhost:11434

# Cloud AI (optional)
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
DEEPSEEK_API_KEY=sk-...
GROQ_API_KEY=gsk-...

# Security
LUMINA_MASTER_KEY=your-master-key

# WhatsApp
WHATSAPP_API_KEY=...
WHATSAPP_PHONE_ID=...
```

---

## License

MIT — Free for personal and commercial use.

---

## Links

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/system/health
- **Kernel Status**: http://localhost:8000/kernel/status
