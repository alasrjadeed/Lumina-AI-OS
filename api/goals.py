"""Goals & Todos API routes."""

from fastapi import APIRouter, HTTPException, Query

from core.goals import GoalStatus, TodoStatus, goal_store

router = APIRouter(prefix="/goals", tags=["Goals"])


@router.get("")
async def list_goals(status: str | None = None):
    goal_status = GoalStatus(status) if status else None
    return {"goals": [g.to_dict() for g in goal_store.list_goals(goal_status)]}


@router.post("")
async def create_goal(title: str, description: str = "", tags: str = "", thread_id: str | None = None):
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []
    goal = goal_store.create_goal(title=title, description=description, tags=tag_list, thread_id=thread_id)
    return {"goal": goal.to_dict()}


@router.get("/{goal_id}")
async def get_goal(goal_id: str):
    goal = goal_store.get_goal(goal_id)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goal": goal.to_dict(), "todos": [t.to_dict() for t in goal_store.list_todos(goal_id=goal_id)]}


@router.patch("/{goal_id}")
async def update_goal(goal_id: str, title: str | None = None, description: str | None = None, status: str | None = None, tags: str | None = None):
    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if status is not None:
        kwargs["status"] = status
    if tags is not None:
        kwargs["tags"] = [t.strip() for t in tags.split(",") if t.strip()]
    goal = goal_store.update_goal(goal_id, **kwargs)
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"goal": goal.to_dict()}


@router.delete("/{goal_id}")
async def delete_goal(goal_id: str):
    ok = goal_store.delete_goal(goal_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"deleted": True}


@router.get("/{goal_id}/todos")
async def list_goal_todos(goal_id: str, status: str | None = None):
    todo_status = TodoStatus(status) if status else None
    if not goal_store.get_goal(goal_id):
        raise HTTPException(status_code=404, detail="Goal not found")
    return {"todos": [t.to_dict() for t in goal_store.list_todos(status=todo_status, goal_id=goal_id)]}


@router.post("/todos")
async def create_todo(title: str, goal_id: str | None = None, description: str = "", priority: int = 0, thread_id: str | None = None):
    todo = goal_store.create_todo(title=title, goal_id=goal_id, description=description, priority=priority, thread_id=thread_id)
    return {"todo": todo.to_dict()}


@router.get("/todos/{todo_id}")
async def get_todo(todo_id: str):
    todo = goal_store.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"todo": todo.to_dict()}


@router.patch("/todos/{todo_id}")
async def update_todo(todo_id: str, title: str | None = None, description: str | None = None, status: str | None = None, priority: int | None = None, assignee: str | None = None):
    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if description is not None:
        kwargs["description"] = description
    if status is not None:
        kwargs["status"] = status
    if priority is not None:
        kwargs["priority"] = priority
    if assignee is not None:
        kwargs["assignee"] = assignee
    todo = goal_store.update_todo(todo_id, **kwargs)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"todo": todo.to_dict()}


@router.post("/todos/{todo_id}/move")
async def move_todo(todo_id: str, status: str = Query(...)):
    try:
        new_status = TodoStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}. Choose from {[s.value for s in TodoStatus]}")
    todo = goal_store.move_todo(todo_id, new_status)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"todo": todo.to_dict()}


@router.delete("/todos/{todo_id}")
async def delete_todo(todo_id: str):
    ok = goal_store.delete_todo(todo_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"deleted": True}


@router.get("/board/kanban")
async def get_kanban():
    return {"columns": goal_store.get_kanban()}


@router.get("/stats")
async def get_stats():
    return goal_store.get_stats()
