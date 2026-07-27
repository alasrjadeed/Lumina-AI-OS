# Lumina AI OS — Security Architecture

> **Version**: 1.0.0 | **Status**: Approved | **Updated**: July 2026

---

## 1. Security Overview

Lumina implements defense-in-depth with five security layers:

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Network Security                                │
│   CORS, Rate Limiting, Nginx Reverse Proxy, HTTPS        │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Authentication & Identity                       │
│   PBKDF2 Passwords, Sessions, API Keys, Account Lockout  │
├─────────────────────────────────────────────────────────┤
│ Layer 3: Authorization (RBAC + ABAC)                     │
│   Roles, Permissions, Policies, Role Inheritance         │
├─────────────────────────────────────────────────────────┤
│ Layer 4: Data Protection                                 │
│   Fernet Encryption, Secrets Vault, HMAC, Key Rotation   │
├─────────────────────────────────────────────────────────┤
│ Layer 5: Audit & Monitoring                              │
│   Tamper-Evident Audit Chain, Structured Logging         │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Authentication System

### 2.1 Password Storage

```python
# PBKDF2-SHA256 with per-user random salt
salt = secrets.token_hex(16)                           # 32 hex chars = 16 bytes
hash = hashlib.pbkdf2_hmac("sha256", password, salt, 100000)  # 100k iterations
stored = f"{salt}:{hash.hex()}"                        # Combined format
```

| Property | Value |
|----------|-------|
| Algorithm | PBKDF2-SHA256 |
| Iterations | 100,000 |
| Salt length | 16 bytes (32 hex chars) |
| Output length | 32 bytes (64 hex chars) |

### 2.2 Session Management

```python
# Session tokens
token = f"l_ses_{secrets.token_urlsafe(32)}"  # 43 chars

# Configurable expiry
session_expiry: 3600 seconds (1 hour, default)
token_expiry: 86400 seconds (24 hours)

# Stored in-memory, flushed on restart
```

### 2.3 API Key Authentication

```python
# API key format
key = f"l sk-{secrets.token_hex(32)}"  # "l sk-" prefix + 64 hex chars

# One key per user, multiple keys supported
# Validated on each request: user must exist and be enabled
```

### 2.4 Account Lockout

| Parameter | Value |
|-----------|-------|
| Max failed attempts | 5 |
| Lockout window | 900 seconds (15 minutes) |
| Tracking | Timestamp-based sliding window |
| Reset | Automatic after window expires or on successful login |

```python
# Lockout flow
attempts = [timestamp_of_failed_login, ...]  # Sliding window
if len(recent_attempts) >= 5:
    return "Account locked"  # 401 Unauthorized
```

### 2.5 Password Policy

| Rule | Value |
|------|-------|
| Minimum length | 8 characters |
| Change password | Requires old password verification |
| Storage | Never logged, never returned in API responses |

---

## 3. Authorization System (RBAC)

### 3.1 Default Roles

```python
Role("admin", permissions=[
    Permission(resource="*", action="*")           # Full access
])

Role("user", permissions=[
    Permission(resource="chat", action="create"),
    Permission(resource="chat", action="read"),
    Permission(resource="profile", action="*"),     # Full profile access
])

Role("viewer", permissions=[
    Permission(resource="chat", action="read"),     # Read-only chat
    Permission(resource="profile", action="read"),  # Read-only profile
])
```

### 3.2 Role Inheritance

```python
Role("manager", inherits=["user"], permissions=[
    Permission(resource="crm", action="*"),
    Permission(resource="reports", action="read"),
])

Role("developer", inherits=["user"], permissions=[
    Permission(resource="plugins", action="*"),
    Permission(resource="api", action="*"),
])
```

Permission resolution recursively walks the inheritance tree (cycle-safe with visited set).

### 3.3 Attribute-Based Policies

```python
Policy(
    name="block-suspicious-ips",
    effect="deny",                                  # Explicit deny
    resources=["*"],
    actions=["*"],
    subjects=["*"],
)

Policy(
    name="allow-internal-tools",
    effect="allow",
    resources=["browser", "desktop", "android"],    # Specific resources
    actions=["*"],
    subjects=["admin", "developer"],                # Specific roles
)
```

Policy evaluation: **explicit deny > explicit allow > implicit deny**.

### 3.4 Permission Check Flow

```
Request → Extract user roles → Resolve inherited permissions →
         → Check direct permission match (resource + action + conditions) →
         → Check policies (allow/deny) →
         → Allow or Deny (403 Forbidden)
```

---

## 4. Encryption

