# Lumina AI OS — Product Constitution

## Preamble
Lumina AI OS is built to function as a digital employee, not a chatbot.
Every architectural decision serves this vision.

## Core Principles

### 1. Core-First Development
Nothing is built unless the Core supports it.
All features are extensions of the kernel, not patches on top of it.

### 2. AI Independence
Lumina must never be dependent on a single AI provider.
The AI Provider Layer abstracts all model interactions.
Switching providers must never require code changes outside the provider layer.

### 3. Production Quality
Every file includes:
- Type hints
- Docstrings
- Structured logging
- Error handling
- Unit tests

No throwaway code. Ever.

### 4. Human-in-the-Loop
Lumina is autonomous but accountable.
Always ask before:
- Deleting data
- Production deployment
- Payments
- Signing contracts

### 5. Privacy by Design
All sensitive data is stored locally by default.
Credentials are stored in encrypted vaults.
User data never leaves the user's infrastructure without explicit consent.

### 6. Modular Architecture
Each AI agent is an independent module.
Agents communicate through the Event Bus, never directly.
Services are registered through the Service Registry, never hard-coded.
Dependencies are resolved through the DI Container, never imported directly.

### 7. Work Memory
Lumina remembers projects, not conversations.
Project context (architecture, decisions, bugs, tasks) persists across sessions.
"Open the Restaurant ERP project" restores full working context instantly.

### 8. Extensibility
All features are plugins.
The Plugin System is the primary extension mechanism.
The Plugin Marketplace allows third-party extensions.

### 9. Security
API keys are hashed, never stored in plain text.
Input sanitization is applied to all user commands.
Command validation prevents dangerous system operations.
Audit logs track all AI actions.

### 10. Scalability
Async-first architecture throughout the codebase.
Event-driven communication between components.
Scheduled jobs run in a pool of workers.
Database connections are pooled and managed.

## Development Workflow
Epic -> Version -> Sprint -> Task -> Module -> Feature -> Testing -> Release

## Technology Stack
- Core Language: Python 3.11+
- Backend: FastAPI + SQLAlchemy (async)
- Database: PostgreSQL + ChromaDB (vector)
- Cache/Queue: Redis
- Desktop: Electron + React / Tauri
- Frontend: React + TypeScript + Vite
- Mobile: Flutter
- AI Providers: Ollama, OpenAI, Anthropic, OpenRouter (abstracted)
- Deployment: Docker + Kubernetes (enterprise)

## Versioning
This constitution is version-controlled alongside the code.
Changes to this document require the same review process as code changes.
