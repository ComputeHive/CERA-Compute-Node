from pydantic import BaseModel
from app.enums import AppStatusEnum
from typing import Dict
from collections import defaultdict
class AppStateModel(BaseModel):
    app_state: AppStatusEnum = AppStatusEnum.CHECK_DEP
    installed_tools:Dict[str,bool] = defaultdict(bool)