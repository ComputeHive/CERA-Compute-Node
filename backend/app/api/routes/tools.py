import os

from app.constants import SCRIPT_DIR, required_tools
from app.enums import AppStatusEnum, BuildToolEnum, ToolStatusEnum
from app.lib.utils import (
    edit_global_state,
    edit_node_config,
    load_global_state,
)
from app.models.install_deps_req import InstallDepsRequest
from app.schemas import GlobalStateModel, NodeConfigModel
from app.services.executor import executor
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

rootfs_path = "/var/lib/cera/images/ubuntu-22.04.ext4"


@router.get("/prog-status")
def check_app_status():
    installer_stage = load_global_state()
    return {"status": installer_stage.app_state}


@router.get("/check-deps")
async def check_dependencies():
    tools_status = {tool: ToolStatusEnum.INSTALLED for tool in required_tools}
    output_lines = []
    async for line in executor.run(
        ["bash", "checking_prerequisites.sh"], cwd=SCRIPT_DIR
    ):
        if isinstance(line, tuple):
            break
        output_lines.append(line.strip())
    print(output_lines)
    missing_tools = " ".join(output_lines).split()
    for tool in missing_tools:
        tools_status[tool] = ToolStatusEnum.NOT_INSTALLED

    if not missing_tools and os.path.exists(rootfs_path):
        edit_global_state(
            GlobalStateModel(
                app_state=AppStatusEnum.READY, installed_tools=tools_status
            )
        )
    elif (
        not missing_tools
        or missing_tools == ["debootstrap"]
        or missing_tools == ["docker"]
    ):
        edit_global_state(
            GlobalStateModel(
                app_state=AppStatusEnum.BUILDING_IMG,
                installed_tools=tools_status,
            )
        )
    else:
        edit_global_state(
            GlobalStateModel(
                app_state=AppStatusEnum.INSTALLING_DEP,
                installed_tools=tools_status,
            )
        )

    return {"data": tools_status, "stdout": output_lines}


@router.get("/install-deps")
async def install_dependencies():
    installer_stage = load_global_state()
    if installer_stage is None:
        return None
    tools_arr = [
        "0" if tool == ToolStatusEnum.INSTALLED else "1"
        for tool in installer_stage.installed_tools.values()
    ]

    async def stream():
        exit_code = -1
        async for line in executor.run(
            ["bash", "install_deps.sh", *tools_arr], cwd=SCRIPT_DIR
        ):
            if isinstance(line, tuple):
                exit_code = line[1]
                break
            yield line + "\n"
        if exit_code == 0:
            installer_stage.app_state = AppStatusEnum.BUILDING_IMG
            edit_global_state(installer_stage)

    return StreamingResponse(stream(), media_type="text/plain")


@router.post("/build-image")
async def build_image(request: InstallDepsRequest):
    installer_stage = load_global_state()
    install_method = (
        "normal"
        if request.build_tool == BuildToolEnum.DEBOOTSTRAP
        else "docker"
    )

    async def stream():
        exit_code = -1
        async for line in executor.run(
            ["bash", "build_image.sh", f"{install_method}"], cwd=SCRIPT_DIR
        ):
            if isinstance(line, tuple):
                exit_code = line[1]
                print(exit_code)
                break
            yield line + "\n"

        if exit_code == 0:
            installer_stage.app_state = AppStatusEnum.READY
            edit_global_state(installer_stage)

    return StreamingResponse(stream(), media_type="text/plain")


@router.post("/auth/signup")
async def signup(cfg: NodeConfigModel):
    edit_node_config(cfg)
    state = load_global_state()
    state.app_state = AppStatusEnum.READY
    edit_global_state(state)
    return {"status": "saved", "node_index": cfg.node_index}
