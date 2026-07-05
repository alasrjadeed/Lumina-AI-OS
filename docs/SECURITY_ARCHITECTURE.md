# Lumina AI OS — Security Architecture

## Authentication
- JWT-based access tokens (30 min expiry)
- Refresh tokens (7 day expiry)
- Passwords hashed with bcrypt
- API keys hashed with SHA-256

## Authorization
- Role-based access control (admin, user)
- Permission-based action validation
- Approval workflows for sensitive operations

## Input Validation
- All user input sanitized (dangerous characters removed)
- Command validation blocks dangerous system commands
- Maximum input length enforced (10,000 chars)

## Data Protection
- Secrets stored in encrypted vault
- No plaintext credentials in logs
- HTTPS in production
- CORS restricted to allowed origins

## Audit
- All AI actions logged to audit.log
- JSON-structured logs for machine parsing
- Timestamp with timezone for all events

## Secure Defaults
- Local AI (Ollama) as default provider
- All data stays on user's infrastructure
- Human approval required for destructive operations

## Threat Model
| Threat | Mitigation |
|--------|------------|
| Unauthorized access | JWT authentication |
| Code injection | Input sanitization + command validation |
| API key theft | Hashed storage, encrypted vault |
| Data breach | Local-first, user-controlled infrastructure |
| Privilege escalation | Role-based authorization |
