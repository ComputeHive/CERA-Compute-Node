import time
from typing import Any, List, Optional

from ..models.flattenedcode import FlattenedCode
from ..models.task import (
    FileProcessingState,
    FunctionInputState,
    ShuffleSortState,
    TaskState,
    TaskTypeEnum,
)
from ..utils.file_handler import FileHandler
from ..utils.state_manager import StateManager, StateWriter
from .base_executor import BaseExecutor

_STREAMING_TYPES = (
    TaskTypeEnum.FUNCTION_WITH_FILES,
    TaskTypeEnum.MAP,
    TaskTypeEnum.COMBINER,
    TaskTypeEnum.REDUCE,
)


class TaskManager:
    def __init__(
        self, cpu_cores: int, state_path: str, max_retries: int = 3
    ) -> None:
        self._cpu_cores = cpu_cores
        self._state_manager = StateManager(state_path)
        self._max_retries = max_retries
        self._state_writer = StateWriter(self._state_manager)
        self._executor = BaseExecutor(cpu_cores)

    def _load_or_create_state(
        self,
        task_type: TaskTypeEnum,
        input_files: List[str],
    ) -> TaskState:
        existing = self._state_manager.load()
        if existing is not None:
            return existing
        if task_type in _STREAMING_TYPES:
            return FileProcessingState(
                task_type=task_type,
                retry=0,
                next_row_to_write=0,
                total=FileHandler.total_lines_multiple_files(input_files),
                updated_at=time.time(),
            )
        if task_type == TaskTypeEnum.FUNCTION_WITH_INPUT:
            return FunctionInputState(
                task_type=task_type,
                retry=0,
                completed=False,
                updated_at=time.time(),
            )
        if task_type == TaskTypeEnum.SHUFFLE_SORT:
            return ShuffleSortState(
                task_type=task_type,
                retry=0,
                shuffle_completed=False,
                merge_completed=False,
                updated_at=time.time(),
            )
        raise ValueError(f"Cannot create state for type: {task_type}")

    def run(
        self,
        task_type: TaskTypeEnum,
        output_path: Optional[str] = None,
        *,
        input_files: Optional[List[str]] = None,
        flattened_code: Optional[FlattenedCode] = None,
        input_params: Optional[dict] = None,
        num_of_partitions: Optional[int] = None,
        balance_partitions: bool = False,
    ) -> Any:
        state = self._load_or_create_state(task_type, input_files or [])
        if state.retry > self._max_retries:
            raise RuntimeError(
                f"Task {task_type.value} failed after {state.retry} retries"
            )

        last_exc: Optional[Exception] = None
        succeed = False
        self._state_writer.start(state)
        try:
            result = self._dispatch(
                task_type,
                state,
                output_path,
                input_files=input_files,
                flattened_code=flattened_code,
                input_params=input_params,
                num_of_partitions=num_of_partitions,
                balance_partitions=balance_partitions,
            )
            succeed = True
            return result
        except Exception as exc:
            last_exc = exc
            state.retry += 1
        finally:
            self._state_writer.stop(save=not succeed)

        raise RuntimeError(
            f"Task {task_type.value} failed after {self._max_retries} retries"
        ) from last_exc

    def _dispatch(
        self,
        task_type: TaskTypeEnum,
        state: TaskState,
        output_path: Optional[str],
        *,
        input_files: Optional[List[str]],
        flattened_code: Optional[FlattenedCode],
        input_params: Optional[dict],
        num_of_partitions: Optional[int],
        balance_partitions: bool,
    ) -> Any:
        if task_type in _STREAMING_TYPES:
            return self._run_streaming(
                task_type,
                state,
                output_path,
                input_files,
                flattened_code,
                input_params,
            )
        if task_type == TaskTypeEnum.SHUFFLE_SORT:
            return self._run_shuffle_sort(
                state,
                output_path,
                input_files,
                num_of_partitions,
                balance_partitions,
            )
        if task_type == TaskTypeEnum.FUNCTION_WITH_INPUT:
            return self._run_macro(
                state, output_path, flattened_code, input_params
            )
        raise ValueError(f"Unsupported task type: {task_type}")

    def _run_streaming(
        self,
        task_type: TaskTypeEnum,
        state: TaskState,
        output_path: Optional[str],
        input_files: Optional[List[str]],
        flattened_code: Optional[FlattenedCode],
        input_params: Optional[dict],
    ) -> None:
        assert isinstance(state, FileProcessingState)
        assert output_path is not None
        assert flattened_code is not None
        assert input_params is not None
        assert input_files is not None
        rows = FileHandler.stream_rows_multiple_files(
            input_files, input_params, state.next_row_to_write, task_type
        )
        self._executor.run_micro_batches(
            rows, output_path, state.total, flattened_code, state
        )

    def _run_shuffle_sort(
        self,
        state: TaskState,
        output_path: Optional[str],
        input_files: Optional[List[str]],
        num_of_partitions: Optional[int],
        balance_partitions: bool,
    ) -> None:
        assert isinstance(state, ShuffleSortState)
        assert output_path is not None
        assert input_files is not None
        assert num_of_partitions is not None
        self._executor.run_shuffle_sort(
            num_of_partitions,
            input_files,
            output_path,
            state,
            balance_partitions,
        )

    def _run_macro(
        self,
        state: TaskState,
        output_path: str,
        flattened_code: FlattenedCode,
        input_params: dict,
    ) -> Any:
        assert isinstance(state, FunctionInputState)

        result = self._executor.run_macro_task(
            flattened_code, output_path, input_params
        )
        state.completed = True
        state.updated_at = time.time()
        return result
