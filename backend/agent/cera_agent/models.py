import json
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = "task_received"
    TASK_RUNNING = "task_running"
    TASK_FAILED = "task_failed"
    TASK_COMPLETED = "task_completed"
    METRICS_REPORT = "metrics_report"
    IDENTITY_PROVISION = "identity_provision"


class EndpointsEnum(str, Enum):
    HEARTBEAT_ENDPOINT = "heartbeat_endpoint"
    RECEIVE_TASKS_ENDPOINT = "receive_tasks_endpoint"
    SEND_PUBLIC_KEY_ENDPOINT = "send_public_key_endpoint"
    RECEIVE_PUBLIC_KEY_ENDPOINT = "receive_public_key_endpoint"
    TASK_FINISHED_ENDPOINT = "task_finished_endpoint"
    TASK_FAILED_ENDPOINT = "task_failed_endpoint"


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
    FUNCTION_WITH_FILES = "function_with_files"
    FUNCTION_WITH_INPUT = "function_with_input"
    WORKFLOW = "workflow"
    MAP = "map"
    SHUFFLE_SORT = "shuffle_sort"
    REDUCE = "reduce"
    COMBINER = "combiner"


class TaskStatusEnum(str, Enum):
    CANCELLED = "cancelled"
    RECEIVED = "received"
    PROCESSED = "processed"
    EXECUTING = "executing"
    FINISHED = "finished"
    FAILED = "failed"


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
