from pydantic import BaseModel
from app.enums import AppStatusEnum
class AppStateModel:
    app_state: AppStatusEnum
