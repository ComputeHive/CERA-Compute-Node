from fastapi import APIRouter
from services.executor import executor

router = APIRouter()

@router.get("/prog-status")
def check_app_status():
    # TODO: Add functions for saving state ...
    # Just Check Status of Installation {the frontend must route based on this}
    # TODO: update state after finishing of each stage function
    # TODO: Frontend must call this function once it opens...
    pass
@router.get("/check-deps")
async def check_dependencies():
    res = await executor.run(["bash", "checking_prerequisites.sh"], cwd="../scripts/")
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}


@router.get("/install-deps")
async def install_dependencies():
    # TODO: Here Comes From Frontend The Binary of things to be installed
    res = await executor.run(["bash", "install_deps.sh"], cwd="../scripts/")
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}


@router.get("/build-image")
async def build_image():
    # TODO: Here Comes From the Frontend Building Method
    res = await executor.run(["bash", "build_image.sh"], cwd="../scripts/")
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}


@router.post("/run-vm")
async def run_vm():
    res = await executor.run(["bash", "run_firecracker.sh"], cwd="../scripts/")
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}
