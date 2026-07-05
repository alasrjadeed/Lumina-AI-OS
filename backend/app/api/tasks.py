from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime

router = APIRouter()


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    command: Optional[str] = None
    parameters: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    id: int
    title: str
    status: str
    priority: str
    created_at: datetime
    completed_at: Optional[datetime] = None


@router.post("/", response_model=TaskResponse)
async def create_task(task: TaskCreate):
    return TaskResponse(
        id=1,
        title=task.title,
        status="pending",
        priority=task.priority,
        created_at=datetime.utcnow(),
    )


@router.get("/", response_model=List[TaskResponse])
async def list_tasks(skip: int = 0, limit: int = 50):
    return []


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int):
    raise HTTPException(status_code=404, detail="Task not found")


@router.delete("/{task_id}")
async def delete_task(task_id: int):
    return {"message": "Task deleted"}
