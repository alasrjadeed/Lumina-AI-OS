# Volume 8: Architecture Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CLIENTS                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐   │
│  │Web Dash. │  │ VS Code  │  │ Flutter  │  │ 3rd Party API │   │
│  │(React)   │  │ Extension│  │ (Mobile) │  │ Clients       │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬───────┘   │
│       │              │             │                │           │
├───────┴──────────────┴─────────────┴────────────────┴───────────┤
│                       API GATEWAY                                │
│               FastAPI (12 routers, 60+ endpoints)                │
├─────────────────────────────────────────────────────────────────┤
│                       KERNEL                                     │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Event Bus (pub/sub)                    │   │
│  │  Topics: chat.*, system.*, crm.*, browser.*, custom.*    │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │              Service Registry (DI Container)              │   │
│  │  Register: engine, memory, browser, desktop, crm, seo... │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │                    Scheduler                              │   │
│  │  Cron jobs, delayed tasks, recurring operations          │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │              Middleware Pipeline                          │   │
│  │  Auth → Logging → Metrics → Rate Limiting (planned)     │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                       AI CORE                                    │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Provider Chain (8 providers)                 │   │
│  │  Ollama → OpenRouter → Groq → Gemini → DeepSeek →       │   │
│  │  OpenAI → Cloudflare → NVIDIA                            │   │
│  │  Auto-failover: if one fails, try next                   │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │              Agent System (19 agents)                     │   │
│  │  Coder, Researcher, Writer, Designer, Analyst, etc.      │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │              Tool Executor                                │   │
│  │  Timeout, retry, caching, parallel execution             │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │              Memory Engine (8 layers)                     │   │
│  │  Working → Episodic → Semantic → Short-Term →           │   │
│  │  Long-Term → Vector Store → Embeddings → Search/Recall  │   │
│  └──────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│                     PLUGIN SYSTEM                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  PluginManager — Discover → Load → Enable → Execute      │   │
│  │  7 built-in: CRM, SEO, WhatsApp, Email, Leads, Mktg,    │   │
│  │  Reporting                                               │   │
│  │  Custom plugins via PluginSDK + PackageManager           │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Request Lifecycle

```
1. Client sends HTTP request
2. FastAPI router matches endpoint
3. Auth middleware checks credentials (if enabled)
4. Request handled by route handler
5. Handler calls core service (sync or async)
6. Service uses AI provider chain if needed
7. Response returned to client
```

## Data Flow — Chat Request

```
User: "Create a CRM contact for John"
  ↓
POST /chat {"message": "..."}
  ↓
chat_router → engine.chat()
  ↓
Provider Chain:
  1. Try Ollama (local)
  2. If fail → OpenRouter
  3. If fail → Groq
  ...
  ↓
AI extracts intent: /crm contact John
  ↓
crm.add_contact("John")
  ↓
Response: {"reply": "Created contact John", "agent": "general"}
```

## Module Dependencies

```
Kernel (no deps)
├── AI Core → Kernel
│   ├── Voice → AI Core
│   ├── Browser → Kernel
│   ├── Desktop → Kernel, AI Core
│   ├── Android → Kernel
│   ├── Security → Kernel
│   └── Deploy → Kernel
├── Memory → Kernel, AI Core
├── API → All core modules
└── Plugins → Kernel, AI Core
    ├── CRM → Kernel
    ├── SEO → Kernel, Browser, AI Core
    ├── WhatsApp → Kernel
    └── ...
```

## Data Storage

| Data | Storage | Location |
|------|---------|----------|
| Conversations | JSON file | `lumina_memory.json` |
| CRM data | JSON file | `crm_data.json` |
| SEO data | JSON file | `seo_data.json` |
| Auth users | JSON file | `lumina_auth.json` |
| Secrets | JSON file (encrypted) | `lumina_secrets.json` |
| Settings | `.env` + JSON | `.env`, `lumina_settings.json` |
| Audit log | JSON file | `lumina_audit.json` |
| Plugins | Directory | `core/plugins/` |
| Sessions | Cookie file | `.whatsapp_session/` |

## Scalability

- **Horizontal**: Multiple API instances behind load balancer
- **Vertical**: Increase resources for Ollama/Playwright
- **Caching**: Tool executor has TTL-based result cache
- **Async**: All I/O is async via asyncio + httpx
