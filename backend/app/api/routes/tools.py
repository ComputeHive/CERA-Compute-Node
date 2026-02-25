from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.services.executor import executor
from app.lib.utils import AppStateModel
from app.enums import AppStatusEnum
from app.models.install_deps_req import InstallDepsRequest
from app.lib.utils import edit_state_file, load_state_file

router = APIRouter()

SCRIPT_DIR = "/home/ahmed/Desktop/GP/ComputeNode/backend/scripts"
required_tools = [
    "curl",
    "docker",
    "ip",
    "iptables",
    "mkfs.ext4",
    "debootstrap",
    "firecracker",
]


@router.get("/prog-status")
def check_app_status():
    installer_stage = load_state_file()
    # TODO: Frontend must call this function once it opens...
    return {"status": installer_stage.app_state}


@router.get("/check-deps")
async def check_dependencies():
    tools_status = {tool: True for tool in required_tools}
    output_lines = []
    async for line in executor.run(
        ["bash", "checking_prerequisites.sh"], cwd=SCRIPT_DIR
    ):
        output_lines.append(line.strip())
    missing_tools = " ".join(output_lines).split()
    for tool in missing_tools:
        tools_status[tool] = False
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
        "0" if tool else "1" for tool in installer_stage.installed_tools.values()
    ]

    print(tools_arr)

    async def stream():
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
        else:
            yield f"[ERROR]: Installation Failed"

    return StreamingResponse(stream(), media_type="text/plain")


@router.post("/build-image")
async def build_image(request: InstallDepsRequest):
    # TODO: Here Comes From the Frontend Building Method
    installer_stage = load_state_file()
    install_method = "normal" if request.build_tool else "docker"

    async def stream():
        async for line in executor.run(
            ["bash", "build_image.sh", f"{install_method}"], cwd=SCRIPT_DIR
        ):
            if isinstance(line, tuple):
                exit_code = line[1]
                break
            yield line + "\n"
        if exit_code == 0:
            installer_stage.app_state = AppStatusEnum.READY
            edit_state_file(installer_stage)
        else:
            yield f"[ERROR]: Building Image Failed"

    return StreamingResponse(stream(), media_type="text/plain")


@router.post("/run-vm")
async def run_vm():
    res = await executor.run(["bash", "run_firecracker.sh"], cwd=SCRIPT_DIR)
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}