### 4.1 Symmetric Encryption (Fernet)

```python
# Key derivation from master key
derived_key = base64.urlsafe_b64encode(hashlib.sha256(master_key).digest())
fernet = Fernet(derived_key)

# Encrypt
ciphertext = fernet.encrypt(plaintext.encode()).decode()

# Decrypt
plaintext = fernet.decrypt(ciphertext.encode()).decode()
```

### 4.2 Fallback Cipher (XOR)

When `cryptography` library is unavailable, a simple XOR cipher with the master key provides basic obfuscation:

```python
# XOR encrypt (NOT cryptographically secure — Fernet strongly recommended)
result = bytearray()
for i, c in enumerate(data):
    result.append(c ^ ord(key[i % len(key)]))
```

### 4.3 Asymmetric Encryption (RSA)

```python
KeyPair(
    public_key="-----BEGIN PUBLIC KEY-----...",
    private_key="-----BEGIN PRIVATE KEY-----...",
    algorithm="RSA-2048",
)
```

### 4.4 HMAC Signing

```python
# Sign
signature = hmac.new(key, data, hashlib.sha256).hexdigest()

# Verify (constant-time comparison)
hmac.compare_digest(expected, signature)
```

### 4.5 File Encryption

```python
# Encrypt file to .enc
encrypt_file("secret.txt", master_key)  # → "secret.txt.enc"

# Decrypt file from .enc
decrypt_file("secret.txt.enc", master_key)  # → "secret.txt.dec"
```

---

## 5. Secrets Management

### 5.1 Secrets Vault

```python
secrets_manager = SecretsManager(
    storage_path="lumina_secrets.json",
    master_key=os.environ.get("LUMINA_MASTER_KEY"),
)

# Store with encryption
secrets_manager.set("openai_key", "sk-...", tags=["ai", "production"])

# Retrieve (auto-decrypts)
api_key = secrets_manager.get("openai_key")

# Rotate
secrets_manager.rotate("openai_key", "sk-new-...")

# Search by tag
ai_secrets = secrets_manager.search_by_tag("ai")
```

### 5.2 Secret Lifecycle

```
Create → Store (encrypted with Fernet) → Use (auto-decrypt) → Rotate (new version) → Delete
```

### 5.3 Best Practices

- **Never** log secret values (keys, tokens, passwords)
- **Never** return secrets in API responses (strip from responses)
- Rotate secrets every 90 days (use `rotate_all()` with a generator)
- Export secrets only to encrypted backup
- Use `LUMINA_MASTER_KEY` environment variable (never hardcode)

---

## 6. Audit System

### 6.1 Tamper-Evident Chain

Each audit event is cryptographically linked to the previous event:

```python
class AuditEvent:
    id: str                    # evt_{timestamp}_{index}
    action: str                # login, file_read, api_call
    actor: str                 # username or system
    resource: str              # affected resource
    result: str                # success / failure
    details: dict              # extra context
    timestamp: float           # Unix timestamp
    ip: str                    # client IP
    previous_hash: str         # SHA-256 of previous event
    hash: str                  # SHA-256 of this event's data

# Hash computation
hash = SHA256(f"{id}:{action}:{actor}:{resource}:{result}:{timestamp}:{previous_hash}")
```

### 6.2 Chain Verification

```python
# Verify entire chain
corrupted_indices = audit.verify_chain()  # Returns list of indices that fail

# Verify single event
is_valid = audit.verify_event(index)
```

If any event is modified, its `hash` won't match the recomputed hash, and all subsequent events will also fail (because `previous_hash` breaks the chain).

### 6.3 Export Formats

- **JSON**: Full structured export
- **CSV**: Tabular export for spreadsheet analysis

### 6.4 Query Capabilities

```python
audit.query(action="login", actor="admin", limit=100)
audit.get_recent(limit=50)
audit.get_by_user("john_doe", limit=50)
audit.get_failures(limit=50)  # All failed actions
```

---

## 7. Network Security

### 7.1 CORS Configuration

```python
# Development: allow all origins
CORS_ORIGINS = "*"

# Production: restricted origins
CORS_ORIGINS = "http://localhost:5173,https://lumina.example.com"
```

### 7.2 Rate Limiting

| Environment | Limit |
|-------------|-------|
| Development | Disabled |
| Production | 100 requests per 60 seconds per IP |

Implemented as FastAPI middleware. Returns `429 Too Many Requests` when exceeded.

### 7.3 Nginx Reverse Proxy (Production)

