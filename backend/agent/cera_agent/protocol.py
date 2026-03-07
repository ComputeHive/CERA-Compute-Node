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

    def encode(self) -> bytes:
        obj = {"type": self.type, "payload": self.payload}
        return (json.dumps(obj, separators=(",", ":")) + "\n").encode()


def metrics_report(cpu_percent: float, ram_percent: float, disk_used: float) -> Message:
    return Message(
        type=MsgTypeEnum.METRICS_REPORT,
        payload={"CPU": cpu_percent, "RAM": ram_percent, "Disk": disk_used},
    )


def task_failed(task_id: str) -> Message:
    return Message(
        type=MsgTypeEnum.TASK_FAILED,
        payload={"message": f"{task_id} failed, restart."},
    )


def task_running(task_id: str) -> Message:
    return Message(
        type=MsgTypeEnum.TASK_RUNNING, payload={"message": f"{task_id} start running."}
    )


def task_completed(task_id: str) -> Message:
    return Message(
        type=MsgTypeEnum.TASK_COMPLETED, payload={"message": f"{task_id} completed."}
    )
