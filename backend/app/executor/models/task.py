from enum import Enum
from typing import Annotated, Any, Dict, List, Literal, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl, TypeAdapter, model_validator

from .flattenedcode import FlattenedCode


class TaskTypeEnum(str, Enum):
    FUNCTION_WITH_FILES = "function_with_files"
    FUNCTION_WITH_INPUT = "function_with_input"
    MAP = "map"
    SHUFFLE_SORT = "shuffle_sort"
    REDUCE = "reduce"


TASK_TYPES_WITH_FILES = frozenset(
    {
        TaskTypeEnum.MAP,
        TaskTypeEnum.REDUCE,
        TaskTypeEnum.FUNCTION_WITH_FILES,
    }
)


class InputSourceTypeEnum(str, Enum):
    DEFAULT = "default"
    FUNCTION_OUTPUT = "function_output"


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
    state_path: str


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


TaskStateAdapter = TypeAdapter(TaskState)
