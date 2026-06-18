import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.enums import MsgTypeEnum, TaskStatusEnum
from app.executor.models.task import TaskTypeEnum


class Message(BaseModel):
    type: MsgTypeEnum
    payload: Dict[str, Any] = {}

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        return cls(**json.loads(raw.decode(errors="replace").strip()))

    def encode(self) -> bytes:
        obj = {"type": self.type, "payload": self.payload}
        return (json.dumps(obj, separators=(",", ":")) + "\n").encode()


class SigninRequest(BaseModel):
    node_id: str
    token: str


class TaskRecord(BaseModel):
    task_id: str
    price: float = 0.0
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    status: TaskStatusEnum = TaskStatusEnum.RECEIVED


class TaskReport(BaseModel):
    id: str
    price: float = 0.0
    upTime: str = ""
    status: TaskStatusEnum = TaskStatusEnum.RECEIVED


class TaskSnapShot(BaseModel):
    task_id: str
    task_type: TaskTypeEnum
    task_status: TaskStatusEnum


class Task(BaseModel):
    task_id: str
    task_link: str
    task_type: TaskTypeEnum


class AssignedTasks(BaseModel):
    tasks: List[Task]


class Heartbeat(BaseModel):
    cpu_load: float
    cpu_cores: int
    available_ram_mb: float
    available_disk_mb: float
    assigned_tasks: List[TaskSnapShot]


class ReceivedTask(BaseModel):
    task_id: str
    task_type: TaskTypeEnum
    task_link: str
