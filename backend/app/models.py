import json
from datetime import datetime
from typing import Any, Dict, Optional

from app.enums import (
    AppStatusEnum,
    BuildToolEnum,
    MsgTypeEnum,
    TaskStatusEnum,
    ToolStatusEnum,
)
from pydantic import BaseModel


class InstallDepsRequest(BaseModel):
    build_tool: BuildToolEnum = BuildToolEnum.DEBOOTSTRAP


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


class RunVMRequest(BaseModel):
    token: str


class TaskRecord(BaseModel):
    task_id: str
    price: float = 0.0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: TaskStatusEnum = TaskStatusEnum.RECEIVED


class Message(BaseModel):
    type: MsgTypeEnum
    payload: Dict[str, Any] = {}

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        return cls(**json.loads(raw.decode(errors="replace").strip()))
