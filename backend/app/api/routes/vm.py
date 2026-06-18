from fastapi import APIRouter

from app.observer import message_observer

router = APIRouter()


@router.get("/metrics")
async def get_current_metrics():
    return message_observer.latest_metrics


@router.get("/tasks")
async def get_node_tasks():
    return {"tasks": message_observer.latest_tasks}
