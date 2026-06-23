import json
from pathlib import Path

from app.executor.models.task import TaskModel
from app.executor.utils.logging_config import get_logger

logger = get_logger(__name__)


class TaskParser:
    @staticmethod
    def parse_dict(raw: dict) -> TaskModel:
        task = TaskModel.model_validate(raw)
        return task

    @staticmethod
    def parse_file(file_path: str) -> TaskModel:
        raw = Path(file_path).read_text(encoding="utf-8")
        data = json.loads(raw)
        task = TaskModel.model_validate(data)
        logger.info("Task %s validated function %s", task.type, task.name)
        return task
