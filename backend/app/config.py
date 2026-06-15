import json
import os

from pydantic_settings import BaseSettings

GLOBAL_STATE_PATH = "/var/lib/cera/app_state.json"


class Settings(BaseSettings):
    APP_NAME: str = "CERA_VM Manager"
    VERSION: str = "1.0.0"

    model_config = {"env_prefix": "CERA_", "case_sensitive": False}

    @property
    def APP_STATE_DIR(self) -> str:
        return GLOBAL_STATE_PATH

    def model_post_init(self, __context):
        default_state_files = [
            (
                GLOBAL_STATE_PATH,
                {"app_state": "checking_dep", "installed_tools": {}},
            ),
        ]
        for path, default in default_state_files:
            if not os.path.exists(path):
                try:
                    os.makedirs(
                        os.path.dirname(self.APP_STATE_DIR), exist_ok=True
                    )
                except OSError:
                    pass  # Setup script should handle this with sudo
            if not os.path.exists(path):
                with open(path, "w") as f:
                    json.dump(default, f)


settings = Settings()
