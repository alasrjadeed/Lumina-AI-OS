import enum
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, Enum
from sqlalchemy.sql import func
from backend.app.core.database import Base


class AgentStatus(str, enum.Enum):
    IDLE = "idle"
    BUSY = "busy"
    PROCESSING = "processing"
    ERROR = "error"
    OFFLINE = "offline"


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    role = Column(String(100))
    description = Column(Text)
    status = Column(Enum(AgentStatus), default=AgentStatus.IDLE)
    capabilities = Column(JSON, default=list)
    tasks_completed = Column(Integer, default=0)
    success_rate = Column(Integer, default=100)
    configuration = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    health_status = Column(String(50), default="healthy")
