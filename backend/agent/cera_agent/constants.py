from typing import Dict

from cera_agent.config import app_config
from cera_agent.models import EndpointsEnum

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
    "compute-tasks/finished-task",
    EndpointsEnum.TASK_FAILED_ENDPOINT: f"{app_config.COORDINATOR_URL}/"
    "compute-nodes/failed-task",
}
