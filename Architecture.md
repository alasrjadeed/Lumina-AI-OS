# Lumina AI OS — Architecture

> **Version**: 1.0.0 | **Status**: Approved | **Updated**: July 2026

---

## 1. High-Level Architecture

Lumina follows a **layered microkernel architecture** with a kernel at the center, core services around it, and an API layer exposing functionality to multiple frontends.

```
┌──────────────────────────────────────────────────────────────────┐
│                        INTERFACES                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────┐ │
│  │Web (React)│ │CLI (Bash)│ │VS Code   │ │Flutter   │ │  MCP  │ │
│  └─────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬───┘ │
├────────┼─────────────┼───────────┼───────────┼───────────┼───────┤
│        └─────────────┴───────────┴─ API LAYER ┴───────────┘      │
│                    FastAPI :8000 (53 routers)                      │
├───────────────────────────────┬──────────────────────────────────┤
│                          KERNEL                                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │Event Bus │ │Services  │ │    DI    │ │  Plugin Loader       │ │
│  │Pub/Sub   │ │Registry  │ │Container │ │  (discovery, sandbox)│ │
│  │Wildcards │ │named reg │ │Singleton │ │  lifecycle, version) │ │
│  │DLQ+Retry │ │          │ │Scoped    │ │                      │ │
│  │History   │ │          │ │Transient │ │                      │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘ │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  Scheduler (delayed, recurring, retryable jobs)              │ │
│  └──────────────────────────────────────────────────────────────┘ │
├───────────────────────────────┬──────────────────────────────────┤
│                          AI CORE                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │Provider  │ │Agents    │ │Tools     │ │  Memory Engine       │ │
│  │Chain     │ │19 agents │ │Executor  │ │  8 layers            │ │
│  │8 models  │ │3 cats    │ │sandboxed │ │  vector + semantic   │ │
│  │fallback  │ │lifecycle │ │          │ │  recall pipeline     │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘ │
├───────────────────────────────┬──────────────────────────────────┤
│                       CORE SERVICES                               │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ │
│  │Voice │Browser│Desktop│Android│ CRM  │ SEO  │WhatsApp│Writer │ │
│  │Vision│Email  │Social │Market │Audit │ Deploy│Learning│Pipes │ │
│  │Code  │Vault  │Tasks  │Project│Test  │Queue │Analytics│Flow │ │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ │
├───────────────────────────────┬──────────────────────────────────┤
│                    SECURITY LAYER                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐ │
│  │  Auth    │ │   RBAC   │ │Encryption│ │  Audit (chained)     │ │
│  │PBKDF2    │ │Inherit   │ │Fernet    │ │  SHA-256 tamper      │ │
│  │JWT/API   │ │Policies  │ │Secrets   │ │  JSON/CSV export     │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘ │
├───────────────────────────────┬──────────────────────────────────┤
│                    PLUGINS (7 built-in)                            │
│  SEO · CRM · WhatsApp · Email · Leads · Marketing · Reporting     │
└───────────────────────────────┴──────────────────────────────────┘
```

---

## 2. Kernel Architecture

The Kernel is the foundation that all Lumina modules depend on. It provides five core services:

### 2.1 Event Bus

Pub/sub event system with:
- **Wildcard topic matching** (`agent.run`, `kernel.*`, `*`)
- **History** for late subscribers (configurable buffer)
- **Dead Letter Queue** (SQLite backend) for failed events
- **Retry** with exponential backoff and max attempts
- **Priority** levels: LOW, NORMAL, HIGH, CRITICAL
- **Built-in middleware**: Logging, Metrics, Validation, Tracing, Rate Limiting, OpenTelemetry

```python
# Subscribe
await event_bus.register(Subscription(topic="agent.run", handler=on_agent_run))

# Publish
await event_bus.publish(Event(name="agent.run", payload={"agent": "lead_gen"}))

# Wildcard
await event_bus.register(Subscription(topic="*", handler=log_all))
```

### 2.2 Service Registry

Named service registration and resolution:

```python
kernel.services.register("ai_engine", engine)
kernel.services.register("browser", browser)
kernel.services.register("crm", crm)
# ... 15+ services registered
```

