from typing import Dict, Optional

from app.enums import AppStatusEnum, ToolStatusEnum
from pydantic import BaseModel


class GlobalStateModel(BaseModel):
    app_state: AppStatusEnum = AppStatusEnum.CHECK_DEP
    installed_tools: Dict[str, ToolStatusEnum] = {}


class NodeConfigModel(BaseModel):
    node_index: str
    username: Optional[str] = None
    token: Optional[str] = None
    cpu: int
    ram: int
    disk: int
