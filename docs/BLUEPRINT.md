# Lumina AI Platform — Master Blueprint

> **Version**: 1.0.0  
> **Status**: Production Ready  
> **Updated**: July 2026

---

## Product Definition

**Lumina** is an **AI Automation Platform** that combines conversational AI, workflow automation, browser automation, voice interaction, business tools, and extensibility through plugins. It operates locally, in the cloud, or in hybrid mode with a modular plugin architecture.

### What Lumina Is NOT

- ❌ Just a chatbot
- ❌ Just a desktop assistant
- ❌ Just an API wrapper
- ❌ Just a CRM tool

### What Lumina IS

| + | Windows | + ChatGPT | + VS Code | + Zapier |
|---|---------|-----------|-----------|----------|
| + Chrome Automation | + CRM | + SEO Platform | + Voice Assistant | + Developer SDK |

All inside one unified, modular platform.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Dashboard (React)                     │
│              http://localhost:5173                            │
├─────────────────────────────────────────────────────────────┤
│                    API Layer (FastAPI)                       │
│              http://localhost:8000                            │
├─────────────────────────────────────────────────────────────┤
│                        Kernel                                │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │ Event Bus│    DI    │Scheduler │    Service Registry  │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                        AI Core                              │
│  ┌──────────┬──────────┬──────────┬──────────────────────┐  │
│  │Provider  │  Agents  │  Tools   │    Memory Engine     │  │
│  │Chain (8) │  (19)    │Executor  │  (8 layers)          │  │
│  └──────────┴──────────┴──────────┴──────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Core Services                             │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┬──────┐  │
│  │Voice │Browser│Desktop│Mobile│ CRM  │ SEO  │WhatsApp│ ...│
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────┴──────┘  │
├─────────────────────────────────────────────────────────────┤
│                    Plugins (7 built-in)                      │
│  ┌──────┬──────┬──────┬──────┬──────┬──────┬──────┐        │
│  │SEO   │ CRM  │WA Msg│Email │ Leads│Mktg  │Report│        │
│  └──────┴──────┴──────┴──────┴──────┴──────┴──────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Modes of Operation

| Mode | Description | Ideal For |
|------|-------------|-----------|
| **Desktop** | Runs locally | Personal AI, offline automation, local files |
| **Cloud** | Runs on server | Teams, CRM, business automation, APIs |
| **Hybrid** | Desktop + Cloud cooperate | Local processing + cloud AI |

---

## Core Capabilities

### AI Assistant
Chat naturally, ask questions, generate content, summarize, translate, brainstorm, analyze data, code assistance, draft emails, learn concepts.

### Voice Assistant

```
Mic → AudioRecorder → STTEngine → VoiceController → TTSEngine → Speaker
                           │              │               │
                    Language auto-detect  │        Language-matched voice
                    (Whisper + Unicode)   │        (EdgeTTS / gTTS / Piper)
                                          ▼
                              LLM Intent Parser
                              (category, action, params, confidence)
                                          │
                                          ▼
                              Task Planner → Execute (CRM/SEO/Browser/...)
                                          │
                                          ▼
                              Reply Generator → TTS
```

**Speech-to-Text** — OpenAI Whisper (cloud, 99 languages), FasterWhisper (local), Google STT (cloud). Anti-hallucination filters (confidence + no-speech-prob thresholds). Language auto-detection per utterance.

**Text-to-Speech** — 6-provider fallback chain:
1. **EdgeTTS** (free, no API key, 400+ neural voices, 100+ languages) ← primary
2. **EmotiVoice** (emotional synthesis: happy/sad/angry, local server)
3. **Piper** (fully offline neural TTS, auto-downloads 60MB model)
4. **OpenAI TTS** (cloud, 6 voices)
5. **gTTS** (Google, any language, no API key)
6. **pyttsx3** (offline system TTS)

**45 Languages** — Arabic, Urdu, Hindi, Bengali, Chinese, Filipino, Thai, Japanese, Korean + 37 more. Auto-matched voice per language.

**VoiceController** — Wake word ("Lumina" + 44 translations), 5-second follow-up window, echo detection (N-gram fingerprinting), stop command ("stop/shut up/never mind"), LLM intent parsing, task planning, tool-result digest for small models, confirmation for destructive actions.

**Streaming** — `LiveTranscriber` for real-time mic→text, `StreamSynthesizer`, VAD with `SilenceBuffer` for voice activity detection.

