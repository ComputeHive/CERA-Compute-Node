from app.config import settings
import json
from app.schemas import AppStateModel
from typing import Optional
def load_state_file() -> Optional[AppStateModel]:
    try:
        with open(settings.APP_STATE_DIR,'r') as file:
            data = json.load(file)
        return AppStateModel(**data)
    except Exception as e:
        print(e)
        
def edit_state_file(new_state:AppStateModel)-> None:
    with open(settings.APP_STATE_DIR,'w') as file:
        json.dump(new_state.model_dump(mode='json'),file) 
