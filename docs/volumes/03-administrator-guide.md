# Volume 3: Administrator Guide

## Installation

### Requirements
- Python 3.12+
- Node.js 20+ (for UI development)
- Docker + Docker Compose (for containerized deployment)
- 4GB RAM minimum (8GB recommended)
- 2GB free disk space

### Quick Install
```bash
git clone <repo> lumina
cd lumina/workspace
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Production Install
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Configuration

### Environment Variables (.env)
Refer to `.env.example` for all available variables. Key groups:

| Group | Variables | Required |
|-------|-----------|----------|
| AI Providers | `OLLAMA_*`, `OPENAI_*`, `OPENROUTER_*`, etc. | At least one |
| WhatsApp | `WHATSAPP_API_KEY`, `WHATSAPP_PHONE_ID` | Optional |
| Security | `AUTH_ENABLED`, `API_KEYS`, `LUMINA_MASTER_KEY` | Recommended for production |
| CORS | `CORS_ORIGINS` | Required for web UI |

### Settings File
`config/settings.py` — All settings defined as Pydantic BaseSettings.
Each field auto-reads from the matching uppercase env variable.

## User Management

### Via API
```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePass123!"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"SecurePass123!"}'
```
Note: Auth endpoints are at `/auth/*` when `AUTH_ENABLED=true`.

### Roles
- `admin` — Full system access
- `user` — Chat, agents, personal workflows
- `viewer` — Read-only access

## Plugin Management

### Install a Plugin
```bash
# From directory
python3 -c "
from core.developer.package_manager import PackageManager
pm = PackageManager()
pm.install('/path/to/plugin')
"

# From .lumina package
python3 -c "
pm = PackageManager()
pm.install('plugin.lumina')
"
```

### List Installed Plugins
```bash
python3 -c "
from core.desktop.plugin_manager import PluginManager
pm = PluginManager()
count = pm.load_all()
for p in pm.list_plugins():
    print(f'{p.metadata.name} v{p.metadata.version} - {\"enabled\" if p.enabled else \"disabled\"}')"
```

## Monitoring

### Health Check
```bash
curl http://localhost:8000/system/health
```

### Kernel Status
```bash
curl http://localhost:8000/kernel/status
```

### Audit Log
```bash
curl http://localhost:8000/audit/recent
```

### Metrics
```python
from core.deploy.monitoring import Monitoring
m = Monitoring()
m.register_check("api", lambda: True)
# Run checks
import asyncio
asyncio.run(m.run_all_checks())
```

## Backup & Recovery

### Automated Backups
```bash
python3 -c "
from core.deploy.backups import Backups
b = Backups()
b.schedule(interval_hours=24)
"
```

### Manual Backup
```bash
python3 -c "
from core.deploy.backups import Backups
b = Backups()
b.create_snapshot('pre-update')
"
```

### Restore
```bash
python3 -c "
from core.deploy.backups import Backups
b = Backups()
b.restore('pre-update')
"
```

## Logging

Logs are written to stdout by default. Configure via:

```python
# core/log.py
import logging
logging.basicConfig(level=logging.INFO)
```

Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Updating

### Docker
```bash
docker-compose pull
docker-compose up -d
```

### Manual
```bash
git pull
pip install -r requirements.txt --upgrade
python3 -m uvicorn main:app --reload
```

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| API won't start | Missing dependencies | `pip install -r requirements.txt` |
| Ollama not responding | Ollama not running | `ollama serve` |
| Browser automation fails | Playwright not installed | `playwright install chromium` |
| CORS errors | Wrong origin in config | Set `CORS_ORIGINS` to match your frontend URL |
| Auth errors | Missing/wrong API key | Check `AUTH_ENABLED` and `API_KEYS` in `.env` |
