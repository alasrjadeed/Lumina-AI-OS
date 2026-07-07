# Volume 2: User Manual

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+ (for UI)

### Quick Start
```bash
# Terminal 1: Start API
cd /home/oem/Documents/Lumina/workspace
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Start UI
cd /home/oem/Documents/Lumina/workspace/lumina-ui
npx vite --host 0.0.0.0

# Open http://localhost:5173
```

## Web Dashboard (14 pages)

### Dashboard `/`
System overview, AI provider status, available agents, services.

### Chat `/chat`
Natural conversation with AI. Type `/` for slash commands:
- `/help` — Show all commands
- `/agents` — List agents
- `/code <desc> -l <lang>` — Generate code
- `/heal <task>` — Self-healing automation
- `/crm summary` — Sales summary
- `/files <path>` — List directory

### Code Generator `/code`
Generate code in 26 languages with explanations.

### Code Review `/code/review`
Paste code for AI-powered review and feedback.

### Agents `/agents`
Run 19 specialized agents for specific tasks.

### CRM `/crm`
Pipeline overview, contact manager, deal tracker, stage analytics.

### Browser Console `/browser`
URL navigation, click/fill actions, page content viewer, link extraction, screenshots.

### File Manager `/files`
Browse directories, read files, navigate file system.

### SEO Toolkit `/seo`
Site management, page analysis, meta tag generation.

### Android Manager `/android`
Device shell, package listing, logcat viewer.

### WhatsApp Messenger `/whatsapp`
Send text/template messages, sent history.

### Automation `/automation`
Self-healing task runner, form profile management.

### Settings `/settings`
View all 11 providers with connected/disconnected status.
