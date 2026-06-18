from enum import Enum


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = "task_received"
    TASK_RUNNING = "task_running"
    TASK_FAILED = "task_failed"
    TASK_COMPLETED = "task_completed"
    METRICS_REPORT = "metrics_report"
    IDENTITY_PROVISION = "identity_provision"


class TaskStatusEnum(str, Enum):
    CANCELLED = "cancelled"
    RECEIVED = "received"
    PROCESSED = "processed"
    EXECUTING = "executing"
    FINISHED = "finished"
    FAILED = "failed"


class EndpointsEnum(str, Enum):
    HEARTBEAT_ENDPOINT = "heartbeat_endpoint"
    RECEIVE_TASKS_ENDPOINT = "receive_tasks_endpoint"
    SEND_PUBLIC_KEY_ENDPOINT = "send_public_key_endpoint"
    RECEIVE_PUBLIC_KEY_ENDPOINT = "receive_public_key_endpoint"
    TASK_FINISHED_ENDPOINT = "task_finished_endpoint"
    TASK_FAILED_ENDPOINT = "task_failed_endpoint"
