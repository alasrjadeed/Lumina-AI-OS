# Lumina AI OS — Project Blueprint

> **Version**: 1.0.0 | **Status**: Production Ready | **Updated**: July 2026

---

## Vision

Lumina is the world's first **Autonomous AI Employee Operating System** — a unified platform that combines conversational AI, workflow automation, browser control, voice interaction, business tools, and an extensible plugin ecosystem into a single, modular system that operates locally, in the cloud, or hybrid.

### What Lumina IS

| AI Desktop | + | ChatGPT | + | VS Code | + | Zapier |
|-------------|---|----------|---|----------|---|---------|
| + Chrome Automation | + CRM | + SEO Platform | + Voice Assistant | + Developer SDK |

### What Lumina is NOT

- Not just a chatbot
- Not just a desktop assistant
- Not just an API wrapper
- Not just a CRM tool

---

## Product Pillars

| Pillar | Description |
|--------|-------------|
| **AI Core** | Multi-provider chain (8 providers), 19 specialized agents, 8-layer memory engine |
| **Automation** | Browser (Playwright), Desktop (OS), Android (ADB), WhatsApp (Cloud API), Email |
| **Business** | CRM pipeline, SEO toolkit, marketing campaigns, lead management, reporting |
| **Voice** | Wake word detection, speech-to-text (Whisper/Google), text-to-speech (ElevenLabs/gTTS) |
| **Extensibility** | 7 built-in plugins, plugin SDK, package manager, sandboxed execution |
| **Interfaces** | Web Dashboard (React), CLI, VS Code Extension, Flutter Mobile, MCP Server |
| **Security** | PBKDF2 auth, JWT/API key, RBAC with inheritance, Fernet encryption, tamper-evident audit |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│              Interfaces (Dashboard · CLI · VSCode · Mobile)  │
├─────────────────────────────────────────────────────────────┤
│                    API Layer (FastAPI)                       │
│              80+ endpoints, 39 routers                       │
├─────────────────────────────────────────────────────────────┤
│                        Kernel                                │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │ Event Bus│    DI    │Scheduler │   Service Registry   │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                        AI Core                              │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │Provider  │  Agents  │  Tools   │   Memory Engine      │  │
│  │Chain (8) │  (19)    │Executor  │  (8 layers)          │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Core Services                             │
│  Voice │Browser│Desktop│Android│ CRM │ SEO │WhatsApp│Writer │
│  Vision│Email  │Social │Market │Audit│Code │Learning│Pipes  │
├─────────────────────────────────────────────────────────────┤
│                    Plugins (7 built-in)                      │
│  SEO · CRM · WhatsApp · Email · Leads · Marketing · Report  │
└─────────────────────────────────────────────────────────────┘
```

---

## Modes of Operation

| Mode | Description | Ideal For |
|------|-------------|-----------|
| **Desktop** | Runs locally, offline-capable | Personal AI, local files, privacy |
| **Cloud** | Runs on server, always-on | Teams, CRM, business automation, APIs |
| **Hybrid** | Desktop + Cloud cooperate | Local processing + cloud AI providers |

---

## AI Provider Chain

```
1. Ollama (local, free)          → Always available
2. OpenRouter (free models)      → If Ollama fails
3. Groq (free tier)              → If OpenRouter fails
4. Gemini (free tier)            → If Groq fails
5. DeepSeek (free credits)       → If Gemini fails
6. OpenAI (paid)                 → If DeepSeek fails
7. Cloudflare Workers AI         → If OpenAI fails
8. NVIDIA AI                     → If Cloudflare fails
```

Automatic fallback with exponential backoff and jitter on timeout, rate limit, credit exhaustion, or API error.

---

## Agent Catalog (19 Total)

### Base Agents (7)
| Agent | Purpose |
|-------|---------|
| `software_engineer` | Write and debug code |
| `web_developer` | Build web applications |
| `business_manager` | Business operations |
| `marketing_manager` | SEO, social media, campaigns |
| `qa_engineer` | Testing and quality |
| `data_analyst` | Data analysis |
| `research_analyst` | Research tasks |

### Specialized Agents (8)
| Agent | Purpose |
|-------|---------|
| `lead_gen` | Find leads, search businesses, enrich data |
| `quotation` | Create quotations and proposals |
| `email_assistant` | Draft, reply, manage emails |
| `call_assistant` | VoIP, call scheduling, notes |
| `customer_success` | Post-sale onboarding, retention |
| `documentation` | Auto-generate documentation |
| `voice_narrator` | Narration scripts, voiceover |
| `designer` | Visual design, branding, UI |

### Content Agents (4)
| Agent | Purpose |
|-------|---------|
| `media_writer` | Blog posts, articles, copywriting |
| `media_video` | Video scripts, storyboards |
| `media_podcast` | Podcast scripts, show notes |
| `content_writer` | Multi-format content creation |

---

## Memory Engine (8 Layers)

| Layer | Type | Purpose |
|-------|------|---------|
| **Working Memory** | TTL-based | Active task context |
| **Short-Term Memory** | Ring buffer | Recent conversation |
| **Long-Term Memory** | Persistent KV | Facts, preferences, learned data |
| **Episodic Memory** | Event log | Past runs, actions, outcomes |
| **Semantic Memory** | Graph | Conceptual relationships, facts |
| **Vector Store** | Cosine similarity | Embedding-based retrieval |
| **Embeddings** | Dense vectors | Semantic similarity |
| **Recall Engine** | Query pipeline | Cross-layer retrieval with ranking |

---

## User Roles

| Role | Capabilities |
|------|-------------|
| **Administrator** | Full system config, users, plugins, security, monitoring |
| **Manager** | Teams, CRM, reports, automation |
| **Standard User** | AI assistant, personal workflows, documents, voice |
| **Developer** | Build plugins, APIs, integrations, custom workflows |

---

## Tech Stack

### Backend
- **Python 3.12+** — Core language
- **FastAPI** — REST API framework (39 routers, 80+ endpoints)
- **Playwright** — Browser automation
- **Pydantic v2** — Settings + validation
- **httpx** — Async HTTP client with connection pooling
- **cryptography (Fernet)** — Encryption at rest
- **pytest** — Testing (1,112+ tests)

### Frontend
- **React 19** — UI framework
- **TypeScript 5.6** — Type safety
- **Tailwind CSS v4** — Utility-first styling
- **Vite 6** — Build tool
- **lucide-react** — Icon library
- **recharts** — Chart components

### Infrastructure
- **Docker + Docker Compose** — Multi-service (API, Ollama, UI)
- **Nginx** — Reverse proxy
- **GitHub Actions** — CI/CD pipeline

### Mobile
- **Flutter (Dart)** — iOS/Android companion app

### Extensions
- **VS Code Extension** — In-IDE AI commands

---

## Project Stats

| Metric | Value |
|--------|-------|
| Python files | 239+ |
| TypeScript files | 16+ |
| Core modules | 20+ |
| API routers | 39 |
| API endpoints | 80+ |
| Built-in plugins | 7 |
| Web dashboard pages | 14+ |
| Test files | 69+ (1,112+ passing) |
| AI providers | 8 |
| Specialized agents | 19 |
| Memory layers | 8 |
| Nodes indexed | 8,536 |
| Edges indexed | 33,592 |

---

## Documentation Map

| # | Document | Description |
|---|----------|-------------|
| 0 | **Blueprint.md** | This document — high-level vision and architecture |
| 1 | **PRD.md** | Product requirements, user stories, success criteria |
| 2 | **Architecture.md** | Detailed system design, modules, data flows |
| 3 | **Rules.md** | Coding standards, conventions, commit rules |
| 4 | **Phases.md** | Development roadmap, milestones, future vision |
| 5 | **Design.md** | UI/UX design system, components, tokens |
| 6 | **Security.md** | Auth, RBAC, encryption, audit, threat model |
| 7 | **README.md** | Quick start, installation, contributing |

---

## License

MIT License — Open source and free for personal and commercial use.
