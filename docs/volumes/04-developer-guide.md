# Volume 4: Developer Guide

## Architecture Overview

```
┌──────────────────────────────────────────┐
│              FastAPI Routes              │
│  (12 routers, 60+ endpoints)            │
├──────────────────────────────────────────┤
│              Kernel                      │
│  ┌──────────┬──────────┬──────────────┐  │
│  │Event Bus │    DI    │  Scheduler   │  │
│  │(pub/sub) │Container │ (cron jobs)  │  │
│  └──────────┴──────────┴──────────────┘  │
├──────────────────────────────────────────┤
│           Core Services                  │
│  ┌──────┬──────┬──────┬──────┬──────┐   │
│  │ AI   │Memory│Voice │Browser│Desktop│  │
│  │Core  │      │      │       │       │  │
│  └──────┴──────┴──────┴──────┴──────┘   │
├──────────────────────────────────────────┤
│           Plugin System                  │
│  ┌──────┬──────┬──────┬──────┬──────┐   │
│  │ CRM  │ SEO  │ Email│ Leads│ Mktg │   │
│  └──────┴──────┴──────┴──────┴──────┘   │
└──────────────────────────────────────────┘
```

## Module Structure

Every core module follows this pattern:
```
core/<module>/
├── __init__.py      # Public API exports
├── main_logic.py    # Implementation
└── ...              # Supporting files
```

### Creating a New Module
```python
# core/my_module/__init__.py
"""My module description."""
from core.my_module.main import MyClass

__all__ = ["MyClass"]
```

```python
# core/my_module/main.py
from core.log import log

class MyClass:
    def __init__(self):
        log.info("MyClass initialized")
    
    async def do_something(self) -> dict:
        return {"status": "ok"}
```

## Dependency Injection

The Kernel's service container manages cross-module dependencies:

```python
from kernel import Kernel
kernel = Kernel()

# Register services
kernel.services.register("ai_engine", engine)
kernel.services.register("memory", memory)

# Access services
engine = kernel.services.get("ai_engine")
```

## Event Bus

Pub/sub for loosely coupled communication:

```python
from kernel.events import Event, Subscription

# Subscribe
async def on_message(event: Event):
    print(f"Received: {event.name}")

await kernel.event_bus.register(
    Subscription(topic="chat.message", handler=on_message)
)

# Publish
await kernel.event_bus.publish(Event(
    name="chat.message",
    data={"content": "Hello", "user": "alice"}
))
```

## Adding an API Route

```python
# api/my_module.py
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/my-module", tags=["My Module"])

class MyRequest(BaseModel):
    name: str

@router.post("/action")
async def my_action(req: MyRequest):
    return {"result": f"Hello, {req.name}!"}
```

Register in `main.py`:
```python
from api.my_module import router as my_router
app.include_router(my_router)
```

## Adding an AI Provider

```python
# core/provider.py
class MyProvider(AIProvider):
    def __init__(self):
        self.name = "my_provider"
        self.api_key = settings.my_api_key
        self.base_url = "https://api.myprovider.com/v1"
        self.model = "my-model"

    async def chat(self, messages, tools=None, **kwargs):
        payload = {
            "model": kwargs.get("model", self.model),
            "messages": messages,
        }
        data = await self._post(f"{self.base_url}/chat", payload)
        return self._openai_chat(data)

# Register in AIEngine._init_providers()
# Add to order list and key_map
```

## Adding a Web Dashboard Page

1. Create `lumina-ui/src/pages/MyPage.tsx`
2. Add route in `App.tsx`
3. Add nav link in `components/Layout.tsx`

```tsx
// pages/MyPage.tsx
import { api } from '../api';

export default function MyPage() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white">My Page</h1>
    </div>
  );
}
```

## Testing

### Running Tests
```bash
python3 -m pytest                          # All tests
python3 -m pytest -v                       # Verbose
python3 -m pytest kernel/tests/test_*.py   # Specific file
python3 -m pytest -k "test_feature"        # Specific test
```

### Writing Tests
```python
# kernel/tests/test_my_module.py
import pytest
from core.my_module import MyClass

@pytest.mark.asyncio
async def test_my_feature():
    instance = MyClass()
    result = await instance.do_something()
    assert result["status"] == "ok"
```

### Integration Tests
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_my_endpoint():
    resp = client.post("/my-module/action", json={"name": "test"})
    assert resp.status_code == 200
```

## Code Style

- Follow PEP 8 via Ruff (line length: 100)
- Use Python 3.12 type annotations
- Async-first for I/O operations
- Module docstrings on all `__init__.py`
- Log via `core.log.log`
