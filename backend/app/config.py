from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.executor.models.task import TaskTypeEnum


class Settings(BaseSettings):
    APP_NAME: str = "CERA COMPUTE NODE"
    model_config = SettingsConfigDict(
        env_file=Path(__file__).with_name(".env")
    )
    volume_path: str = str(Path("/tmp/Cera_downloads").absolute())
    COORDINATOR_URL: str = ""
    HKDF_INFO: str = ""
    COORDINATOR_ID: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    NODE_ID: str = ""
    TASK_POLL_INTERVAL: int = 10
    COORD_AUTH_TOKEN: str = ""

    def KEYSTORE_DIR(self) -> str:
        return f"~/Desktop/Compute_Node_{self.NODE_ID}/keystore"

    @property
    def state_dir(self) -> str:
        return str(Path(self.volume_path) / "execution_state")

    def state_path(self, task_id: str) -> str:
        return str(Path(self.state_dir) / f"state_{task_id}.json")

    def _file_ext(self, task_type: TaskTypeEnum) -> str:
        EXT = {
            TaskTypeEnum.MAP: ".csv",
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
                / f"task_{task_id}{self._file_ext(task_type)}"
            )

    def provision(self, token: str, node_index: str) -> None:
        self.COORD_AUTH_TOKEN = token
        self.NODE_ID = node_index

    @property
    def HEADERS(self):
        return {"Authorization": f"Bearer {self.COORD_AUTH_TOKEN}"}


app_config = Settings()
