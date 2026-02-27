from fastapi import APIRouter, HTTPException
from app.services.vm_manager import vm_manager
from app.models import RunVMRequest

router = APIRouter()


@router.post("/run")
async def run_vm(request: RunVMRequest):
    try:
        await vm_manager.start(request.CPU, request.RAM, request.Disk)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "VM started", "config": vm_manager.vm_config}


@router.post("/stop")
async def stop_vm():
    if not vm_manager.is_running:
        raise HTTPException(status_code=400, detail="VM is not running")
    await vm_manager.stop()
    return {"status": "VM stopped"}
