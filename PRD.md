# Lumina AI OS — Product Requirements Document

> **Version**: 1.0.0 | **Status**: Approved | **Updated**: July 2026

---

## 1. Product Overview

### 1.1 Elevator Pitch

Lumina is an autonomous AI employee operating system that provides businesses and individuals with a unified platform for AI chat, workflow automation, browser control, voice interaction, CRM, SEO, marketing, and developer tools — all running locally, in the cloud, or in hybrid mode.

### 1.2 Target Audience

| Segment | Persona | Primary Use Case |
|---------|---------|-----------------|
| **Small Business Owners** | Non-technical entrepreneurs | CRM, marketing, lead generation, automation |
| **Developers** | Software engineers, freelancers | Code generation, browser testing, API integrations |
| **Marketing Teams** | Content creators, SEO specialists | Content writing, SEO analysis, social media |
| **Enterprise** | IT admins, operations teams | On-premise AI, workflow automation, compliance |
| **Power Users** | Productivity enthusiasts | Desktop automation, voice control, personal AI |

### 1.3 Problem Statement

Existing AI tools are fragmented: chatbots in one tab, CRM in another, browser automation requires separate scripts, and nothing integrates voice, desktop control, and business tools into one platform. Lumina solves this by unifying everything under a single kernel with a plugin architecture.

---

## 2. Core Requirements

### 2.1 Functional Requirements

#### FR-01: Multi-Provider AI Chain
- Support at least 6 AI providers with automatic fallback
- Free-tier-first ordering: Ollama → OpenRouter → Groq → Gemini → DeepSeek → OpenAI
- Configurable timeouts, retry with exponential backoff + jitter
- Streaming and non-streaming completion modes
- Provider health monitoring and status API

#### FR-02: Specialized Agent System
- 19+ pre-built specialized agents across base, specialized, and content categories
- Agent lifecycle: OBSERVE → THINK → PLAN → ASSIGN → EXECUTE → VERIFY → REPORT
- Agent manager for dispatch, routing, and result aggregation
- Extensible agent framework for custom agents

#### FR-03: Memory Engine
- 8-layer memory architecture: Working, Short-Term, Long-Term, Episodic, Semantic, Vector, Embeddings, Recall
- Persistent storage with JSON file backing
- Cross-layer recall with semantic search and ranking
- Conversation history with TTL-based retention

#### FR-04: Browser Automation
- Playwright-based headless and headed browser control
- Navigation, clicking, form filling, content extraction, screenshots
- Multi-tab management, session persistence, download handling
- Network interception and DOM interaction APIs

#### FR-05: Desktop Automation
- File system operations: list, read, write, copy, move, delete, mkdir
- Shell command execution with output capture
- System information retrieval (OS, CPU, memory, disk)
- Application launch and process management

#### FR-06: Android Integration
- ADB-based device discovery and connection
- Screen tap, text input, key events, swipe gestures
- APK installation, package management, logcat viewing
- Screenshot capture, device info retrieval

#### FR-07: WhatsApp Integration
- WhatsApp Cloud API messaging (text, templates, images, documents)
- Connection status monitoring
- Template management (list, create)
- Phone number validation

#### FR-08: CRM Pipeline
- Contact management with CRUD operations
- Deal pipeline: LEAD → QUALIFIED → PROPOSAL → NEGOTIATION → CLOSED_WON / CLOSED_LOST
- Activity logging, sales summary analytics
- Persistent JSON data store

#### FR-09: SEO Toolkit
- Site registration and tracking
- HTML page analysis (meta tags, headings, structure, performance)
- Meta tag generation with keyword targeting
- Audit history with queryable log
- Competitor analysis

#### FR-10: Plugin System
- Plugin discovery from directories
- Lifecycle hooks: load, enable, disable, unload
- Dependency resolution between plugins
- Sandboxed execution for untrusted plugins
- Semantic versioning and compatibility checking
- 7 built-in plugins: SEO, CRM, WhatsApp, Email, Leads, Marketing, Reporting

#### FR-11: Kernel System
- Event Bus: pub/sub with wildcard topics, history, dead-letter queue, retry, priority
- Service Registry: named service registration and resolution
- DI Container: singleton, scoped, transient lifetimes with decorator support
- Scheduler: delayed, recurring, and retryable jobs
- Plugin Loader: discover, validate, and load plugins

#### FR-12: Voice Interaction (Jarvis)
- Wake word detection ("Jarvis" or configurable)
- Speech-to-text via Whisper or Google STT
- Text-to-speech via ElevenLabs or gTTS
- Voice command routing with entity extraction
- Continuous listening mode with auto-restart

#### FR-13: Vision System
- Camera device abstraction with multi-camera support
- Object detection, face detection/recognition
- Scene description using AI
- Video stream processing
- Visual cortex for unified vision pipeline

#### FR-14: Multi-Interface Support
- **Web Dashboard** (React 19 + TypeScript + Tailwind v4): Chat, Code Generator, Agents, Settings, 14+ pages
- **CLI** (`lumina` command): Chat, code gen, agents, CRM, SEO, file ops
- **VS Code Extension**: 8 commands with keyboard shortcuts
- **Flutter Mobile App**: Dashboard and Chat screens for iOS/Android
- **MCP Server**: 14 tools exposed to MCP-compatible AI clients (Claude Desktop, Cursor)

