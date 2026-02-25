from typing import Dict, Any
from app.lib.utils import edit_state_file, load_state_file
from app.enums import AppStatusEnum
from app.schemas import AppStateModel


def test_edit_state_file() -> None:
    next_state = AppStateModel(app_state=AppStatusEnum.CHECK_DEP, INSTALLING_DEP={})
    edit_state_file(next_state)
    app_state = load_state_file()
    assert app_state == next_state