Services registered at startup in `main.py`:
- `ai_engine`, `memory`, `config`, `automation_engine`
- `form_filler`, `browser`, `desktop`, `android`
- `whatsapp`, `crm`, `seo`, `task_manager`
- `pipeline_builder`, `voice_controller`
- `camera_factory`, `detector_factory`, `describer_factory`, `cortex_factory`
- `brain` (Think → Observe → Command autonomous loop)
- `workflow_store` (n8n template store + execution engine)
- `agents` (all 19 agents merged)

### 2.3 DI Container

Dependency Injection container with:
- **Singleton**: One instance for the app lifetime
- **Scoped**: One instance per scope (e.g., per request)
- **Transient**: New instance every time
- **Decorator-based** registration (`@injectable`, `@singleton`, `@scoped`)
- **Interface-based** resolution
- **Factory** providers

### 2.4 Plugin Loader

Plugin discovery and lifecycle:
- **Discovery**: Scan directories for plugin manifests
- **Validation**: Check manifest structure, version compatibility
- **Loading**: Resolve dependencies, initialize plugins
- **Lifecycle**: `load → enable → disable → unload`
- **Sandbox**: Isolated execution for untrusted plugins
- **Versioning**: SemVer-based compatibility checking

### 2.5 Scheduler

Job scheduling with:
- **Delayed**: Execute after N seconds
- **Recurring**: Execute every N seconds
- **Retryable**: Auto-retry on failure with backoff
- **Job model**: ID, status, attempts, next run, payload

---

## 3. AI Core Architecture

### 3.1 Provider Chain

```
User Request → Provider Chain → [Ollama → OpenRouter → Groq → Gemini → DeepSeek → OpenAI → Cloudflare → NVIDIA]
                                  ↓ (fail)      ↓ (fail)     ↓ (fail)  ↓ (fail)  ↓ (fail)    ↓ (fail)   ↓ (fail)
                              Try next      Try next      Try next  Try next  Try next    Try next   Try next    → Error
```

Key implementation details:
- **Shared HTTP client** with connection pooling (100 max connections, 20 keep-alive)
- **Exponential backoff** with jitter: `delay = min(1.0 * 2^(attempt-1), 10.0) + random(0, delay*0.5)`
- **Max 3 retries** per provider
- **Timeout**: 60s per request
- **Streaming**: SSE parsing for OpenAI-compatible and DeepSeek/Groq/Gemini
- **Provider status**: Health tracking, fallback on error/rate-limit/timeout

### 3.2 Agent System

```
CEO Orchestrator (orchestrator.py)
  ├── Agent Manager (manager.py) ── routes tasks to appropriate agents
  ├── Base Agents (base.py) ─────── software_engineer, web_developer, etc.
  ├── Specialized Agents ────────── lead_gen, quotation, email_assistant, etc.
  └── Content Agents ────────────── media_writer, media_video, content_writer, etc.
```

Agent lifecycle:
1. **OBSERVE** — Parse and understand user request
2. **THINK** — Analyze context and requirements
3. **PLAN** — Break into steps with dependencies
4. **ASSIGN** — Delegate to specialized agents
5. **EXECUTE** — Run the plan
6. **VERIFY** — Check results for quality
7. **REPORT** — Summarize in natural language

### 3.3 Memory Engine

```
┌─────────────────────────────────────────────┐
│              Memory Engine                    │
├─────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Working Mem │  │  Short-Term Memory   │  │
│  │ (TTL, temp) │  │  (ring buffer)       │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Long-Term   │  │  Episodic Memory     │  │
│  │ (persist KV)│  │  (event log)         │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Semantic    │  │  Vector Store        │  │
│  │ (facts,rel) │  │  (cosine similarity) │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Embeddings  │  │  Recall Engine       │  │
│  │ (dense vec) │  │  (cross-layer query) │  │
│  └─────────────┘  └──────────────────────┘  │
│  ┌────────────────────────────────────────┐ │
│  │  Consolidation Engine                  │ │
│  │  (episodic → semantic migration)       │ │
│  └────────────────────────────────────────┘ │
└─────────────────────────────────────────────┘
```

