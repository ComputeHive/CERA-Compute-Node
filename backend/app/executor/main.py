import argparse
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    __package__ = "executor"

from pydantic import ValidationError

from .constants import TASK_TYPES_WITH_FILES
from .core.task_runners import TaskManager
from .models.task import ExecutorTaskPayload, TaskTypeEnum


def build_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    root.add_argument(
        "--payload",
        type=str,
        required=True,
        help="JSON Serialized ExecutorTaskPayload",
    )
    return root


def main() -> None:
    args = build_parser().parse_args()

    try:
        payload = ExecutorTaskPayload.model_validate_json(args.payload)
    except ValidationError as exc:
        raise argparse.ArgumentTypeError(f"Invalid payload: {exc}") from exc

    task_type = payload.task_type

    manager = TaskManager(
        cpu_cores=payload.config.resources.cpu_cores,
        state_path=payload.config.state_path,
        max_retries=payload.config.resources.max_retries,
    )
    if task_type in TASK_TYPES_WITH_FILES:
        manager.run(
            task_type=task_type,
            output_path=payload.output_path,
            input_files=payload.input_files,
            flattened_code=payload.flattened_code,
            input_params=payload.flattened_code.input_schema,
        )
        return

    if task_type == TaskTypeEnum.SHUFFLE_SORT:
        manager.run(
            task_type=task_type,
            output_path=payload.output_path,
            input_files=payload.input_files,
            input_params=payload.input_params,
            num_of_partitions=payload.num_of_partitions,
            balance_partitions=payload.balance_partitions,
        )
        return

    if task_type == TaskTypeEnum.FUNCTION_WITH_INPUT:
        manager.run(
            task_type=task_type,
            output_path=payload.output_path,
            flattened_code=payload.flattened_code,
            input_params=payload.input_params,
        )
        return

    raise ValueError(f"Unsupported task type: {task_type}")


if __name__ == "__main__":
    main()
