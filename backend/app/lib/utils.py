from app.config import settings
import json
from app.schemas import AppStateModel
from typing import Optional
def load_state_file() -> Optional[AppStateModel]:
    try:
        with open(settings.APP_STATE_DIR,'r') as file:
            data = json.load(file)
            if data is None:
                clean_state = AppStateModel()
                edit_state_file(clean_state,{})
                return clean_state
        return AppStateModel(**data)
    except Exception as e:
        print(e)
    
def edit_state_file(new_state:AppStateModel)-> None:
    with open(settings.APP_STATE_DIR,'w') as file:
        json.dump(new_state.model_dump(mode='json'),file) 