- **Working Memory**: `dict` with TTL per entry, auto-expiry
- **Short-Term Memory**: Ring buffer, last N messages
- **Long-Term Memory**: JSON-persisted key-value store
- **Episodic Memory**: Append-only event log with metadata
- **Semantic Memory**: Subject-predicate-object fact triples
- **Vector Store**: In-memory, cosine similarity search
- **Embeddings**: Dummy provider (extensible to OpenAI/sentence-transformers)
- **Recall Engine**: Queries all layers, merges results, ranks by relevance
- **Consolidation**: Periodically moves important episodic events to semantic memory

---

## 4. Core Service Modules

### 4.1 Voice Module (`core/voice/`)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Recorder   │ →  │  VAD / Wake  │ →  │     STT      │
│  (microphone)│    │  Word Detect │    │  (Whisper/   │
│              │    │  ("Jarvis")  │    │   Google)    │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                    ┌──────────────┐    ┌──────▼───────┐
                    │     TTS      │ ←  │   Command    │
                    │  (ElevenLabs │    │   Router     │
                    │   / gTTS)    │    │              │
                    └──────────────┘    └──────────────┘
```

Files: `recorder.py`, `vad.py`, `wake_word.py`, `stt.py`, `tts.py`, `command_router.py`, `streaming.py`, `dictation.py`, `echo.py`, `languages.py`, `controller.py`

### 4.2 Browser Module (`core/browser/`)

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   Browser    │ →  │     Page     │ →  │     DOM      │
│   Manager    │    │              │    │  Interaction │
└──────────────┘    └──────────────┘    └──────────────┘
       │                                       │
┌──────▼──────┐    ┌──────────────┐    ┌──────▼───────┐
│   Session   │    │   Network    │    │     Form     │
│             │    │ Interception │    │   Filler     │
└──────────────┘    └──────────────┘    └──────────────┘
```

Files: `browser_manager.py`, `page.py`, `dom_interaction.py`, `session.py`, `network.py`, `form_filler.py`, `automation.py`, `tab_manager.py`, `screenshots.py`, `downloads.py`, `finder.py`, `agent.py`, `monitor.py`

### 4.3 Desktop Module (`core/desktop/`)

Files: `os_automation.py`, `app_manager.py`, `window_manager.py`, `clipboard.py`, `notifications.py`, `shortcuts.py`, `settings.py`, `ui.py`, `ui_notifications.py`, `chat.py`, `logs.py`, `plugin_manager.py`

### 4.4 Security Module (`core/security/`)

| File | Purpose |
|------|---------|
| `auth.py` | User authentication, sessions, API keys, PBKDF2 password hashing |
| `authorization.py` | RBAC with role inheritance, policy-based access control |
| `encryption.py` | Symmetric (Fernet) and asymmetric (RSA) encryption, HMAC, hashing |
| `secrets.py` | Secrets vault with encryption at rest, rotation, tagging |
| `audit.py` | Tamper-evident audit chain with SHA-256 chained hashing |

---

## 5. API Layer

### 5.1 Router Map (53 Routers)

