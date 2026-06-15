from enum import StrEnum, auto
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from executor.constants import TASK_TYPES_WITH_FILES
from executor.models.flattenedcode import FlattenedCode
from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, model_validator

# TODO: Move Unrelated out of executor package


class TaskTypeEnum(StrEnum):
    FUNCTION_WITH_FILES = auto()
    FUNCTION_WITH_INPUT = auto()
    WORKFLOW = auto()
    MAP = auto()
    SHUFFLE_SORT = auto()
    REDUCE = auto()
    COMBINER = auto()


class InputSourceTypeEnum(StrEnum):
    DEFAULT = auto()
    FUNCTION_OUTPUT = auto()


class DecoratorParamsModel(BaseModel):
    ram_mb: int = Field(default=256, gt=0)
    disk_mb: int = Field(default=512, gt=0)
    cpu_cores: int = Field(default=1, gt=0)
    timeout_seconds: int = Field(default=30, gt=0)
    max_retries: int = Field(default=3, gt=0)
    num_of_partitions: Optional[int] = Field(
        default=None, gt=0, description="Only provided for shuffle_sort tasks."
    )
    balanced_partition: bool = False


class InputItem(BaseModel):
    source: InputSourceTypeEnum
    value: Any
    type: str


class InputFileMetaData(BaseModel):
    file_name: str
    link: Optional[HttpUrl] = None
    file_path: Optional[str] = None


class TaskModel(BaseModel):
    id: UUID
    name: Optional[str] = None
    type: TaskTypeEnum
    resources: DecoratorParamsModel = Field(
        default_factory=DecoratorParamsModel
    )
    inputs: Optional[Dict[str, InputItem]] = None
    input_files: Optional[List[InputFileMetaData]] = None
    output_schema: Optional[Dict[str, str]] = None
    hash_sha256: Optional[str] = None

    @model_validator(mode="after")
    def _validate_inputs(self) -> "TaskModel":
        if self.type == TaskTypeEnum.SHUFFLE_SORT:
            if not self.input_files:
                raise ValueError(
                    "shuffle_sort tasks must specify 'input_files'."
                )
            return self
        if self.inputs is None and self.input_files is None:
            raise ValueError(
                "Non-shuffle_sort tasks must provide 'inputs' and/or "
                "'input_files'."
            )
        return self


class ExecutionConfig(BaseModel):
    resources: DecoratorParamsModel = Field(
        default_factory=DecoratorParamsModel
    )
    volumes: dict[str, dict[str, str]] = Field(default_factory=dict)
    state_path: str = "/data/state.json"


class ExecutorTaskPayload(BaseModel):
    id: UUID
    task_type: TaskTypeEnum
    flattened_code: Optional[FlattenedCode] = None
    input_files: list[str] = Field(default_factory=list)
    output_path: Optional[str] = None
    input_params: dict[str, Any] = Field(default_factory=dict)
    num_of_partitions: Optional[int] = None
    balance_partitions: bool = False
    config: ExecutionConfig = Field(default_factory=ExecutionConfig)

    @model_validator(mode="after")
    def _validate_task_args(self) -> "ExecutorTaskPayload":

        if self.task_type in TASK_TYPES_WITH_FILES:
            if self.flattened_code is None:
                raise ValueError("Streaming tasks require flattened_code")
            if not self.input_files:
                raise ValueError("Streaming tasks require input_files")
            if self.output_path is None:
                raise ValueError("Streaming tasks require output_path")
        elif self.task_type == TaskTypeEnum.FUNCTION_WITH_INPUT:
            if self.flattened_code is None:
                raise ValueError("function_with_input requires flattened_code")
        elif self.task_type == TaskTypeEnum.SHUFFLE_SORT:
            if not self.input_files:
                raise ValueError("shuffle_sort requires input_files")
            if self.output_path is None:
                raise ValueError("shuffle_sort requires output_path")
            if self.num_of_partitions is None:
                raise ValueError("shuffle_sort requires num_of_partitions")
        return self


class BaseTaskState(BaseModel):

    retry: int = 0
    updated_at: float


class FileProcessingState(BaseTaskState):
    task_type: Literal[
        TaskTypeEnum.FUNCTION_WITH_FILES,
        TaskTypeEnum.MAP,
        TaskTypeEnum.REDUCE,
        TaskTypeEnum.COMBINER,
    ]
    next_row_to_write: int = 0
    total: int = 0


class ShuffleSortState(BaseTaskState):
    task_type: Literal[TaskTypeEnum.SHUFFLE_SORT,]
    next_file_to_write: int = 0
    next_row_to_write: int = 0
    total: int = 0
    key_file: str = ""
    partition_files: List[str] = []
    shuffle_completed: bool = False
    merge_completed: bool = False


class FunctionInputState(BaseTaskState):
    task_type: Literal[TaskTypeEnum.FUNCTION_WITH_INPUT]
    completed: bool = False


TaskState = Annotated[
    Union[FileProcessingState, ShuffleSortState, FunctionInputState],
    Field(discriminator="task_type"),
]


# class ExecutionStatusEnum(StrEnum):
#     COMPLETED = auto()
#     FAILED = auto()
#     TIMEOUT = auto()
#     REJECTED = auto()


# class NodeStateEnum(StrEnum):
#     IDLE = auto()
#     RUNNING = auto()
#     PAUSED = auto()


# class ExecutionMetrics(BaseModel):
#     rows_processed: int = 0
#     retries_used: int = 0
#     wall_time_seconds: float = 0.0
#     output_size_bytes: int = 0


# class ExecutionResult(BaseModel):
#     status: ExecutionStatusEnum
#     output_path: Optional[str] = None
#     metrics: ExecutionMetrics = Field(default_factory=ExecutionMetrics)
#     error: Optional[str] = None


# class TaskResult(BaseModel):
#     task_id: str
#     result: ExecutionResult
#     duration_seconds: float


# class ResourceSnapshot(BaseModel):
#     cpu_pct: float
#     ram_used_mb: float
#     disk_used_mb: float
#     net_out_kbps: float
#     timestamp: float


# class NodeStatus(BaseModel):
#     state: NodeStateEnum
#     active_task_id: Optional[str] = None
#     resources: ResourceSnapshot


# class TaskPackage(BaseModel):
#     task_id: str
#     encrypted_contract: bytes
#     encrypted_code: Optional[bytes] = None


# ResourceSpec = DecoratorParamsModel


# class ExecutionContext(BaseModel):
#     task_id: str
#     task_type: TaskTypeEnum
#     code_path: Optional[str] = None
#     input_paths: List[str]
#     output_path: str
#     resources: ResourceSpec


# class NodeEvent(BaseModel):
# type: str
#     payload: Dict[str, Any]


TaskStateAdapter = TypeAdapter(TaskState)
