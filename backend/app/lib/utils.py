import json
from typing import Optional

from app.config import GLOBAL_STATE_PATH
from app.schemas import GlobalStateModel, NodeConfigModel


def load_global_state() -> GlobalStateModel:
    try:
        with open(GLOBAL_STATE_PATH, 'r') as f:
            data = json.load(f)
            return GlobalStateModel(**(data or {}))
    except Exception as e:
        print(e)
        return GlobalStateModel()


def edit_global_state(state: GlobalStateModel) -> None:
    with open(GLOBAL_STATE_PATH, 'w') as f:
        json.dump(state.model_dump(mode='json'), f)


def load_node_config(node_index: str) -> Optional[NodeConfigModel]:
    path = f"/var/lib/cera/node_{node_index}_config.json"
    try:
        with open(path, 'r') as f:
            return NodeConfigModel(**json.load(f))
    except Exception:
        return None


def edit_node_config(cfg: NodeConfigModel) -> None:
    path = f"/var/lib/cera/node_{cfg.node_index}_config.json"
    with open(path, 'w') as f:
        json.dump(cfg.model_dump(mode='json'), f)
