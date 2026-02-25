from pydantic import BaseModel
from app.enums import AppStatusEnum, ToolStatusEnum
from typing import Dict
from collections import defaultdict


class AppStateModel(BaseModel):
    app_state: AppStatusEnum = AppStatusEnum.CHECK_DEP
    installed_tools: Dict[str, ToolStatusEnum] = {}
