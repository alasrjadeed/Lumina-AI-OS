# Lumina AI OS — Database Architecture

## Entities

### users
Stores user accounts, authentication, preferences, and permissions.

### tasks
Stores task definitions, status, priority, assignments, execution history, and approval workflows.

### agents
Stores AI agent configurations, capabilities, performance metrics, and health status.

### memory
(Work Memory — file-based JSON persistence in memory_store/)
Stores project contexts, decisions, bugs, and task states.

### chroma_db
(Vector database for semantic memory)
Stores embeddings for semantic search and context retrieval.

## Relationships
- User has many Tasks (user_id FK)
- Task has one User approver (approved_by FK)
- Task has one assigned Agent (assigned_agent string)
- User has one Agent configuration (ai_configuration JSON)

## Key Design Decisions
- Async SQLAlchemy for non-blocking DB operations
- Connection pooling (20 pool size)
- JSON columns for flexible schema (preferences, permissions, configurations)
- Timestamps with timezone awareness
- Soft-delete not needed; tasks preserve history via status changes
