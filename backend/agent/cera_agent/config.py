import os
import time
from pathlib import Path
from uuid import UUID

from dotenv import load_dotenv
from executor.models.task import TaskTypeEnum
from pydantic import computed_field
from pydantic_settings import BaseSettings

load_dotenv()


class AppSettings(BaseSettings):
    volume_path: str = str(Path("Downloads").absolute())
    COORDINATOR_URL = os.environ["COORDINATOR_URL"]
    HKDF_INFO = os.environ["HKDF_INFO"]
    COORDINATOR_ID = os.environ["COORDINATOR_ID"]
    TASK_POLL_INTERVAL = 10
    KEYSTORE_DIR = "/var/cera/keystore"

    @computed_field
    @property
    def state_dir(self) -> str:
        return str(Path(self.volume_path) / "execution_state")

    @computed_field
    def state_path(self, task_id: UUID) -> str:
        return str(Path(self.state_dir) / f"state_{task_id}.json")

    @computed_field
    def _file_ext(self, task_type: TaskTypeEnum) -> str:
        EXT = {
            TaskTypeEnum.MAP: ".tsv",
            TaskTypeEnum.SHUFFLE_SORT: ".tsv",
            TaskTypeEnum.FUNCTION_WITH_FILES: ".csv",
            TaskTypeEnum.FUNCTION_WITH_INPUT: ".txt",
            TaskTypeEnum.REDUCE: ".csv",
        }
        return EXT[task_type]

    @computed_field
    def task_volume_path(self, task_id: str) -> str:
        return str(Path(self.volume_path) / f"{task_id}_{time.time()}")

    @computed_field
    def output_path(self, task_type: TaskTypeEnum, task_id: str) -> str:
        if task_type == TaskTypeEnum.SHUFFLE_SORT:
            return self.task_volume_path(task_id)
        else:
            return str(
                Path(self.task_volume_path(task_id))
                / f"{task_id}{self._file_ext(task_type)}"
            )

    def provision(self, token: str, node_index: str) -> None:
        self.COORD_AUTH_TOKEN = token
        self.NODE_ID = node_index

    @computed_field
    @property
    def HEADERS(self):
        return {"Authorization": f"Bearer {self.COORD_AUTH_TOKEN}"}


app_config = AppSettings()