| Router | File | Purpose |
|--------|------|---------|
| `chat_router` | `api/chat.py` | Chat with slash commands |
| `system_router` | `api/system.py` | Health, config, kernel status |
| `code_router` | `api/code.py` | Code generation and review |
| `agents_router` | `api/agents.py` | Agent listing and execution |
| `automation_router` | `api/automation.py` | Self-healing, form automation |
| `browser_router` | `api/browser.py` | Browser control |
| `desktop_router` | `api/desktop.py` | Desktop automation |
| `android_router` | `api/android.py` | Android ADB control |
| `whatsapp_router` | `api/whatsapp.py` | WhatsApp messaging |
| `crm_router` | `api/crm.py` | CRM pipeline |
| `seo_router` | `api/seo.py` | SEO analysis |
| `auth_router` | `api/auth.py` | Authentication |
| `vault_router` | `api/vault.py` | Secrets vault |
| `social_router` | `api/social.py` | Social media |
| `writer_router` | `api/writer.py` | Content generation |
| `assistant_router` | `api/assistant.py` | Assistant features |
| `learning_router` | `api/learning.py` | Learning agent |
| `tester_router` | `api/tester.py` | Test runner |
| `queue_router` | `api/queue.py` | Job queue |
| `employee_router` | `api/employee.py` | Employee orchestrator |
| `tasks_router` | `api/tasks.py` | Task management |
| `pipeline_router` | `api/pipeline.py` | Pipeline builder |
| `voice_router` | `api/voice.py` | Voice control |
| `vision_router` | `api/vision.py` | Vision system |
| `coding_agent_router` | `api/coding_agent.py` | Coding agent |
| `email_router` | `api/email.py` | Email automation |
| `marketing_router` | `api/marketing.py` | Marketing campaigns |
| `marketplace_router` | `api/marketplace.py` | Plugin marketplace |
| `analytics_router` | `api/analytics_router.py` | Analytics |
| `test_browser_router` | `api/test_browser.py` | Browser testing |
| `audit_router` | `api/audit_api.py` | Audit logs |
| `core_api_router` | `api/core_api.py` | Core system API |
| `multiagent_router` | `api/multiagent.py` | Multi-agent coordination |
| `projects_router` | `api/projects.py` | Project management |
| `visual_flows_router` | `api/visual_flows.py` | Visual flow editor |
| `skills_router` | `api/skills.py` | Skills management |
| `presets_router` | `api/presets.py` | Presets |
| `connectors_router` | `api/connectors.py` | External connectors |
| `community_skills_router` | `api/community_skills.py` | Community skills |
| `brain_router` | `api/brain.py` | Brain system (Think → Observe → Command) |
| `workflow_editor_router` | `api/workflow_editor.py` | n8n workflow templates + execution engine |

### 5.2 Middleware Stack

```
Request → CORS → Rate Limiter (prod) → Router → Response
```

- **CORS**: Configurable origins via `CORS_ORIGINS` env var
- **Rate Limiter**: 100 requests per 60s window (production only)
- **Auth Middleware**: Token/session/API key validation (on protected routes)

---

## 6. Frontend Architecture

### 6.1 Web Dashboard (`lumina-ui/`)

```
src/
├── App.tsx                     # Root component, routing
├── main.tsx                    # React entry point
├── api.ts                      # API client (axios wrapper)
├── types.ts                    # TypeScript interfaces
├── index.css                   # Tailwind imports + global styles
├── components/
│   ├── Layout.tsx              # Shell: sidebar, header, content
│   └── ui/
│       ├── Card.tsx            # Card, CardSection
│       ├── LoadingState.tsx    # SkeletonLine, SkeletonCard, LoadingSpinner, EmptyState, ErrorState
│       ├── PageHeader.tsx      # Page title + actions
│       └── Toast.tsx           # Toast notifications
├── hooks/
│   ├── useApi.ts              # GET/POST hooks with loading/error states
│   └── useToast.ts            # Toast context and hooks
└── pages/ (53 pages)
    ├── Dashboard.tsx           # System overview, provider status
    ├── Chat.tsx                # AI chat with slash commands
    ├── Brain.tsx               # Brain system dashboard
    ├── WorkflowEditor.tsx      # n8n workflow templates + execution
    ├── CodeGenerator.tsx       # Multi-language code generation
    ├── Agents.tsx              # Agent catalog and execution
    ├── Settings.tsx            # Configuration, providers, system
    ├── SettingsEditor.tsx      # Advanced settings
    ├── About.tsx               # App info
    ├── Help.tsx                # Help and support
    ├── AndroidManager.tsx      # Android device control
    ├── Automation.tsx          # Workflow automation
    ├── BrowserAgent.tsx        # Browser agent control
    ├── BrowserConsole.tsx      # Browser console
    ├── CRM.tsx                 # CRM pipeline UI
    ├── DesktopControl.tsx      # Desktop automation
    ├── FileManager.tsx         # File operations
    ├── Projects.tsx            # Project management
    ├── SEO.tsx                 # SEO toolkit
    ├── SEOToolkit.tsx          # Advanced SEO tools
    ├── Vision.tsx              # Vision system
    ├── VoiceAssistant.tsx      # Voice control panel
    ├── WhatsAppBusiness.tsx    # WhatsApp Business API
    ├── WhatsAppMessenger.tsx   # WhatsApp messaging
    ├── MarketingHub.tsx        # Marketing campaigns
    ├── LeadGen.tsx             # Lead generation
    ├── ContentWriter.tsx       # Content generation
    ├── CodingAgent.tsx         # Coding agent
    ├── CodeReview.tsx          # Code review
    ├── AgentBuilder.tsx        # Agent builder
    ├── AgentChaining.tsx       # Agent chaining
    ├── AgentMemory.tsx         # Agent memory management
    ├── MultiAgent.tsx          # Multi-agent coordination
    ├── AutonomousEmployee.tsx  # Employee orchestrator
    ├── EmailCampaigns.tsx      # Email marketing
    ├── SocialManager.tsx       # Social media manager
    ├── MessagingChannels.tsx   # Multi-channel messaging
    ├── DataVault.tsx           # Secrets vault
    ├── AuditLog.tsx            # Audit log viewer
    ├── UserManagement.tsx      # User administration
    ├── AnalyticsDashboard.tsx  # Analytics
    ├── VisualFlows.tsx         # Visual flow builder
    ├── TaskQueue.tsx           # Job queue
    ├── Goals.tsx               # Goals tracking
    ├── MemoryTree.tsx          # Memory browser
    ├── ModelRouting.tsx        # Model routing
    ├── MultiModal.tsx          # Multi-modal input
    ├── RAGPipeline.tsx         # RAG pipeline
    ├── ToolFramework.tsx       # Tool framework
    ├── LearningAgent.tsx       # Learning agent
    ├── MeetingAgents.tsx       # Meeting agents
    ├── SkillsPresets.tsx       # Skills and presets
    ├── SelfTester.tsx          # Self-testing
    └── VideoStudio.tsx         # Video studio
```

