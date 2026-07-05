# Lumina AI OS — API Architecture

## Design Principles
- RESTful endpoints with predictable URL patterns
- JSON request/response format
- JWT-based authentication
- Async handlers for all I/O operations
- WebSocket for real-time communication

## Base URL
`/api/`

## Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/register | Create account |
| POST | /auth/login | Get JWT tokens |
| POST | /auth/refresh | Refresh access token |
| GET | /auth/me | Current user info |

## Core APIs
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | System info |
| GET | /health | Health check |
| WS | /ws | Real-time communication |

## Tasks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /tasks | Create task |
| GET | /tasks | List tasks |
| GET | /tasks/:id | Get task |
| DELETE | /tasks/:id | Delete task |

## Explain Mode
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /explain/text | Explain topic |
| POST | /explain/code | Explain code |
| POST | /explain/document | Explain document |
| POST | /explain/website | Explain webpage |
| POST | /explain/report | Explain report |

## Reader
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /reader/read | Read file/text |
| POST | /reader/command | Reader controls |

## Voice
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /voice/speak | Text to speech |
| POST | /voice/recognize | Speech to text |
| POST | /voice/stop | Stop playback |

## Developer Platform
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /developer/generate | Generate code |
| POST | /developer/review | Review code |
| POST | /developer/debug | Debug code |
| POST | /developer/refactor | Refactor code |
| POST | /developer/test | Generate tests |
| POST | /developer/terminal/create | Create terminal |
| POST | /developer/terminal/exec | Execute command |

## Desktop
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /desktop/files | List files |
| POST | /desktop/files/read | Read file |
| POST | /desktop/files/write | Write file |
| POST | /desktop/files/copy | Copy file |
| POST | /desktop/files/move | Move file |
| POST | /desktop/files/delete | Delete file |

## Browser
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /browser/navigate | Navigate to URL |
| GET | /browser/content | Get page content |
| POST | /browser/screenshot | Take screenshot |
| POST | /browser/click | Click element |
| POST | /browser/fill | Fill form field |

## CRM
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /crm/leads | Create lead |
| GET | /crm/leads | List leads |
| GET | /crm/leads/:id | Get lead |
| POST | /crm/proposals | Generate proposal |
| POST | /crm/quotations | Generate quotation |
| POST | /crm/followups | Schedule follow-up |
| POST | /crm/calendar | Create event |
| POST | /crm/workspaces/:company | Create workspace |

## Marketing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /marketing/seo/analyze | SEO analysis |
| POST | /marketing/content/blog | Write blog |
| POST | /marketing/content/social | Social post |
| POST | /marketing/design/logo | Logo design |
| POST | /marketing/analytics/report | Analytics |

## Response Format
```json
{
  "status": "success",
  "data": {},
  "error": null
}
```

## Error Format
```json
{
  "detail": "Error message"
}
```
