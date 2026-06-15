import json
from pathlib import Path

from executor.models.task import TaskModel
from utils.logger import get_logger

logger = get_logger(__name__)  # TODO: Check if the new Logger has any problems


class TaskParser:

    @staticmethod
    def parse(raw_json: str) -> TaskModel:

        data = json.loads(raw_json)
        task = TaskModel.model_validate(data)
        logger.info(
            "Task contract validated: type=%s, name=%s", task.type, task.name
        )
        return task

    @staticmethod
    def parse_file(file_path: str) -> TaskModel:
        raw = Path(file_path).read_text(encoding="utf-8")
        return TaskParser.parse(raw)
