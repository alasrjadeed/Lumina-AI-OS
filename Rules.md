# Lumina AI OS — Rules & Conventions

> **Version**: 1.0.0 | **Updated**: July 2026

---

## 1. Code Style

### 1.1 Python

| Rule | Standard |
|------|----------|
| **Language version** | Python 3.12+ |
| **Formatter** | Ruff (line length 100) |
| **Linter** | Ruff with rules: E, F, W, I, N, UP, SIM, PERF, PLC |
| **Type hints** | Required on all public functions/methods. Use `from __future__ import annotations` |
| **String quotes** | Double quotes preferred |
| **Imports** | Sorted with `isort` (I rule in Ruff). Standard → Third-party → Local |
| **Naming** | `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_CASE` for constants |
| **Docstrings** | Google-style for public APIs. One-line summary + args/returns/raises sections |
| **Async** | Prefer `async/await` for I/O-bound operations. Use `asyncio` for concurrency |
| **Error handling** | Specific exceptions, never bare `except:`. Log warnings for recoverable, raise for fatal |

```python
# Good
from __future__ import annotations

import asyncio
from dataclasses import dataclass

import httpx

from core.log import log


@dataclass
class TaskResult:
    status: str
    output: str
    error: str = ""


async def execute_task(task_id: str, timeout: float = 30.0) -> TaskResult:
    """Execute a task with timeout.

    Args:
        task_id: The task identifier.
        timeout: Maximum execution time in seconds.

    Returns:
        TaskResult with status, output, and optional error.

    Raises:
        ValueError: If task_id is empty.
    """
    if not task_id:
        raise ValueError("task_id must not be empty")
    # ...
```

### 1.2 TypeScript / React

| Rule | Standard |
|------|----------|
| **Language version** | TypeScript 5.6+ |
| **Framework** | React 19 with functional components + hooks |
| **Styling** | Tailwind CSS v4 utility classes |
| **Component structure** | One component per file. Named exports preferred |
| **Naming** | `PascalCase` for components, `camelCase` for hooks/functions/variables |
| **Hooks** | Prefix with `use` (e.g., `useApi`, `useToast`) |
| **API calls** | Use `useApi` / `useApiMutation` hooks from `hooks/useApi.ts` |
| **Types** | Define in `types.ts` or co-located. Prefer `interface` over `type` for objects |
| **File extension** | `.tsx` for components, `.ts` for utilities |

```tsx
// Good
import { useState } from "react";
import { Card, CardSection } from "../components/ui/Card";
import { useApi } from "../hooks/useApi";
import type { Agent } from "../types";

export function AgentCard({ agent }: { agent: Agent }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <Card>
      <CardSection title={agent.name}>
        {expanded && <p>{agent.description}</p>}
      </CardSection>
    </Card>
  );
}
```

---

## 2. Project Structure

| Rule | Standard |
|------|----------|
| **New API routes** | Add to `api/` directory. Import and register in `main.py` |
| **New core services** | Add to `core/` directory with `__init__.py` |
| **New agents** | Add to `core/agents/` and register in agent catalog |
| **New plugins** | Add to `core/plugins/` with a manifest |
| **Tests** | Place in `kernel/tests/` with `test_` prefix |
| **Config** | Environment variables in `.env`, defaults in `config/settings.py` |

---

## 3. Git Conventions

### 3.1 Branch Naming

```
feature/<name>          # New features
fix/<name>              # Bug fixes
refactor/<name>         # Code refactoring
docs/<name>             # Documentation
test/<name>             # Test additions
chore/<name>            # Maintenance tasks
```

### 3.2 Commit Messages

```
<type>(<scope>): <subject>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `style`, `perf`

Examples:
```
feat(agents): add data_analyst agent with chart generation
fix(browser): handle page crash during navigation
refactor(kernel): extract event middleware into separate files
docs(api): document CRM pipeline endpoints
test(event_bus): add retry and DLQ integration tests
```

### 3.3 Pull Requests

- One feature/fix per PR
- Description must include: what, why, how to test
- All tests must pass
- Ruff lint must pass (`make lint`)
- At least one reviewer for core changes
- Squash merge preferred

---

## 4. Testing

### 4.1 Requirements

| Rule | Standard |
|------|----------|
| **Framework** | pytest + pytest-asyncio |
| **Async mode** | `strict` (auto-detects async tests) |
| **Test location** | `kernel/tests/` |
| **Naming** | `test_<module>.py` for files, `test_<function>` for functions |
| **Coverage** | > 80% on kernel, > 60% on core |
| **Fixtures** | Use `conftest.py` for shared fixtures |

### 4.2 Test Structure

```python
import pytest
from kernel.events import Event, Subscription, EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_subscribe():
    bus = EventBus()
    received: list[Event] = []

    async def handler(event: Event) -> None:
        received.append(event)

    await bus.register(Subscription(topic="test.event", handler=handler))
    await bus.publish(Event(name="test.event", payload={"key": "value"}))

    assert len(received) == 1
    assert received[0].name == "test.event"
    assert received[0].payload == {"key": "value"}
