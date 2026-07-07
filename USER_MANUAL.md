# Lumina AI OS — User Manual

> Version 1.0.0 | The World's First Autonomous AI Employee Operating System

---

## Table of Contents

1.  [Overview](#1-overview)
2.  [Quick Start](#2-quick-start)
3.  [Architecture](#3-architecture)
4.  [Backend API](#4-backend-api)
5.  [AI Provider Chain](#5-ai-provider-chain)
6.  [Slash Commands](#6-slash-commands)
7.  [CLI Interface](#7-cli-interface)
8.  [Web Dashboard](#8-web-dashboard)
9.  [VS Code Extension](#9-vs-code-extension)
10. [Agents](#10-agents)
11. [CRM](#11-crm)
12. [Browser Automation](#12-browser-automation)
13. [Desktop Automation](#13-desktop-automation)
14. [Android Integration](#14-android-integration)
15. [WhatsApp Integration](#15-whatsapp-integration)
16. [SEO Toolkit](#16-seo-toolkit)
17. [Self-Healing Loop](#17-self-healing-loop)
18. [Kernel System](#18-kernel-system)
19. [MCP Server](#19-mcp-server)
20. [Flutter Mobile App](#20-flutter-mobile-app)
21. [Troubleshooting](#21-troubleshooting)

---

## 1. Overview

Lumina AI OS is an autonomous AI employee operating system. It coordinates multiple AI
providers, specialized agents, and automation tools to act as your digital workforce.

### Core Capabilities

- **Chat** — Talk to the CEO AI for planning, research, and task breakdown
- **Code Generation** — Generate production code in any language
- **19 Specialized Agents** — Software engineer, lead gen, CRM, design, media, and more
- **Self-Healing Loop** — Autonomous plan → execute → verify → fix → retry cycle
- **CRM Pipeline** — Contacts, deals, sales tracking
- **Browser Automation** — Playwright-based web control
- **Desktop Automation** — File management, system commands
- **Android Integration** — ADB device control
- **WhatsApp Business** — Send messages, templates, media
- **SEO Analysis** — Page audits, meta generation
- **MCP Server** — Expose all tools to any MCP-compatible AI client
- **Slash Commands** — Quick actions from any chat interface

---

## 2. Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+
- Ollama (optional, for local AI)

### Start the Backend

```bash
cd /home/oem/Documents/Lumina/workspace
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Start the Frontend (optional)

```bash
cd /home/oem/Documents/Lumina/workspace/lumina-ui
npm run dev -- --host 0.0.0.0
```

### Open the Dashboard

- **Web UI:** http://localhost:5173
- **API Docs:** http://localhost:8000/docs

### First Chat

```bash
lumina chat "Hello, what can you do?"
```

Or open http://localhost:5173 and type a message.

---

## 3. Architecture

```
┌─────────────────────────────────────────────────────┐
│                    YOU                                │
│          (Dashboard · CLI · VS Code · Mobile)         │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                 LUMINA API (FastAPI)                  │
│              http://localhost:8000                    │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                    KERNEL                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │Event Bus │ │ Service   │ │    DI    │ │Plugin   │ │
│  │          │ │ Registry  │ │Container │ │Loader   │ │
│  └──────────┘ └──────────┘ └──────────┘ └────────┘ │
│  ┌────────────────────────────────────────────────┐ │
│  │                Scheduler                        │ │
│  └────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              AI PROVIDER CHAIN                        │
│  Ollama → OpenRouter(free) → Groq(free) → Gemini     │
│  → DeepSeek → OpenAI(paid, last resort)              │
│        ↑ Auto-fallback on failure/credit exhaustion  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              SPECIALIZED AGENTS                      │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │Lead  │ │Quote │ │Email │ │ Call │ │Customer   │  │
│  │ Gen  │ │ation │ │  Asst │ │ Asst │ │ Success   │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐  │
│  │ Docs │ │Voice │ │Design│ │Media │ │  Content  │  │
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────────┘  │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              AUTOMATION MODULES                      │
│  Browser · Desktop · Android · WhatsApp · CRM · SEO │
└─────────────────────────────────────────────────────┘
```

---

## 4. Backend API

The backend runs on **http://localhost:8000** with full Swagger docs at **/docs**.

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Server info + kernel status |
| GET | `/system/health` | Health check + active providers |
| GET | `/system/config` | Full configuration |
| POST | `/chat` | Talk to CEO AI (supports `/` commands) |
| GET | `/chat/history` | Conversation history |
| GET | `/chat/commands` | List available slash commands |

### Code Generation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/code/generate` | Generate code in any language |
| POST | `/code/review` | Review existing code |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agents` | List all 19 agents |
| GET | `/agents/categories` | Agents grouped by category |
| POST | `/agents/run` | Execute a specific agent |

### Automation

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/automation/heal` | Self-healing loop |
| POST | `/automation/form/analyze` | Analyze HTML form fields |
| POST | `/automation/form/fill` | Suggest form values |
| POST | `/automation/form/profile` | Save form profile |

### Browser

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/browser/navigate` | Navigate to URL |
| POST | `/browser/click` | Click element |
| POST | `/browser/fill` | Fill form field |
| GET | `/browser/content` | Get page HTML/text |
| GET | `/browser/links` | Extract all links |
| GET | `/browser/forms` | Extract form fields |
| POST | `/browser/screenshot` | Take screenshot |
| POST | `/browser/close` | Close browser |

### Desktop

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/desktop/info` | System information |
| GET | `/desktop/files` | List directory |
| GET | `/desktop/files/read` | Read file content |
| POST | `/desktop/files/write` | Write file |
| POST | `/desktop/files/copy` | Copy file |
| POST | `/desktop/files/move` | Move file |
| DELETE | `/desktop/files/delete` | Delete file |
| POST | `/desktop/execute` | Run shell command |

### Android

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/android/devices` | List connected devices |
| POST | `/android/connect` | Connect to device |
| GET | `/android/info` | Device information |
| POST | `/android/shell` | Run ADB shell command |
| POST | `/android/install` | Install APK |
| POST | `/android/tap` | Tap screen at coordinates |
| POST | `/android/text` | Input text |
| POST | `/android/screenshot` | Take device screenshot |
| GET | `/android/logcat` | Get device logs |
| GET | `/android/packages` | List installed packages |

### WhatsApp

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/whatsapp/status` | Connection status |
| POST | `/whatsapp/send/text` | Send text message |
| POST | `/whatsapp/send/template` | Send template message |
| POST | `/whatsapp/send/image` | Send image |
| POST | `/whatsapp/send/document` | Send document |
| GET | `/whatsapp/templates` | List message templates |

### CRM

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/crm/contacts` | List contacts |
| POST | `/crm/contacts` | Add contact |
| GET | `/crm/deals` | List deals |
| POST | `/crm/deals` | Add deal |
| POST | `/crm/deals/stage` | Update deal stage |
| GET | `/crm/summary` | Sales summary |
| POST | `/crm/activities` | Log activity |

### SEO

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/seo/sites` | List tracked sites |
| POST | `/seo/sites` | Add site |
| POST | `/seo/analyze` | Analyze page HTML |
| POST | `/seo/meta` | Generate meta tags |
| GET | `/seo/history` | Audit history |

### Kernel

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/kernel/status` | Kernel services + event bus |

---

## 5. AI Provider Chain

Lumina uses a **free-first** provider chain with automatic fallback:

| # | Provider | Model | Cost | Fallback Trigger |
|---|----------|-------|------|------------------|
| 1 | Ollama (local) | qwen2.5-coder:0.5b | Always free | Timeout (15s) |
| 2 | OpenRouter | cohere/north-mini-code:free | Free model | API error |
| 3 | Groq | llama-3.1-8b-instant | Free tier | Rate limit/error |
| 4 | Gemini | gemini-1.5-flash | Free tier (60 req/min) | Quota exceeded |
| 5 | DeepSeek | deepseek-chat | Free credits | Credits exhausted |
| 6 | OpenAI | gpt-4o-mini | Paid (last resort) | N/A |

When a provider fails (timeout, rate limit, credit exhausted, API error),
Lumina automatically tries the next provider in the chain.

### Configure Providers

Edit `workspace/.env`:

```env
# Ollama (local)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:0.5b

# OpenAI (optional, paid)
OPENAI_API_KEY=sk-proj-...

# OpenRouter (free models available)
OPENROUTER_API_KEY=sk-or-v1-...

# DeepSeek
DEEPSEEK_API_KEY=sk-...

# Groq (free tier)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.1-8b-instant

# Gemini (free tier)
GEMINI_API_KEY=AIzaSy...
```

---

## 6. Slash Commands

Type `/` in any chat interface to see available commands. Use arrow keys to
navigate and Enter to select.

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/skills` | Show Lumina skills overview |
| `/status` | System health & provider chain |
| `/agents` | List all 19 agents |
| `/agent <name> <task>` | Run a specialized agent |
| `/code <desc> -l <lang>` | Generate code |
| `/heal <task>` | Self-healing loop |
| `/crm summary` | CRM sales summary |
| `/crm contact <name>` | Add CRM contact |
| `/crm deals` | List deals |
| `/files <path>` | List directory |
| `/read <path>` | Read a file |
| `/mcp` | Start MCP server |
| `/open` | Open dashboard in browser |

### Examples

```
/status
/agent software_engineer write a Python function to sort a list
/code build a REST API endpoint -l python
/heal find and fix bugs in app.py
/crm summary
/files /home/oem/Documents
/read /home/oem/Documents/notes.txt
```

---

## 7. CLI Interface

The `lumina` command is available from any terminal.

### Installation

The CLI is already installed at `/usr/local/bin/lumina`. If not found:

```bash
source ~/.bashrc
```

### Usage

```bash
lumina <command> [args]

Commands:
  chat <message>          Talk to Lumina CEO AI
  code <desc> -l <lang>   Generate code
  agent <name> <task>     Run an agent
  agents                  List all agents
  heal <task>             Self-healing loop
  status                  System health
  crm summary|contact|deals
  seo <html>              SEO analysis
  files <path>            List directory
  read <path>             Read file
  mcp                     Start MCP server
  open                    Open dashboard in browser
```

### Examples

```bash
lumina status
lumina chat "What is the capital of France?"
lumina code "function to sort a list" -l python
lumina agent lead_gen "Find restaurants in Bahrain without websites"
lumina heal "fix bugs in app.py"
lumina crm summary
lumina files /home
lumina read /home/notes.txt
```

---

## 8. Web Dashboard

The React dashboard runs on **http://localhost:5173**.

### Pages

| Page | Route | Features |
|------|-------|----------|
| Dashboard | `/` | System health, provider status, agent cards |
| Chat | `/chat` | Talk to CEO AI, slash commands with autocomplete |
| Code Generator | `/code` | Generate code in 8 languages, copy to clipboard |
| Agents | `/agents` | Run any of 19 agents with task input |
| Settings | `/settings` | Provider config, system info |

### Start the Frontend

```bash
cd /home/oem/Documents/Lumina/workspace/lumina-ui
npm run dev -- --host 0.0.0.0
```

---

## 9. VS Code Extension

### Installation

```bash
cd /home/oem/Documents/Lumina/workspace/lumina-vscode
vsce package
code --install-extension lumina-vscode-0.1.0.vsix
```

### Commands

| Command | Shortcut | Description |
|---------|----------|-------------|
| Lumina: Open AI Chat | Ctrl+Alt+L | Chat panel in VS Code |
| Lumina: Explain Selected Code | Ctrl+Alt+E | Select code → get explanation |
| Lumina: Generate Code at Cursor | Ctrl+Alt+G | Describe code → inserts at cursor |
| Lumina: Review Current File | — | Review file or selection |
| Lumina: Open Dashboard | — | Open web dashboard in browser |
| Lumina: Open API Docs | — | Open Swagger docs |
| Lumina: Open CLI Terminal | — | Open terminal with CLI ready |
| Lumina: Start MCP Server | — | Start MCP server in terminal |

Access via: `Ctrl+Shift+P` → type `Lumina`

---

## 10. Agents

19 specialized AI agents are available:

### Base Agents

| Agent | Purpose |
|-------|---------|
| `software_engineer` | Write and debug code |
| `web_developer` | Build web applications |
| `business_manager` | Business operations |
| `marketing_manager` | SEO, social media, campaigns |
| `qa_engineer` | Testing and quality |
| `data_analyst` | Data analysis |
| `research_analyst` | Research tasks |

### Specialized Agents

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

### Content Agents

| Agent | Purpose |
|-------|---------|
| `media_writer` | Blog posts, articles, copywriting |
| `media_video` | Video scripts, storyboards |
| `media_podcast` | Podcast scripts, show notes |
| `content_writer` | Multi-format content creation |

### Run an Agent

```bash
lumina agent software_engineer "Write a Python function to calculate fibonacci"
lumina agent lead_gen "Find restaurants in Bahrain without online ordering"
lumina agent documentation "Write README for this project"
```

---

## 11. CRM

The CRM module manages contacts, deals, and sales pipeline.

### Deal Stages

```
LEAD → QUALIFIED → PROPOSAL → NEGOTIATION → CLOSED_WON
                                               CLOSED_LOST
```

### Commands

```bash
# Add a contact
lumina crm contact "John Doe"

# View sales summary
lumina crm summary

# Add a deal (via API)
curl -X POST http://localhost:8000/crm/deals \
  -H "Content-Type: application/json" \
  -d '{"title":"Website Design","value":5000,"contact_id":"1"}'

# View deals
lumina crm deals

# Update deal stage (via API)
curl -X POST http://localhost:8000/crm/deals/stage \
  -H "Content-Type: application/json" \
  -d '{"deal_id":"1","stage":"closed_won"}'
```

Data is persisted to `crm_data.json` in the workspace root.

---

## 12. Browser Automation

Playwright-based browser control.

### Prerequisites

```bash
pip install playwright
playwright install chromium
```

### Usage

```python
# Via API
curl -X POST http://localhost:8000/browser/navigate \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com"}'

curl http://localhost:8000/browser/links
curl http://localhost:8000/browser/forms
```

### Slash Commands

```
/files https://example.com   (not applicable - use API)
```

---

## 13. Desktop Automation

File management and system commands.

### Commands

```bash
# List files
curl http://localhost:8000/desktop/files?path=/home

# Read file
curl "http://localhost:8000/desktop/files/read?path=/home/user/notes.txt"

# Write file
curl -X POST http://localhost:8000/desktop/files/write \
  -H "Content-Type: application/json" \
  -d '{"path":"/home/user/test.txt","content":"Hello World"}'

# Execute command
curl -X POST http://localhost:8000/desktop/execute \
  -H "Content-Type: application/json" \
  -d '{"command":"ls -la"}'

# System info
curl http://localhost:8000/desktop/info
```

### Slash Commands

```
/files /home
/read /home/user/notes.txt
```

---

## 14. Android Integration

ADB-based Android device control.

### Prerequisites

```bash
# Install ADB
sudo apt install adb
# Enable USB debugging on device
# Connect device via USB
```

### Commands

```bash
# List devices
curl http://localhost:8000/android/devices

# Connect
curl -X POST http://localhost:8000/android/connect

# Device info
curl http://localhost:8000/android/info

# Install APK
curl -X POST http://localhost:8000/android/install \
  -H "Content-Type: application/json" \
  -d '{"apk_path":"/path/to/app.apk"}'

# Tap screen
curl -X POST http://localhost:8000/android/tap \
  -H "Content-Type: application/json" \
  -d '{"x":500,"y":800}'

# Input text
curl -X POST http://localhost:8000/android/text \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello World"}'

# Take screenshot
curl -X POST http://localhost:8000/android/screenshot

# View logs
curl "http://localhost:8000/android/logcat?lines=100"
```

---

## 15. WhatsApp Integration

WhatsApp Cloud API messaging.

### Prerequisites

Add to `.env`:

```env
WHATSAPP_API_KEY=your_facebook_graph_api_token
WHATSAPP_PHONE_ID=your_phone_number_id
```

### Commands

```bash
# Check status
curl http://localhost:8000/whatsapp/status

# Send text
curl -X POST http://localhost:8000/whatsapp/send/text \
  -H "Content-Type: application/json" \
  -d '{"to":"+973XXXXXXXX","text":"Hello from Lumina!"}'

# Send template
curl -X POST http://localhost:8000/whatsapp/send/template \
  -H "Content-Type: application/json" \
  -d '{"to":"+973XXXXXXXX","template_name":"hello_world","params":["John"]}'

# List templates
curl http://localhost:8000/whatsapp/templates
```

---

## 16. SEO Toolkit

Search engine optimization analysis and meta tag generation.

### Commands

```bash
# Add a site
curl -X POST http://localhost:8000/seo/sites \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com","name":"My Site"}'

# Analyze page HTML
curl -X POST http://localhost:8000/seo/analyze \
  -H "Content-Type: application/json" \
  -d '{"html":"<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>","url":"https://example.com"}'

# Generate meta tags
curl -X POST http://localhost:8000/seo/meta \
  -H "Content-Type: application/json" \
  -d '{"content":"Your page content here...","focus_keyword":"AI assistant"}'

# View audit history
curl http://localhost:8000/seo/history?limit=10
```

---

## 17. Self-Healing Loop

Autonomous task execution with verification and retry.

### How It Works

```
1. PLAN      → Break task into steps
2. EXECUTE   → Run each step
3. VERIFY    → Check results for errors
4. FIX       → Revise plan if issues found
5. RETRY     → Repeat until quality met (max 3 attempts)
```

### Commands

```bash
# Via CLI
lumina heal "Write a Python script to backup my Documents folder"

# Via API
curl -X POST http://localhost:8000/automation/heal \
  -H "Content-Type: application/json" \
  -d '{"task":"Write a Python script to backup my Documents folder"}'

# Via slash command
/heal Write a Python script to backup my Documents folder
```

---

## 18. Kernel System

The Kernel is the foundation that all Lumina modules depend on.

### Components

| Component | Description |
|-----------|-------------|
| **Event Bus** | Pub/sub event system with wildcards and history |
| **Service Registry** | Register and resolve services by name |
| **DI Container** | Dependency injection (singleton/scoped/transient) |
| **Plugin Loader** | Discover and load plugins from directories |
| **Scheduler** | Delayed, recurring, and retryable job execution |

### Event Bus

The event bus allows modules to communicate without direct coupling.

```python
from kernel import event_bus

# Subscribe
async def on_agent_run(event, data):
    print(f"Agent ran: {data}")

event_bus.subscribe("agent.run", on_agent_run)

# Emit
await event_bus.emit("agent.run", {"agent": "software_engineer", "task": "..."})

# Wildcard subscriber (receives all events)
event_bus.subscribe("*", lambda e, d: print(f"Event: {e}"))
```

### Service Registry

All major services register themselves on startup:

```python
kernel.services.register("ai_engine", engine)
kernel.services.register("memory", memory)
kernel.services.register("config", settings)
kernel.services.register("browser", browser)
kernel.services.register("desktop", desktop)
# ... etc
```

### Status

```bash
curl http://localhost:8000/kernel/status
```

Returns registered services, event subscriber count, and scheduled jobs.

---

## 19. MCP Server

Model Context Protocol server — exposes all Lumina tools to MCP-compatible
AI clients (Claude Desktop, Cursor, etc.).

### Start

```bash
source venv/bin/activate
python3 mcp_server/server.py
```

Or from VS Code: `Ctrl+Shift+P` → `Lumina: Start MCP Server`

### Available Tools (14)

| Tool | Description |
|------|-------------|
| `chat` | Talk to CEO AI |
| `generate_code` | Generate code in any language |
| `run_agent` | Execute any specialized agent |
| `list_agents` | List all agents |
| `self_heal` | Autonomous plan→execute→verify→fix loop |
| `system_health` | Check providers and status |
| `desktop_info` | Get system information |
| `list_files` | Browse local files |
| `read_file` | Read file content |
| `crm_summary` | CRM sales summary |
| `crm_add_contact` | Add CRM contact |
| `crm_add_deal` | Add CRM deal |
| `seo_analyze_page` | Analyze HTML for SEO |
| `seo_generate_meta` | Generate SEO meta tags |

### Connect Claude Desktop

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "lumina-ai-os": {
      "command": "python3",
      "args": ["/home/oem/Documents/Lumina/workspace/mcp_server/server.py"],
      "env": {
        "PYTHONPATH": "/home/oem/Documents/Lumina/workspace"
      }
    }
  }
}
```

A pre-made config file is at `workspace/lumina-mcp.json`.

---

## 20. Flutter Mobile App

A mobile companion app for iOS/Android.

### Location

```
workspace/lumina_app/
├── lib/
│   ├── main.dart               # App entry point
│   ├── screens/
│   │   ├── dashboard.dart       # Dashboard screen
│   │   └── chat.dart            # Chat screen
│   └── services/
│       └── api_service.dart     # API client
└── pubspec.yaml                 # Dependencies
```

### Build

```bash
cd /home/oem/Documents/Lumina/workspace/lumina_app
flutter pub get
flutter run
```

---

## 21. Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check logs
cat /tmp/lumina_server.log

# Restart
kill $(lsof -ti:8000)
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### AI Providers not responding

```bash
# Check health
curl http://localhost:8000/system/health

# Check config
curl http://localhost:8000/system/config

# Ensure .env has valid keys
cat /home/oem/Documents/Lumina/workspace/.env
```

### Slash commands not working

```bash
# Verify the endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"/status"}'
```

### VS Code extension not appearing

```bash
# Reload window: Ctrl+Shift+P → Developer: Reload Window
# Reinstall if needed
code --install-extension /home/oem/Documents/Lumina/workspace/lumina-vscode/lumina-vscode-0.1.0.vsix
```

### Ollama model too slow

Edit `workspace/core/provider.py` and change `OLLAMA_TIMEOUT = 15.0` to a
higher value, or use the cloud providers which fall through automatically.

### Backup

```bash
# Create a backup
tar -czf lumina-backup.tar.gz \
  --exclude=node_modules \
  --exclude=__pycache__ \
  --exclude=venv \
  workspace/

# Restore
tar -xzf lumina-backup.tar.gz
```

---

## Appendix: Project Structure

```
workspace/
├── main.py                    # FastAPI server entry point
├── .env                       # API keys & configuration
├── .env.example               # Template for .env
├── requirements.txt           # Python dependencies
├── test_lumina.py             # API test suite
├── USER_MANUAL.md             # This document
├── lumina-mcp.json            # MCP config for Claude
├── start-vscode.sh            # One-click VS Code launcher
├── config/
│   ├── settings.py            # Pydantic settings
├── api/
│   ├── chat.py                # Chat + slash commands
│   ├── agents.py              # Agent listing & execution
│   ├── code.py                # Code generation
│   ├── system.py              # Health & config
│   ├── automation.py          # Self-healing + form filler
│   ├── browser.py             # Browser automation API
│   ├── desktop.py             # Desktop automation API
│   ├── android.py             # Android ADB API
│   ├── whatsapp.py            # WhatsApp API
│   ├── crm.py                 # CRM pipeline API
│   └── seo.py                 # SEO analytics API
├── core/
│   ├── provider.py            # AI provider chain (6 providers)
│   ├── orchestrator.py        # CEO AI agent
│   ├── self_heal.py           # Self-healing loop
│   ├── log.py                 # Structured logging
│   ├── memory/store.py        # Conversation memory
│   ├── agents/
│   │   ├── base.py            # Base agent class
│   │   ├── specialized.py     # 8 specialized agents
│   │   └── content.py         # 4 content agents
│   ├── browser/
│   │   ├── automation.py      # Playwright browser control
│   │   └── form_filler.py     # Form analysis & filling
│   ├── desktop/
│   │   └── os_automation.py   # File & command execution
│   ├── android/
│   │   └── device.py          # ADB device control
│   ├── whatsapp/
│   │   └── client.py          # WhatsApp Cloud API
│   ├── crm/
│   │   └── pipeline.py        # CRM data & pipeline
│   └── seo/
│       └── analytics.py       # SEO analysis
├── kernel/
│   ├── __init__.py            # Kernel orchestrator
│   ├── events/bus.py          # Event bus
│   ├── services/registry.py   # Service registry
│   ├── di/container.py        # DI container
│   ├── plugins/loader.py      # Plugin loader
│   ├── scheduler/scheduler.py # Job scheduler
│   ├── models/                # Data models
│   ├── exceptions/            # Error types
│   └── tests/                 # 14 kernel unit tests
├── mcp_server/
│   └── server.py              # MCP server (14 tools)
├── cli/
│   └── lumina.py              # CLI interface
├── lumina-ui/                 # React web dashboard
│   └── src/
│       ├── App.tsx
│       ├── api.ts
│       ├── components/Layout.tsx
│       └── pages/ (Dashboard, Chat, CodeGenerator, Agents, Settings)
├── lumina-vscode/             # VS Code extension
│   ├── package.json           # 8 commands
│   └── src/extension.js
├── lumina_app/                # Flutter mobile app
│   └── lib/
│       ├── main.dart
│       ├── screens/ (dashboard, chat)
│       └── services/api_service.dart
├── lumina-vscode-0.1.0.vsix   # Packaged extension
├── crm_data.json              # CRM data store
├── seo_data.json              # SEO data store
└── lumina_memory.json         # Conversation history
```
