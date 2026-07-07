# Volume 10: Security Guide

## Authentication

### Methods
| Method | Header | Use Case |
|--------|--------|----------|
| Master Key | `Authorization: Bearer <key>` | Admin access |
| API Key | `X-API-Key: <key>` | Programmatic access |
| JWT | `Authorization: Bearer <jwt>` | User sessions |

### Configuration
```bash
# .env
AUTH_ENABLED=true
API_KEYS=key1,key2,key3
LUMINA_MASTER_KEY=your-master-key
```

## Authorization (RBAC)

| Role | Permissions |
|------|-------------|
| admin | `*:*` — full access |
| user | `chat:*`, `profile:*` |
| viewer | `chat:read`, `profile:read` |

Custom roles and policies can be added via `core/security/authorization.py`.

## Encryption

### At Rest
- Secrets encrypted with **Fernet (AES-128-CBC)** via `cryptography` library
- Master key from `LUMINA_MASTER_KEY` env var
- Fallback to XOR + base64 if cryptography not installed

### In Transit
- API supports HTTPS via reverse proxy (Nginx)
- CORS restricted to configured origins

### Hashing
- Passwords: **PBKDF2-HMAC-SHA256** with random 16-byte salt, 100,000 iterations
- Audit chain: **SHA-256** hash linking

## Secrets Management

```python
from core.security.secrets import SecretsManager

sm = SecretsManager(master_key="your-key")
sm.set("db_password", "secret123", tags=["database"])
sm.get("db_password")  # "secret123"
sm.rotate("db_password", "new-secret")
```

## Audit Logging

Tamper-evident chain:
```
Event[0]: hash=SHA256(data[0])
Event[1]: hash=SHA256(data[1] + hash[0])
Event[2]: hash=SHA256(data[2] + hash[1])
```

Verification detects any modification:
```python
al.verify_chain()  # returns list of tampered indices
```

## Rate Limiting

Not yet implemented — planned for v1.1.

## Security Checklist

- [ ] Auth enabled in production
- [ ] CORS origins restricted
- [ ] Master key set via environment
- [ ] API keys rotated periodically
- [ ] HTTPS configured
- [ ] Audit logging enabled
- [ ] Secrets encrypted at rest
- [ ] Regular backup rotation
- [ ] Plugin permissions reviewed
