# TODO: Move Unrelated out of executor package
import os

from .models.task import TaskTypeEnum

CHECKPOINT_INTERVAL = 0.5

DEFAULT_CPU_CORES = os.cpu_count() or 1
DEFAULT_STATE_PATH = ".task_state.json"
DEFAULT_MAX_RETRIES = 3

TASK_TYPE_MAP: dict[str, TaskTypeEnum] = {
    "map": TaskTypeEnum.MAP,
    "reduce": TaskTypeEnum.REDUCE,
    "combiner": TaskTypeEnum.COMBINER,
    "function_with_files": TaskTypeEnum.FUNCTION_WITH_FILES,
    "function_with_input": TaskTypeEnum.FUNCTION_WITH_INPUT,
    "shuffle_sort": TaskTypeEnum.SHUFFLE_SORT,
}

TASK_TYPE_CHOICES = tuple(TASK_TYPE_MAP.keys())
TASK_TYPES_WITH_FILES = frozenset(
    {
        TaskTypeEnum.MAP,
        TaskTypeEnum.REDUCE,
        TaskTypeEnum.COMBINER,
        TaskTypeEnum.FUNCTION_WITH_FILES,
    }
)

SHUFFLE_SORT_PARAMS = {"key": "str", "value": "str"}
