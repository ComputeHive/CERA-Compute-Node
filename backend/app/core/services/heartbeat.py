import asyncio
import os

import aiohttp

from app.config import app_config
from app.constants import ENDPOINTS
from app.core.task_service import TaskService
from app.enums import EndpointsEnum
from app.executor.utils.logging_config import get_logger
from app.models import Heartbeat
from app.utils.lib import Metrics

logger = get_logger(__name__)
HEARTBEAT_PERIOD = 30


class HeartbeatService:
    def __init__(
        self, session: aiohttp.ClientSession, task_service: TaskService
    ):
        self._session = session
        self._task_service = task_service

    async def run(self) -> None:
        while True:
            await asyncio.sleep(HEARTBEAT_PERIOD)
            await self._tick()

    async def _tick(self) -> None:
        metrics = await asyncio.to_thread(Metrics.collect_metrics)
        payload: Heartbeat = Heartbeat(
            cpu_load=metrics["CPU"],
            cpu_cores=(os.cpu_count() or 1),
            available_disk_mb=metrics["Disk"],
            available_ram_mb=metrics["RAM"],
            assigned_tasks=self._task_service.assigned_tasks,
        )
        try:
            logger.info("Sending Heartbeat to Coordinator")
            resp = await self._session.post(
                ENDPOINTS[EndpointsEnum.HEARTBEAT_ENDPOINT],
                json=payload.model_dump_json(),
                headers=app_config.HEADERS,
            )
            resp.raise_for_status()
        except aiohttp.ClientError as exc:
            logger.exception("Heartbeat failed: %s", exc)