Tech: React 19, TypeScript 5.6, Tailwind CSS v4, Vite 6, lucide-react, recharts

### 6.2 CLI (`cli/lumina.py`)

Commands: `chat`, `code`, `agent`, `agents`, `heal`, `status`, `crm`, `seo`, `files`, `read`, `mcp`, `open`

### 6.3 VS Code Extension (`lumina-vscode/`)

8 commands with keyboard shortcuts:
- `Ctrl+Alt+L`: Open AI Chat
- `Ctrl+Alt+E`: Explain Selected Code
- `Ctrl+Alt+G`: Generate Code at Cursor
- Review Current File, Open Dashboard, Open API Docs, Open CLI Terminal, Start MCP Server

### 6.4 Flutter Mobile App (`lumina_app/`)

Screens: Dashboard, Chat
Services: API service for backend communication

---

## 7. Data Flow

### 7.1 Chat Flow

```
User Input → API (/chat) → CEO Orchestrator → Agent Manager → Specialized Agent
                ↓                                              ↓
         Slash Command? → Direct handler          AI Provider (via chain)
                ↓                                              ↓
         Memory Engine (record) ←────────────────── Agent Response
                ↓
         Response to User
```

### 7.2 Self-Healing Loop

```
Task Input → PLAN (decompose) → EXECUTE (steps) → VERIFY (check) → FIX (revise) → RETRY (max 3)
                ↑                                                              ↓
                └────────────────── Feedback Loop ─────────────────────────────┘
```

### 7.3 Event Flow

```
Module A → event_bus.publish(Event("topic", payload))
                ↓
        Middleware Pipeline (logging, metrics, validation, tracing, rate limit)
                ↓
        Topic Matcher → Subscriber 1 (topic="topic")
                      → Subscriber 2 (topic="topic.*")
                      → Subscriber 3 (topic="*")
                ↓ (on failure)
        Dead Letter Queue (SQLite) → Retry (configurable attempts + backoff)
```

---

