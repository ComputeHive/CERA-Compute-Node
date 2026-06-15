import json
from enum import Enum, auto
from typing import Any, Dict, List

from pydantic import BaseModel


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = auto()
    TASK_RUNNING = auto()
    TASK_FAILED = auto()
    TASK_COMPLETED = auto()
    METRICS_REPORT = auto()
    IDENTITY_PROVISION = auto()


class EndpointsEnum(str, Enum):
    HEARTBEAT_ENDPOINT = auto()
    RECEIVE_TASKS_ENDPOINT = auto()
    SEND_PUBLIC_KEY_ENDPOINT = auto()
    RECEIVE_PUBLIC_KEY_ENDPOINT = auto()
    TASK_FINISHED_ENDPOINT = auto()
    TASK_FAILED_ENDPOINT = auto()


class Message(BaseModel):
    type: MsgTypeEnum
    payload: Dict[str, Any] = {}

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        return cls(**json.loads(raw.decode(errors="replace").strip()))

    def encode(self) -> bytes:
        obj = {"type": self.type, "payload": self.payload}
        return (json.dumps(obj, separators=(",", ":")) + "\n").encode()


class TaskTypeEnum(str, Enum):
    FUNCTION_WITH_FILES = auto()
    FUNCTION_WITH_INPUT = auto()
    WORKFLOW = auto()
    MAP = auto()
    SHUFFLE_SORT = auto()
    REDUCE = auto()
    COMBINER = auto()


class TaskStatusEnum(str, Enum):
    CANCELLED = auto()
    RECEIVED = auto()
    PROCESSED = auto()
    EXECUTING = auto()
    FINISHED = auto()
    FAILED = auto()


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
    cpu_load: int
    cpu_cores: int
    available_ram_mb: int
    available_disk_mb: int
    assigned_tasks: List[TaskSnapShot]