```

### 4.3 Running Tests

```bash
make test                    # Run all kernel tests
python -m pytest kernel/tests/ -v --tb=short
python -m pytest kernel/tests/test_event_bus.py -v  # Single file
python -m pytest -k "test_retry"  # Filter by name
```

---

## 5. Security Rules

### 5.1 Secrets & Keys

- **NEVER** commit `.env`, `lumina_auth.json`, `lumina_secrets.json`, or any credential files
- Use `.env.example` as a template with dummy values
- API keys stored via `SecretsManager` with Fernet encryption
- Master key sourced from `LUMINA_MASTER_KEY` environment variable
- Rotate secrets regularly using `SecretsManager.rotate()`

### 5.2 Authentication

- Passwords hashed with PBKDF2-SHA256 (100,000 iterations, 16-byte salt)
- Session tokens use `secrets.token_urlsafe(32)`
- API keys prefixed with `l sk-` for easy identification
- Account lockout after 5 failed attempts (15-minute window)
- Rate limiting: 100 requests per 60 seconds (production mode)

### 5.3 Code Safety

- Use `secrets` module for cryptographic randomness (never `random`)
- Use `hmac.compare_digest()` for comparing hashes/tokens
- Validate all user input at API boundaries
- Sanitize shell commands before execution
- Sandbox plugin execution

---

## 6. Documentation Rules

| Rule | Standard |
|------|----------|
| **API docs** | Auto-generated by FastAPI at `/docs` (Swagger) |
| **Module docs** | Each `__init__.py` should have a one-line module description |
| **Public APIs** | Google-style docstrings with args, returns, raises |
| **Architecture** | Update `Architecture.md` when adding new modules |
| **Changelog** | Update `CHANGELOG.md` on each release |

---

## 7. Performance Rules

- Use `httpx.AsyncClient` with connection pooling (single shared client)
- Cache AI provider results where appropriate
- Use `asyncio.gather()` for parallel independent operations
- Memory engine: configurable TTLs to prevent unbounded growth
- Browser: reuse sessions and pages where possible
- Lazy-load non-critical modules

---

## 8. Error Handling

| Layer | Strategy |
|-------|----------|
| **Kernel** | Raise specific exceptions (`InvalidEventError`, `DuplicateSubscriberError`) |
| **Core** | Raise domain exceptions, log at appropriate level |
| **API** | Catch exceptions, return appropriate HTTP status codes + error messages |
| **Provider chain** | Catch and fallback, log warnings, raise `ProviderError` if all fail |
| **Event bus** | Catch subscriber errors, move failed events to DLQ |

```python
# Logging levels guide
log.debug("Detailed diagnostic info")    # Development only
log.info("Normal operational events")     # Registrations, successful operations
log.warning("Recoverable issues")         # Failed providers, retries
log.error("Errors that need attention")   # Failed operations, data loss
```

---

## 9. Dependency Management

- Core dependencies in `requirements.txt`
- Optional dependencies (cryptography, playwright) with graceful fallback
- No pinned patch versions in `requirements.txt` (use `>=`)
- Development dependencies via `pip install -e .` if needed

---

## 10. Plugin Development Rules

1. Every plugin must have a manifest (`plugin.json`) with: name, version, description, author, dependencies
2. Plugins use SemVer (`MAJOR.MINOR.PATCH`)
3. Plugin entry point: `plugin.py` with `setup(kernel)` function
4. Plugins communicate through the Event Bus (no direct imports of other plugins)
5. Plugins register services via `kernel.services.register()`
6. Unsigned plugins run in sandbox mode
7. Test your plugin with `make test` before submitting

---

## 11. Environment Variables

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OLLAMA_BASE_URL` | No | `http://localhost:11434` | Local LLM endpoint |
| `OLLAMA_MODEL` | No | `qwen2.5-coder:1.5b` | Local model name |
| `OPENAI_API_KEY` | No | — | OpenAI API key |
| `OPENROUTER_API_KEY` | No | — | OpenRouter API key |
| `GROQ_API_KEY` | No | — | Groq API key |
| `GEMINI_API_KEY` | No | — | Google Gemini API key |
| `DEEPSEEK_API_KEY` | No | — | DeepSeek API key |
| `LUMINA_MASTER_KEY` | No | — | Master encryption key |
| `LUMINA_ENV` | No | `development` | Environment: `development` / `production` |
| `AUTH_ENABLED` | No | `false` (dev) | Enable authentication |
| `CORS_ORIGINS` | No | `*` (dev) | Allowed CORS origins |
| `WHATSAPP_API_KEY` | No | — | WhatsApp Cloud API token |
| `WHATSAPP_PHONE_ID` | No | — | WhatsApp phone number ID |

---

## 12. Common Commands

```bash
# Development
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
cd lumina-ui && npm run dev -- --host 0.0.0.0

# Testing
make test
python -m pytest kernel/tests/ -v

# Linting
make lint      # ruff check
make fmt       # ruff format

# Docker
docker compose up -d
docker compose down
docker compose logs -f lumina-api

# CLI
lumina status
lumina chat "Hello"
lumina agent lead_gen "Find leads"
```
