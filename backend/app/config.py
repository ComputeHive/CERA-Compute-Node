from pydantic_settings import BaseSettings
import os
import json


class Settings(BaseSettings):
    APP_NAME: str = "CERA_VM Manager"
    VERSION: str = "1.0.0"
    APP_STATE_DIR: str = "/var/lib/cera/app_state.json"

    def model_post_init(self, __context):
        if not os.path.exists(self.APP_STATE_DIR):
            os.makedirs(os.path.dirname(self.APP_STATE_DIR), exist_ok=True)
        if not os.path.exists(self.APP_STATE_DIR):
            with open(self.APP_STATE_DIR, "w") as f:
                json.dump({"app_state": "checking_dep", "installed_tools": {}}, f)


settings = Settings()
