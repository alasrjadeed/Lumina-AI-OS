# Volume 7: Deployment Guide

## Local Development

```bash
# Backend
cd /home/oem/Documents/Lumina/workspace
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd /home/oem/Documents/Lumina/workspace/lumina-ui
npm install
npx vite --host 0.0.0.0
```

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Production
docker-compose -f docker-compose.prod.yml up -d
```

### Services
| Service | Port | Description |
|---------|------|-------------|
| lumina-api | 8000 | FastAPI backend |
| ollama | 11434 | Local AI |
| lumina-ui | 5173 | Frontend |
| nginx | 80/443 | Reverse proxy |

## Production Checklist

- [ ] Set `AUTH_ENABLED=true` in `.env`
- [ ] Set `LUMINA_MASTER_KEY` environment variable
- [ ] Configure `CORS_ORIGINS` with your domain
- [ ] Set `LUMINA_ENV=production`
- [ ] Use `docker-compose.prod.yml`
- [ ] Configure SSL certificates
- [ ] Set up database backups
- [ ] Configure monitoring alerts
- [ ] Enable audit logging

## Backups

```bash
# Automated backups every 24h
python3 -c "from core.deploy.backups import Backups; b = Backups(); b.schedule(24)"

# Manual backup
python3 -c "from core.deploy.backups import Backups; b = Backups(); b.create_snapshot('pre-update')"

# Restore
python3 -c "from core.deploy.backups import Backups; b = Backups(); b.restore('pre-update')"
```
