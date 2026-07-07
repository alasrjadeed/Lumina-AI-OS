# Volume 9: Troubleshooting Guide

## Common Issues

### API Won't Start

**Error**: `ModuleNotFoundError: No module named 'fastapi'`
**Fix**: `pip install -r requirements.txt`

**Error**: `ImportError: cannot import name 'ServerProtocol' from 'websockets'`
**Fix**: `pip install --upgrade websockets`

**Error**: Port already in use
**Fix**: `kill $(lsof -ti:8000)` or change port in command

### AI Provider Not Working

**Symptom**: Chat returns "All providers failed"
**Check**: Run health endpoint
```bash
curl http://localhost:8000/system/health
```

**Symptom**: Specific provider fails
**Check**: Provider API key in `.env`
```bash
python3 -c "from config.settings import settings; print('openai:', settings.openai_api_key[:20] if settings.openai_api_key else 'EMPTY')"
```

**Symptom**: Ollama not responding
**Check**: Ollama is running
```bash
curl http://localhost:11434/api/tags
```

### Browser Automation Fails

**Error**: `playwright.async_api` import error
**Fix**: `pip install playwright && playwright install chromium`

**Error**: Navigation timeout
**Cause**: Page is slow or unreachable
**Fix**: Check URL is correct and site is accessible

**Error**: Element not found
**Cause**: Selector is wrong or element is dynamically loaded
**Fix**: Use `wait_for_selector` with appropriate timeout

### Frontend Issues

**Symptom**: Blank page
**Check**: Browser console for errors
**Fix**: `npx tsc --noEmit` to find TypeScript errors

**Symptom**: API calls failing with 404
**Check**: Vite proxy config in `vite.config.ts`
**Fix**: Ensure `/api` prefix matches the proxy target

**Symptom**: CORS errors in console
**Fix**: Set `CORS_ORIGINS` to your frontend URL in `.env`

### WhatsApp Issues

**Error**: `"The session is invalid because the user logged out"`
**Fix**: Generate new token at https://developers.facebook.com

**Error**: `"Error validating access token"`
**Fix**: Token expired — refresh in Meta Developer Portal

### Database / Storage Issues

**Symptom**: JSON file corrupted
**Fix**: Restore from backup
```bash
python3 -c "
from core.deploy.backups import Backups
b = Backups()
b.restore('backup-name')
"
```

**Symptom**: Memory file grows too large
**Fix**: Clear old conversations
```python
from core.memory.store import MemoryStore
store = MemoryStore()
store._data["conversations"] = store._data["conversations"][-100:]
store._save()
```

## Diagnostic Commands

```bash
# Health check
curl http://localhost:8000/system/health

# Provider config
curl http://localhost:8000/system/config

# Kernel status
curl http://localhost:8000/kernel/status

# Audit log
curl http://localhost:8000/audit/recent

# Check service registration
curl http://localhost:8000/kernel/status
```

## Logs

### Backend logs
Logs are output to stdout. To capture:
```bash
python3 -m uvicorn main:app 2>&1 | tee lumina.log
```

### Frontend logs
Check browser console (F12 → Console tab).
Or check terminal running `npx vite`.

### Debug mode
Set in `.env`:
```bash
DEBUG=true
```

## Recovery

### Reset Everything
```bash
# Stop servers
kill $(lsof -ti:8000) $(lsof -ti:5173)

# Clear data (backup first!)
rm -f *.json  # Removes memory, CRM, SEO, auth data

# Restart
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 &
```

### Factory Reset Plugins
```bash
rm -rf .lumina_packages
python3 -c "from core.desktop.plugin_manager import PluginManager; pm = PluginManager(); pm.load_all()"
```

## Getting Help

- Check logs: `tail -f /tmp/lumina-api.log`
- Run diagnostics: `python3 -m pytest -v`
- Verify all providers: `curl http://localhost:8000/system/config`
- Check frontend build: `cd lumina-ui && npx tsc --noEmit`
