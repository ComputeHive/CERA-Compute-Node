from typing import Dict

from app.config import app_config
from app.enums import EndpointsEnum

ENDPOINTS: Dict[EndpointsEnum, str] = {
    EndpointsEnum.HEARTBEAT_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/heartbeat",
    EndpointsEnum.RECEIVE_TASKS_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/assigned-tasks",
    EndpointsEnum.SEND_PUBLIC_KEY_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/register-key",
    EndpointsEnum.RECEIVE_PUBLIC_KEY_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/public-key",
    EndpointsEnum.TASK_FINISHED_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/finished-task",
    EndpointsEnum.TASK_FAILED_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/failed-task",
}
