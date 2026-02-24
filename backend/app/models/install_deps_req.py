from pydantic import BaseModel
from app.enums import BuildToolEnum

class InstallDepsRequest(BaseModel):
    build_tool:BuildToolEnum = BuildToolEnum.DEBOOTSTRAP