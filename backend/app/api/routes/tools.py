from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.executor import executor
from app.schemas import AppStateModel
from app.enums import AppStatusEnum, BuildToolEnum, ToolStatusEnum
from app.models.install_deps_req import InstallDepsRequest
from app.lib.utils import edit_state_file, load_state_file
from app.models.run_vm_req import RunVMRequest
from app.constants import required_tools, SCRIPT_DIR

router = APIRouter()


@router.get("/prog-status")
def check_app_status():
    installer_stage = load_state_file()
    # TODO: Frontend must call this function once it opens...
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
    if (
        missing_tools == ""
        or missing_tools == "debootstrap"
        or missing_tools == "docker"
    ):
        edit_state_file(
            AppStateModel(
                app_state=AppStatusEnum.BUILDING_IMG, installed_tools=tools_status
            )
        )
    else:
        edit_state_file(
            AppStateModel(
                app_state=AppStatusEnum.INSTALLING_DEP, installed_tools=tools_status
            )
        )
    return {"data": tools_status, "stdout": output_lines}


@router.get("/install-deps")
async def install_dependencies():
    installer_stage = load_state_file()
    tools_arr = [
        "0" if tool == ToolStatusEnum.INSTALLED else "1"
        for tool in installer_stage.installed_tools.values()
    ]

    print(tools_arr)

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
            edit_state_file(installer_stage)

    return StreamingResponse(stream(), media_type="text/plain")


@router.post("/build-image")
async def build_image(request: InstallDepsRequest):
    installer_stage = load_state_file()
    install_method = (
        "normal" if request.build_tool == BuildToolEnum.DEBOOTSTRAP else "docker"
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
            edit_state_file(installer_stage)

    return StreamingResponse(stream(), media_type="text/plain")