## 8. Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Compose                       │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
│  │ lumina-api  │  │   ollama    │  │  lumina-ui  │  │
│  │ (FastAPI)   │  │  (LLM)      │  │  (React)    │  │
│  │ Port: 8000  │  │ Port: 11434 │  │ Port: 5173  │  │
│  │ Health: 30s │  │ Health: 30s │  │ Depends on  │  │
│  │ Restart:    │  │ Restart:    │  │ API         │  │
│  │ unless-stop │  │ unless-stop │  │             │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
│         └────────────────┼────────────────┘         │
│                   lumina-net (bridge)                 │
│                                                       │
│  Volumes: lumina_data, ollama_data                    │
└─────────────────────────────────────────────────────┘
```

MCP Server config: `lumina-mcp.json` — connects Claude Desktop, Cursor, and other MCP clients.

---

## 9. Project Structure

```
workspace/
├── main.py                     # FastAPI entry, lifespan, routing
├── config/settings.py          # Pydantic settings from env
├── Makefile                    # test, lint, fmt, clean, install
├── requirements.txt            # Python deps
├── pyproject.toml              # Project metadata, build, lint config
├── Dockerfile                  # Multi-stage (prod + dev)
├── docker-compose.yml          # API + Ollama + UI
├── docker-compose.prod.yml     # Production override
├── nginx.conf                  # Reverse proxy config
├── .env.example                # Environment template
│
├── api/                        # 53 FastAPI routers
│   └── middleware/             # auth.py, ratelimit.py
│
├── core/                       # Business logic
│   ├── provider.py             # 8-provider AI chain
│   ├── orchestrator.py         # CEO agent
│   ├── brain.py                # Brain system (Think → Observe → Command)
│   ├── workflow_editor.py      # n8n workflow templates + execution engine (15 templates)
│   ├── self_heal.py            # Self-healing loop
│   ├── agents/                 # 19 agents (base, specialized, content)
│   ├── memory/                 # 8-layer memory engine
│   ├── browser/                # Playwright automation (16 files)
│   ├── desktop/                # OS automation (12 files)
│   ├── android/                # ADB control (7 files)
│   ├── voice/                  # Voice pipeline (12 files)
│   ├── vision/                 # Camera, detection, description (8 files)
│   ├── whatsapp/               # WhatsApp Cloud API (3 files)
│   ├── crm/                    # CRM pipeline
│   ├── seo/                    # SEO analytics
│   ├── security/               # Auth, RBAC, encryption, secrets, audit
│   ├── deploy/                 # Docker, K8s, CI/CD, backups, monitoring
│   ├── developer/              # SDK, CLI, docs, templates
│   ├── plugins/                # 7 built-in plugins
│   ├── pipeline/               # Pipeline builder
│   ├── queue/                  # Job queue
│   ├── task_manager/           # Task engine + models
│   ├── vault/                  # Knowledge vault
│   ├── social/                 # Social media manager
│   ├── writer/                 # Content generator
│   ├── learning/               # Learning agent
│   ├── projects/               # Project management
│   ├── tester/                 # Test engine
│   ├── code_review/            # Code review engine
│   ├── context/                # Context manager
│   ├── models/                 # Model router
│   ├── presets/                # Presets
│   ├── skills/                 # Skills
│   ├── prompts/                # Prompt manager
│   ├── visual_flows/           # Visual flow editor
│   ├── automation/             # Automation engine
│   ├── analytics/              # Analytics
│   └── marketplace/            # Plugin marketplace
│
├── kernel/                     # Microkernel
│   ├── __init__.py             # Kernel class
│   ├── events/                 # Event bus (19 files)
│   ├── dependency/             # DI container (12 files)
│   ├── services/               # Service registry
│   ├── scheduler/              # Job scheduler
│   ├── plugins/                # Plugin loader, sandbox, version
│   ├── models/                 # Data models
│   ├── exceptions/             # Error types
│   ├── interfaces/             # Abstract interfaces
│   └── tests/                  # 69+ test files, 1,112+ tests
│
├── cli/lumina.py               # CLI tool
├── mcp_server/server.py        # MCP server (14 tools)
├── jarvis/                     # Voice assistant overlay
├── lumina-ui/                  # React web dashboard
├── lumina-vscode/              # VS Code extension
├── lumina_app/                 # Flutter mobile app
└── hello-lumina/               # Example project
```
