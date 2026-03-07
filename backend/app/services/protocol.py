import json
from pydantic import BaseModel
from enum import Enum
from typing import Dict, Any


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = "task_received"
    TASK_RUNNING = "task_running"
    TASK_FAILED = "task_failed"
    TASK_COMPLETED = "task_completed"
    METRICS_REPORT = "metrics_report"


class Message(BaseModel):
    type: MsgTypeEnum
    payload: Dict[str, Any] = {}

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        return cls(**json.loads(raw.decode(errors="replace").strip()))
