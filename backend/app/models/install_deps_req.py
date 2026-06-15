from app.enums import BuildToolEnum
from pydantic import BaseModel


class InstallDepsRequest(BaseModel):
    build_tool: BuildToolEnum = BuildToolEnum.DEBOOTSTRAP
