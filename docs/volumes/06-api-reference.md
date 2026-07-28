# Volume 6: API Reference

**Base URL**: `http://localhost:8000`  
**Auth**: Optional (set `AUTH_ENABLED=true` + `API_KEYS` in `.env`)  
**Format**: JSON

## System

### `GET /system/health`
Returns system health and active providers.
```json
{"status":"ok","version":"1.0.0","provricts":["ollama","openrouter",...],"primary_provider":"ollama"}
```

### `GET /system/config`
Returns full configuration with provider status.
```json
{"app_name":"Lumina AI OS","version":"1.0.0","providers":{"ollama":true,"openai":false,...}}
```

## Chat

### `POST /chat`
```json
{"message": "Hello, what can you do?"}
```
```json
{"reply": "I can help with...", "agent": "general"}
```

### `GET /chat/history?limit=10`

## Code

### `POST /code/generate`
```json
{"description": "fibonacci function", "language": "python"}
```
### `POST /code/review`
```json
{"description": "def add(a,b): return a+b", "language": "python"}
```

## Agents

### `GET /agents`
### `GET /agents/categories`
### `POST /agents/run`
```json
{"agent": "coder", "task": "Build a REST API"}
```

## CRM

### `GET /crm/summary`
### `GET /crm/contacts`
### `POST /crm/contacts`
```json
{"name": "John", "email": "john@test.com", "phone": "+123"}
```
### `GET /crm/deals`
### `POST /crm/deals`
```json
{"title": "Big Deal", "value": 50000, "contact_id": "1"}
```

## Browser

### `POST /browser/navigate`
```json
{"url": "https://example.com"}
```
### `POST /browser/click`
```json
{"selector": "#button"}
```
### `POST /browser/fill`
```json
{"selector": "#input", "value": "hello"}
```
### `GET /browser/content`
### `GET /browser/links`
### `POST /browser/screenshot`

## Desktop

### `GET /desktop/info`
### `GET /desktop/files?path=.`
### `POST /desktop/execute`
```json
{"command": "ls -la"}
```

## Android

### `GET /android/devices`
### `POST /android/shell`
```json
{"serial": "...", "command": "ls"}
```
### `GET /android/packages?serial=...`
### `GET /android/logcat?serial=...`

## WhatsApp

### `GET /whatsapp/status`
### `POST /whatsapp/send/text`
```json
{"to": "+97333429246", "text": "Hello"}
```

## SEO

### `GET /seo/sites`
### `POST /seo/sites`
### `POST /seo/analyze`
### `POST /seo/meta`

## Workflow Editor

### `GET /workflows`
List all workflows. Optional `?category=` filter.

### `POST /workflows?name=&description=&category=`
Create a new workflow.

### `GET /workflows/{id}`
### `PATCH /workflows/{id}?name=&description=&category=`
### `DELETE /workflows/{id}`

### `POST /workflows/{id}/nodes?node_type=&label=&config={}&x=&y=`
### `DELETE /workflows/{id}/nodes/{node_id}`

### `POST /workflows/{id}/edges?source=&target=`
### `DELETE /workflows/{id}/edges/{edge_id}`

### `GET /workflows/{id}/export/n8n`
Export as n8n-compatible JSON.

### `POST /workflows/{id}/execute`
Execute the workflow locally (no n8n required). Optional JSON body as trigger payload.
```json
{"body": "Hello AI"}
```
Returns per-node execution results.

### `POST /workflows/{id}/save-template?tags=`
Save workflow as a reusable template in the gallery.

### `GET /workflows/n8n/templates?category=&query=`
List templates (15 built-in + custom). Filter by category or search query.

### `POST /workflows/n8n/templates/{template_id}/import`
Import a template as a new workflow.

### `POST /workflows/n8n/import`
Import raw n8n JSON as a Lumina workflow.
```json
{"name":"My n8n WF","nodes":[...],"connections":{...}}
```

### `DELETE /workflows/n8n/templates/{template_id}`
Delete a custom saved template.

## Automation

### `POST /automation/heal`
```json
{"task": "optimize database"}
```

## Kernel

### `GET /`
### `GET /kernel/status`