**Dictation Mode** — Push-to-talk hotkey (default Ctrl+Alt), filler word removal, custom dictionary, auto-types into active window via xdotool/ydotool/pyautogui.

**Modules:** `recorder.py`, `stt.py`, `tts.py`, `controller.py`, `languages.py`, `echo.py`, `vad.py`, `streaming.py`, `dictation.py`, `wake_word.py`, `command_router.py`

### Browser Automation
Navigate, click, fill forms, extract data, screenshots, downloads, session management, network interception, DOM manipulation, multi-tab.

### Memory Engine (8 layers)
Working (TTL), Episodic (past runs), Semantic (facts), Short-term (conversation buffer), Long-term (persistent KV), Vector Store (cosine similarity), Embeddings, Search + Recall.

### Business Modules
- **CRM**: Contacts, deals, pipeline stages, analytics
- **SEO**: Site audits, keyword tracking, meta generation, competitor analysis
- **Marketing**: Campaigns, content calendar, multi-channel, analytics
- **Lead Management**: Capture, scoring, tracking, source attribution
- **Reporting**: Reports, charts, CSV/JSON/HTML export

### Plugin System
Discover, load, enable/disable, lifecycle hooks, dependency resolution, package manager.

### Security
PBKDF2 auth, JWT/API key/Master key, RBAC with role inheritance, Fernet encryption, secrets vault, tamper-evident audit chain.

---

## User Roles

| Role | Capabilities |
|------|-------------|
| **Administrator** | System config, users, plugins, security, monitoring |
| **Manager** | Teams, CRM, reports, automation |
| **Standard User** | AI assistant, personal workflows, documents, voice |
| **Developer** | Build plugins, APIs, integrations, custom workflows |

---

## Provider Chain (8 AI Providers)

```
1. Ollama (local — free)           → Always available
2. OpenRouter (free models)        → If Ollama fails
3. Groq (free tier)                → If OpenRouter fails
4. Gemini (free tier)              → If Groq fails
5. DeepSeek (free credits)        → If Gemini fails
6. OpenAI (paid)                   → If DeepSeek fails
7. Cloudflare Workers AI           → If OpenAI fails
8. NVIDIA AI                       → If Cloudflare fails
```

---

## Documentation Volumes

| # | Volume | Status | Description |
|---|--------|--------|-------------|
| 1 | Executive Guide | ✅ | Product vision, editions, licensing, deployment options |
| 2 | User Manual | ✅ | Every feature with step-by-step instructions |
| 3 | Administrator Guide | 🔧 | Installation, config, security, monitoring, backups |
| 4 | Developer Guide | 🔧 | Architecture, DI, Event Bus, plugin APIs, testing |
| 5 | Plugin SDK Guide | ✅ | Build, package, test, publish plugins |
| 6 | API Reference | ✅ | All endpoints, auth, request/response examples |
| 7 | Deployment Guide | ✅ | Local, Docker, cloud, updates, scaling |
| 8 | Architecture Reference | 🔧 | Module interactions, lifecycle, data flow |
| 9 | Troubleshooting Guide | 🔧 | Common issues, diagnostics, logging, recovery |
| 10 | Security Guide | ✅ | Identity, permissions, secrets, auditing |

---

## Tech Stack

### Backend
- **Python 3.12+** — Core language
- **FastAPI** — REST API framework
- **Playwright** — Browser automation
- **Pydantic** — Settings + validation
- **httpx** — Async HTTP client
- **pytest** — Testing (1112+ tests)

### Frontend
- **React 19** — UI framework
- **TypeScript 6** — Type safety
- **Tailwind CSS v4** — Styling
- **Vite 8** — Build tool
- **lucide-react** — Icons
- **recharts** — Charts

### Infrastructure
- **Docker** — Containerization
- **Docker Compose** — Multi-service orchestration
- **Nginx** — Reverse proxy
- **GitHub Actions** — CI/CD

---

## Project Stats

| Metric | Value |
|--------|-------|
| Python files | 239 |
| TypeScript files | 16 |
| Core modules | 20 |
| Built-in plugins | 7 |
| Web dashboard pages | 14 |
| API endpoints | 60+ |
| Tests | 1112+ passing |
| AI providers | 8 |
| Agents | 19 |
| Memory layers | 8 |
