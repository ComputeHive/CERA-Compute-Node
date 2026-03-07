from fastapi import APIRouter, HTTPException
from app.services.vm_manager import vm_manager
from app.models.run_vm_req import RunVMRequest
from app.lib.utils import edit_state_file, load_state_file
from app.enums import AppStatusEnum
from app.schemas import AppStateModel
from app.services.vsock_listener import vsock_listener

router = APIRouter()


@router.post("/run")
async def run_vm(request: RunVMRequest):
    print(request)
    current_state = load_state_file()
    try:
        await vm_manager.start(request.CPU, request.RAM, request.Disk)
        edit_state_file(
            AppStateModel(
                app_state=AppStatusEnum.RUNNING,
                installed_tools=current_state.installed_tools,
            )
        )
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "VM started"}


@router.post("/stop")
async def stop_vm():
    if not vm_manager.is_running:
        raise HTTPException(status_code=400, detail="VM is not running")
    current_state = load_state_file()
    await vm_manager.stop()
    edit_state_file(
        AppStateModel(
            app_state=AppStatusEnum.READY, installed_tools=current_state.installed_tools
        )
    )
    return {"status": "VM stopped"}


@router.get("/metrics")
async def get_current_metrics():
    return vsock_listener.latest_metrics
