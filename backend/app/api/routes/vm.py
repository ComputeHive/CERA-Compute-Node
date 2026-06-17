import json
from glob import glob

from app.enums import AppStatusEnum
from app.lib.utils import (
    edit_global_state,
    edit_node_config,
    load_global_state,
    load_node_config,
)
from app.models import RunVMRequest
from app.services.vm_manager import vm_manager
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/nodes")
async def list_nodes():
    configs = []
    for p in glob("/var/lib/cera/node_*_config.json"):
        with open(p) as f:
            configs.append(json.load(f))
    return {"nodes": configs}


@router.post("/nodes/{node_index}/run")
async def run_vm(node_index: str, request: RunVMRequest):
    cfg = load_node_config(node_index)

    if not cfg:
        raise HTTPException(status_code=404, detail="Node not registered")
    cfg.token = request.token
    edit_node_config(cfg)
    instance = vm_manager.get_or_create(node_index)
    if instance.is_running:
        await instance.vsock.stop()
        await instance.vsock.start()
        return {"status": "token sent"}
    try:
        await instance.start(cfg.cpu, cfg.ram, cfg.disk)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    current_state = load_global_state()
    current_state.app_state = AppStatusEnum.RUNNING
    edit_global_state(current_state)
    return {"status": "VM started"}


@router.post("/nodes/{node_index}/stop")
async def stop_vm(node_index: str):
    instance = vm_manager.get(node_index)
    if not instance or not instance.is_running:
        raise HTTPException(status_code=400, detail="VM is not running")
    await instance.stop()
    if not vm_manager.list_running():
        current_state = load_global_state()
        current_state.app_state = AppStatusEnum.READY
        edit_global_state(current_state)

    return {"status": "VM stopped"}


@router.get("/nodes/{node_index}/metrics")
async def get_current_metrics(node_index: str):
    instance = vm_manager.get(node_index)
    if not instance:
        raise HTTPException(status_code=404, detail="Node not found")
    return instance.vsock.latest_metrics


@router.get("/nodes/{node_index}/tasks")
async def get_node_tasks(node_index: str):
    instance = vm_manager.get(node_index)
    if not instance:
        raise HTTPException(status_code=404, detail="Node not found")
    return {"tasks": instance.vsock.latest_tasks}
