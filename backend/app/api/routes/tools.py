from fastapi import APIRouter

from app.config import app_config
from app.models import SigninRequest

router = APIRouter()


@router.post("/auth/signin")
async def signup(req: SigninRequest):
    app_config.provision(req.token, req.node_id)
    return {"status": "signed-in"}
