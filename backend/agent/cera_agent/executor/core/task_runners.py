import time
from abc import ABC
from typing import Any, List, Optional

from cera_agent.executor.core.base_executor import BaseExecutor
from cera_agent.executor.utils.file_handler import FileHandler
from cera_agent.executor.utils.state_manager import StateManager, StateWriter
from executor.models.flattenedcode import FlattenedCode
from executor.models.task import (
    FileProcessingState,
    FunctionInputState,
    ShuffleSortState,
    TaskState,
    TaskTypeEnum,
)
from utils.logger import get_logger

logger = get_logger(__name__)  # TODO: Check if the new Logger has any problems


class BaseTaskRunner(ABC):
    def __init__(self, state_path: str):
        self.state_manager = StateManager(state_path)

    def _load_or_create_state(
        self,
        task_type: TaskTypeEnum,
        input_files: List[str],
    ) -> TaskState:
        existing = self.state_manager.load()
        if existing is not None:
            logger.info("Resuming from checkpoint, retry=%d", existing.retry)
            return existing
        if task_type in (
            TaskTypeEnum.FUNCTION_WITH_FILES,
            TaskTypeEnum.MAP,
            TaskTypeEnum.COMBINER,
            TaskTypeEnum.REDUCE,
        ):
            total = FileHandler.total_lines_multiple_files(input_files)

            return FileProcessingState(
                task_type=task_type,
                retry=0,
                next_row_to_write=0,
                total=total,
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


class StreamingTaskRunner(BaseTaskRunner):

    def dispatch(
        self,
        executor: BaseExecutor,
        state: FileProcessingState,
        output_path: str,
        *,
        task_type: TaskTypeEnum,
        flattened_code: FlattenedCode,
        input_params: dict,
        input_files: List[str],
    ):

        if not input_files:
            raise ValueError("Streaming tasks require input_files")

        rows = FileHandler.stream_rows_multiple_files(
            input_files, input_params, state.next_row_to_write, task_type
        )

        executor.run_micro_batches(
            rows,
            output_path,
            state.total,
            flattened_code,
            state,
        )


class ShuffleSortTaskRunner(BaseTaskRunner):
    def dispatch(
        self,
        executor: BaseExecutor,
        state: ShuffleSortState,
        output_path: str,
        *,
        input_files: List[str],
        num_of_partitions: int,
        balance_partitions: bool,
    ):
        if not num_of_partitions or not input_files:
            raise ValueError(
                "Shuffle sort requires num_of_partitions and input_files"
            )
        executor.run_shuffle_sort(
            num_of_partitions,
            input_files,
            output_path,
            state,
            balance_partitions,
        )


class MacroTaskRunner(BaseTaskRunner):
    def dispatch(
        self,
        executor: BaseExecutor,
        state: FunctionInputState,
        *,
        flattened_code: FlattenedCode,
        input_params: dict,
    ) -> Any:
        if not input_params:
            raise ValueError("Macro tasks require input_params")
        result = executor.run_macro_task(
            flattened_code,
            input_params,
        )
        state.completed = True
        state.updated_at = time.time()
        return result


class TaskRunnerFactory:
    @staticmethod
    def get_runner(task_type: TaskTypeEnum):
        if task_type in (
            TaskTypeEnum.FUNCTION_WITH_FILES,
            TaskTypeEnum.MAP,
            TaskTypeEnum.COMBINER,
            TaskTypeEnum.REDUCE,
        ):
            return StreamingTaskRunner
        elif task_type == TaskTypeEnum.SHUFFLE_SORT:
            return ShuffleSortTaskRunner
        elif task_type == TaskTypeEnum.FUNCTION_WITH_INPUT:
            return MacroTaskRunner
        else:
            raise ValueError("Unsupported Task Runner")


class TaskManager:
    def __init__(
        self, cpu_cores: int, state_path: str, max_retries: int = 3
    ) -> None:
        self._cpu_cores = cpu_cores
        self._state_manager = StateManager(state_path)
        self._max_retries = max_retries
        self._state_writer = StateWriter(self._state_manager)
        self._executor = BaseExecutor(cpu_cores)

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
        runner_cls = TaskRunnerFactory.get_runner(task_type)
        runner = runner_cls(self._state_manager.state_path)
        state = runner._load_or_create_state(task_type, input_files or [])

        last_exc: Optional[Exception] = None
        succeed = False
        if state.retry > self._max_retries:
            raise RuntimeError(
                f"Task {task_type.value} failed after {state.retry}" " retries"
            )
        self._state_writer.start(state)
        try:
            result = self._dispatch(
                runner,
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
            logger.warning(
                "Task %s attempt %d/%d failed: %s",
                task_type.value,
                state.retry,
                self._max_retries,
                exc,
            )
        finally:
            self._state_writer.stop(save=not succeed)

        raise RuntimeError(
            f"Task {task_type.value} failed after {self._max_retries} retries"
        ) from last_exc

    def _dispatch(
        self,
        runner: BaseTaskRunner,
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
        if isinstance(runner, StreamingTaskRunner):
            assert isinstance(state, FileProcessingState)
            assert output_path is not None
            assert flattened_code is not None
            assert input_params is not None
            assert input_files is not None
            return runner.dispatch(
                self._executor,
                state,
                output_path,
                task_type=task_type,
                flattened_code=flattened_code,
                input_params=input_params,
                input_files=input_files,
            )
        if isinstance(runner, ShuffleSortTaskRunner):
            assert isinstance(state, ShuffleSortState)
            assert output_path is not None
            assert input_files is not None
            assert num_of_partitions is not None
            return runner.dispatch(
                self._executor,
                state,
                output_path,
                input_files=input_files,
                num_of_partitions=num_of_partitions,
                balance_partitions=balance_partitions,
            )
        if isinstance(runner, MacroTaskRunner):
            assert isinstance(state, FunctionInputState)
            assert flattened_code is not None
            assert input_params is not None
            return runner.dispatch(
                self._executor,
                state,
                flattened_code=flattened_code,
                input_params=input_params,
            )
        raise ValueError(f"Unhandled runner type: {type(runner)}")
