from fastapi import APIRouter
from services.executor import executor

router = APIRouter()


@router.get("/check-deps")
def check_dependencies():
    res = executor.run(["bash", "../scripts/checking_prerequisites.sh"])
    return {"status": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}


@router.get("/install-deps")
def install_dependencies():
    pass


@router.get("/build-image")
def build_image():
    pass


@router.post("/run-vm")
def run_vm():
    pass
