import asyncio

import aiohttp
from cera_agent.config import app_config
from cera_agent.core.node_controller import NodeController
from cera_agent.vsock_queue import VsockQueue

from backend.agent.cera_agent.constants import ENDPOINTS
from backend.agent.cera_agent.models import EndpointsEnum, MsgTypeEnum
from backend.agent.cera_agent.utils.lib import (
    task_annonce_status,
    task_completed,
)


class TaskPollerService:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        queue: VsockQueue,
        controller: NodeController,
    ) -> None:
        self._session = session
        self._queue = queue
        self._controller = controller
        self._active: set[str] = set()

    async def run(self):
        while True:
            await asyncio.sleep(app_config.TASK_POLL_INTERVAL)
            try:
                await self._poll_once()
            except aiohttp.ClientError as exc:
                print(f"[Poller] GET failed: {exc}")

    async def _poll_once(self) -> None:
        # TODO: Endpoint Revision
        resp = await self._session.get(
            ENDPOINTS[EndpointsEnum.RECEIVE_TASKS_ENDPOINT],
            params={"node_id": app_config.NODE_ID},
            headers=app_config.HEADERS,
        )
        resp.raise_for_status()
        tasks = await resp.json()
        for task in tasks:
            task_id = task["task_id"]
            if task_id in self._active:
                continue
            self._active.add(task_id)
            asyncio.create_task(
                self._handle_task(
                    task_id, task["presigned_url"], task.get("price", 0.0)
                )
            )

    async def _handle_task(
        self, task_id: str, presigned_url: str, price: float
    ) -> None:
        await self._queue.put(
            task_annonce_status(task_id, MsgTypeEnum.TASK_RECEIVED)
        )
        try:
            resp = await self._session.get(presigned_url)
            resp.raise_for_status()
            encrypted_zip = await resp.read()
            await self._queue.put(
                task_annonce_status(task_id, MsgTypeEnum.TASK_RUNNING)
            )
            success = await asyncio.to_thread(
                self._controller.handle_task_bytes, task_id, encrypted_zip
            )
            if success:
                await self._queue.put(task_completed(task_id, price))
            else:
                await self._queue.put(
                    task_annonce_status(task_id, MsgTypeEnum.TASK_FAILED)
                )
        except Exception as exc:
            print(f"[Poller] task{task_id} raised: {exc}")
            await self._queue.put(
                task_annonce_status(task_id, MsgTypeEnum.TASK_FAILED)
            )
        finally:
            self._active.discard(task_id)