#### FR-15: Security
- PBKDF2-SHA256 password hashing (100,000 iterations) with per-user salt
- Session tokens with configurable expiry
- API key authentication (`l sk-` prefix)
- Role-Based Access Control with role inheritance
- Attribute-Based Policy evaluation
- Fernet symmetric encryption with fallback XOR cipher
- Secrets vault with encryption at rest, rotation, and tagging
- Tamper-evident audit chain with SHA-256 hashing
- Rate limiting middleware (100 req/min in production mode)
- Account lockout after 5 failed attempts (15 min lockout)

#### FR-16: API Layer
- FastAPI with 39 routers and 80+ endpoints
- CORS middleware with configurable origins
- Rate limiting middleware in production mode
- Swagger/OpenAPI documentation at `/docs`
- Health check endpoint at `/system/health`
- Kernel status endpoint at `/kernel/status`
- Proxy endpoint for iframe embedding with URL rewriting

#### FR-17: Deployment
- Docker multi-stage build (production + development targets)
- Docker Compose multi-service: API, Ollama, UI
- Nginx reverse proxy configuration
- GitHub Actions CI/CD pipeline
- Health checks with auto-restart

### 2.2 Non-Functional Requirements

| ID | Requirement | Target |
|----|------------|--------|
| NFR-01 | API response time (p95) | < 500ms for chat, < 200ms for CRUD |
| NFR-02 | AI provider fallback time | < 3s per provider attempt |
| NFR-03 | Concurrent connections | 100+ simultaneous HTTP clients |
| NFR-04 | Test coverage | > 80% on kernel, > 60% on core |
| NFR-05 | Memory usage (idle) | < 256MB |
| NFR-06 | Startup time | < 5s from cold start |
| NFR-07 | Browser automation reliability | > 95% success rate |
| NFR-08 | Plugin sandbox isolation | Process-level isolation |
| NFR-09 | Audit log immutability | SHA-256 chained hashing |
| NFR-10 | Password security | PBKDF2-SHA256, 100k iterations, 16-byte salt |

---

## 3. User Stories

### 3.1 Business Owner

> "As a small business owner, I want to manage my contacts, deals, and marketing campaigns from one dashboard so I don't need 5 different SaaS tools."

**Acceptance Criteria:**
- Add contacts via chat or CRM UI
- Create and move deals through pipeline stages
- View sales summary with key metrics
- Generate SEO meta tags for website pages
- Send WhatsApp messages to customers

### 3.2 Developer

> "As a developer, I want to generate code, automate browser testing, and control my desktop from a unified CLI so I can ship faster."

**Acceptance Criteria:**
- Generate code in 8+ languages via `/code` command
- Navigate, fill forms, and extract data from web pages
- Execute shell commands and manage files from API
- Build and install custom plugins
- Use VS Code extension for in-IDE AI assistance

### 3.3 Marketing Specialist

> "As a marketing specialist, I want AI to help me write content, analyze SEO, and run campaigns across channels."

**Acceptance Criteria:**
- Generate blog posts, social media content, and email copy
- Analyze website HTML for SEO issues
- Track keyword rankings and site health
- Schedule and manage marketing campaigns
- Export reports in CSV, JSON, or HTML

### 3.4 IT Administrator

> "As an IT admin, I want to deploy Lumina on-premise with proper security, auditing, and user management."

**Acceptance Criteria:**
- Docker Compose one-command deployment
- User registration with role assignment
- API key management (create, revoke)
- Audit log with chained hashing (tamper detection)
- Secrets vault with encryption at rest
- Rate limiting and account lockout

### 3.5 Power User

> "As a power user, I want voice control, desktop automation, and a personal AI that remembers my preferences."

**Acceptance Criteria:**
- Wake word detection for hands-free operation
- Voice commands for system actions
- File management via natural language
- Persistent memory across sessions
- Custom slash commands and shortcuts

---

## 4. Success Metrics

| Metric | Current | Target (v1.0) | Target (v1.5) |
|--------|---------|---------------|---------------|
| API endpoints | 80+ | 100 | 150 |
| Test count | 1,112+ | 1,200 | 2,000 |
| AI providers | 8 | 8 | 10 |
| Specialized agents | 19 | 20 | 30 |
| Plugin ecosystem | 7 built-in | 10 built-in | Community marketplace |
| Web dashboard pages | 14 | 20 | 30 |
| Response time (p95) | < 500ms | < 400ms | < 300ms |
| Concurrent users | 10 (tested) | 50 | 200 |
| Uptime (cloud mode) | 99% | 99.5% | 99.9% |

---

## 5. Constraints & Assumptions

### Constraints
- Python 3.12+ required (uses modern type hints and pattern matching)
- Ollama must be installed and running for local AI (optional)
- Playwright browsers must be installed for browser automation
- ADB required for Android features
- Microphone required for voice features
- Facebook Business account required for WhatsApp API

### Assumptions
- Users have basic technical literacy (CLI usage is optional, not required)
- Internet connection available for cloud AI providers
- Docker available for containerized deployment
- Node.js 18+ for frontend development
- Flutter SDK for mobile app development

---

## 6. Future Scope

- **Multi-tenant support**: Isolated workspaces for teams
- **Plugin marketplace**: Community plugin sharing and rating
- **Workflow visual editor**: Drag-and-drop automation builder
- **LLM fine-tuning**: Custom model training on user data
- **Mobile push notifications**: Real-time alerts on iOS/Android
- **OAuth/SSO**: Google, GitHub, Microsoft login integration
- **WebSocket streaming**: Real-time chat and agent streaming
- **Distributed mode**: Multi-node kernel for horizontal scaling
- **GraphQL API**: Alternative to REST for complex queries
- **Telemetry dashboard**: Usage analytics and performance monitoring
