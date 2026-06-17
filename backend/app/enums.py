from enum import Enum


class AppStatusEnum(str, Enum):
    CHECK_DEP = "checking_dep"
    INSTALLING_DEP = "installing_dep"
    BUILDING_IMG = "building_img"
    READY = "ready"
    RUNNING = "running"
    SIGNUP = "signup"
    SIGNIN = "signin"


class BuildToolEnum(str, Enum):
    DOCKER = "docker"
    DEBOOTSTRAP = "debootstrap"


class ToolStatusEnum(str, Enum):
    NOT_INSTALLED = "Not Installled"
    INSTALLED = "Installed"


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


class MsgTypeEnum(str, Enum):
    TASK_RECEIVED = "task_received"
    TASK_RUNNING = "task_running"
    TASK_FAILED = "task_failed"
    TASK_COMPLETED = "task_completed"
    METRICS_REPORT = "metrics_report"
    IDENTITY_PROVISION = "identity_provision"
