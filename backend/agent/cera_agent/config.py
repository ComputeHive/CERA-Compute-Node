from pathlib import Path
from uuid import UUID

from cera_agent.models import TaskTypeEnum
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv(Path(__file__).with_name(".env"))


class AppSettings(BaseSettings):
    volume_path: str = str(Path("Downloads").absolute())
    COORDINATOR_URL: str
    HKDF_INFO: str
    COORDINATOR_ID: str
    SUPABASE_PROJECT: str
    SUPABASE_KEY: str
    TASK_POLL_INTERVAL: int = 10
    KEYSTORE_DIR: str = "/var/cera/keystore"
    COORD_AUTH_TOKEN: str = ""
    NODE_ID: str = ""

    @property
    def state_dir(self) -> str:
        return str(Path(self.volume_path) / "execution_state")

    def state_path(self, task_id: UUID) -> str:
        return str(Path(self.state_dir) / f"state_{task_id}.json")

    def _file_ext(self, task_type: TaskTypeEnum) -> str:
        EXT = {
            TaskTypeEnum.MAP: ".tsv",
            TaskTypeEnum.SHUFFLE_SORT: ".tsv",
            TaskTypeEnum.FUNCTION_WITH_FILES: ".csv",
            TaskTypeEnum.FUNCTION_WITH_INPUT: ".txt",
            TaskTypeEnum.REDUCE: ".csv",
        }
        return EXT[task_type]

    def task_volume_path(self, task_id: str) -> str:
        return str(Path(self.volume_path) / f"{task_id}")

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

    @property
    def HEADERS(self):
        return {"Authorization": f"Bearer {self.COORD_AUTH_TOKEN}"}


app_config = AppSettings()
