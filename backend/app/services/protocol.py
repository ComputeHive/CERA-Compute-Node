import json
from enum import Enum, auto
from typing import Any, Dict

from pydantic import BaseModel


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = auto()
    TASK_RUNNING = auto()
    TASK_FAILED = auto()
    TASK_COMPLETED = auto()
    METRICS_REPORT = auto()
    IDENTITY_PROVISION = auto()


class Message(BaseModel):
    type: MsgTypeEnum
    payload: Dict[str, Any] = {}

    @classmethod
    def decode(cls, raw: bytes) -> "Message":
        return cls(**json.loads(raw.decode(errors="replace").strip()))