```nginx
# TLS termination
# Rate limiting at edge
# Request size limits
# Security headers:
#   X-Content-Type-Options: nosniff
#   X-Frame-Options: DENY
#   X-XSS-Protection: 1; mode=block
#   Content-Security-Policy: default-src 'self'
```

---

## 8. Plugin Security

### 8.1 Sandbox Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Trusted** | Full access to kernel APIs | Built-in plugins, signed third-party |
| **Sandboxed** | Restricted imports, resource limits | Community plugins, untrusted code |

### 8.2 Sandbox Restrictions

- Restricted module imports (whitelist)
- CPU time limits
- Memory limits
- No file system access outside plugin directory
- No network access without explicit permission

### 8.3 Plugin Vetting

1. Manifest validation (required fields, version format)
2. Dependency resolution (no circular deps)
3. Version compatibility check (SemVer matching)
4. Code review for trusted status

---

## 9. Deployment Security

### 9.1 Environment Variables

All secrets must be passed via environment variables or Docker secrets:
- `LUMINA_MASTER_KEY` — Encryption master key
- `OPENAI_API_KEY`, `GEMINI_API_KEY`, etc. — Provider API keys
- `WHATSAPP_API_KEY` — WhatsApp Cloud API token

### 9.2 Docker Security

- Run as non-root user (Python 3.12-slim default)
- No secrets in Dockerfile (use build args or runtime env)
- Health checks for all services
- Read-only root filesystem where possible
- Network isolation via Docker bridge network

### 9.3 File Permissions

| File | Permission | Owner |
|------|-----------|-------|
| `lumina_auth.json` | `600` (read/write owner only) | app user |
| `lumina_secrets.json` | `600` | app user |
| `lumina_audit.json` | `600` | app user |
| `.env` | `600` | app user |
| Data directories | `700` | app user |

---

## 10. Threat Model

### 10.1 Assets

| Asset | Sensitivity | Impact if Compromised |
|-------|-------------|----------------------|
| User credentials | Critical | Full account takeover |
| API keys | Critical | Unauthorized AI usage, financial loss |
| Secrets vault | Critical | All encrypted data exposed |
| Audit log | High | Loss of forensic capability |
| CRM data | High | Business data leak |
| Conversation history | Medium | Privacy breach |
| Plugin code | Medium | Malicious code execution |

### 10.2 Threat Mitigations

| Threat | Mitigation |
|--------|-----------|
| Password brute-force | PBKDF2 100k iterations, account lockout |
| Session hijacking | Short-lived tokens (1h), HTTPS in production |
| API key leakage | Encrypted at rest, revocable, prefixed for detection |
| SQL/Command injection | Input validation, parameterized commands |
| XSS | React auto-escaping, CSP headers in production |
| CSRF | SameSite cookies, token-based auth |
| Man-in-the-middle | HTTPS via Nginx, TLS termination |
| Privilege escalation | RBAC with explicit deny policies |
| Audit tampering | SHA-256 chained hashing, chain verification |
| Malicious plugins | Sandboxed execution, restricted imports |
| Data exfiltration | Network isolation, audit logging |

### 10.3 Incident Response

1. **Detect**: Monitor logs, audit failures, rate limit hits
2. **Contain**: Revoke compromised API keys, lock affected accounts
3. **Investigate**: Query audit log by actor and time window
4. **Recover**: Rotate all secrets, restore from backup if needed
5. **Report**: Document incident in audit log, notify affected users

---

## 11. Compliance & Best Practices

| Standard | Implementation |
|----------|---------------|
| **OWASP Top 10** | Input validation, output encoding, auth, access control, logging |
| **NIST 800-63B** | PBKDF2 password hashing, account lockout, session management |
| **GDPR (ready)** | Audit all data access, export user data, delete on request |
| **SOC 2 (ready)** | Audit chain, access controls, encryption at rest, monitoring |

---

## 12. Security Checklist

- [x] Passwords hashed with PBKDF2-SHA256 (100k iterations)
- [x] Session tokens use `secrets.token_urlsafe(32)`
- [x] API keys prefixed for easy detection in logs
- [x] RBAC with role inheritance and policy evaluation
- [x] Fernet encryption with master-key derivation
- [x] Secrets vault with rotation and tagging
- [x] Audit chain with SHA-256 tamper detection
- [x] Rate limiting in production mode
- [x] Account lockout after 5 failed attempts
- [x] CORS with configurable origins
- [x] Health check endpoints for monitoring
- [x] Structured logging with log levels
- [ ] HTTPS enforcement in production (via Nginx)
- [ ] Security.txt file
- [ ] Dependency vulnerability scanning (Dependabot)
- [ ] Regular penetration testing
