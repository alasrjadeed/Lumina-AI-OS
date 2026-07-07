# Volume 1: Executive Guide

## Product Overview

Lumina is an **AI Automation Platform** that combines:

- Conversational AI (8-provider chain with auto-failover)
- Browser automation (Playwright-based, 12 modules)
- Voice interface (wake word, STT, TTS, streaming)
- Business tools (CRM, SEO, Marketing, Leads, Reporting)
- Desktop automation (files, apps, windows, clipboard)
- Mobile device management (Android via ADB)
- Plugin ecosystem (7 built-in + SDK for custom)
- Memory engine (8 layers: working to vector)
- Security framework (auth, RBAC, encryption, audit)

## Editions

| Feature | Desktop | Cloud | Enterprise |
|---------|---------|-------|------------|
| Local AI (Ollama) | ✅ | ✅ | ✅ |
| Cloud AI Providers | Optional | ✅ | ✅ |
| Web Dashboard | ✅ | ✅ | ✅ |
| API Access | ✅ | ✅ | ✅ |
| Multi-user | ❌ | ✅ | ✅ |
| SSO | ❌ | ❌ | ✅ |
| Audit Logging | ✅ | ✅ | ✅ |
| Priority Support | ❌ | ❌ | ✅ |

## Licensing

- **Open Source**: MIT License
- **Commercial**: Contact for enterprise licensing

## Deployment Options

- **Local**: `python3 -m uvicorn main:app`
- **Docker**: `docker-compose up`
- **Production**: `docker-compose -f docker-compose.prod.yml up`
- **Kubernetes**: Auto-generate manifests via core/deploy/kubernetes.py
