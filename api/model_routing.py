from fastapi import APIRouter

from core.model_routing import model_router

router = APIRouter(prefix="/model-routing", tags=["Model Routing"])


@router.get("/models")
async def list_models():
    return {"models": model_router.get_available_models()}


@router.get("/routes")
async def get_routes():
    return {"routes": model_router.get_routes()}


@router.post("/routes/{task_type}")
async def update_route(task_type: str, strategy: str, models: str):
    model_list = [m.strip() for m in models.split(",") if m.strip()]
    result = model_router.update_route(task_type, strategy, model_list)
    if not result:
        return {"error": f"Invalid task_type '{task_type}' or strategy '{strategy}'"}, 400
    return {"route": result}


@router.get("/suggest")
async def suggest_model(task_type: str = "chat", prefer_cost: bool = False):
    result = model_router.suggest_model(task_type, prefer_cost=prefer_cost)
    return {"suggestion": result}


@router.get("/usage")
async def get_usage():
    return model_router.get_usage_stats()


@router.post("/usage/reset")
async def reset_usage():
    model_router.reset_usage()
    return {"reset": True}
