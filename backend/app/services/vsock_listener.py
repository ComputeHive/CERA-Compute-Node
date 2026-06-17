import asyncio
import hashlib
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from app.constants import TIMEOUT
from app.lib.utils import load_node_config
from app.logging_config import get_logger
from app.models import Message, MsgTypeEnum, TaskRecord

from backend.app.enums import TaskStatusEnum

logger = get_logger(__name__)

GUEST_AGENT_PORT = 5005
RETRY_DELAY = 3


class VsockListener:
    def __init__(self, node_index: str, guest_port: int = GUEST_AGENT_PORT):
        self._node_index = node_index
        self._guest_port = guest_port
        self._subscribers: List[asyncio.Queue] = []
        self._latest_metrics: dict = {}
        self._task: Optional[asyncio.Task] = None
        self._received_tasks: dict[str, TaskRecord] = {}
        node_idx = int(
            hashlib.md5(self._node_index.encode()).hexdigest()[:2], 16
        )
        self._uds_path = f"/run/cera/node_{node_idx}/firecracker.socket"
        os.makedirs(os.path.dirname(self._uds_path), exist_ok=True)

        os.makedirs(Path(self._uds_path).parent, exist_ok=True)

    @property
    def latest_tasks(self) -> list[dict]:
        now = datetime.now(timezone.utc)
        out = []
        for rec in self._received_tasks.values():
            if rec.started_at:
                end = rec.ended_at or now
                delta = end - rec.started_at
                total_seconds = int(delta.total_seconds())
                uptime = str(timedelta(seconds=total_seconds))
            else:
                uptime = "00:00:00"
            task_out_dict = {
                "id": rec.task_id,
                "price": rec.price,
                "upTime": uptime,
                "status": rec.status,
            }
            out.append(task_out_dict)
        return out

    def subscribe(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    @property
    def latest_metrics(self) -> dict:
        return self._latest_metrics

    async def start(self) -> None:
        self._task = asyncio.create_task(self._listen_loop())

    async def stop(self) -> None:
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None
        self._subscribers.clear()
        self._latest_metrics = {}
        logger.info("VsockListener stopped")

    async def _handshake(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        writer.write(f"CONNECT {self._guest_port}\n".encode())
        await writer.drain()
        fc_response = await asyncio.wait_for(
            reader.readline(), timeout=TIMEOUT
        )
        fc_status = fc_response.decode(errors="replace").strip()
        logger.debug("Firecracker vsock response: %s", fc_status)
        if not fc_status.startswith("OK"):
            raise ConnectionError(
                f"Vsock connect failed: {fc_status or 'empty response'}"
            )

        agent_response = await asyncio.wait_for(
            reader.readline(), timeout=TIMEOUT
        )
        agent_status = agent_response.decode(errors="replace").strip()
        logger.debug("Agent vsock response: %s", agent_status)
        if agent_status != "OK":
            raise ConnectionError(
                f"Agent handshake failed: {agent_status or 'empty response'}"
            )

        cfg = load_node_config(self._node_index)
        if cfg and cfg.token:
            provision_msg = Message(
                type=MsgTypeEnum.IDENTITY_PROVISION,
                payload={
                    "token": cfg.token,
                    "username": cfg.username,
                    "node_index": cfg.node_index,
                },
            )
            writer.write(
                (json.dumps(provision_msg.model_dump()) + "\n").encode()
            )
            await writer.drain()
            logger.info(f"Provisioned identity for user: {cfg.node_index}")

        logger.info("Connected to Agent vsock stream and completed handshake")

    async def _process_stream(self, reader: asyncio.StreamReader) -> None:
        while True:
            raw = await reader.readline()
            if not raw:
                break
            try:
                msg = Message.decode(raw)
                if msg.type == MsgTypeEnum.METRICS_REPORT:
                    self._latest_metrics = msg.payload
                    logger.info(f"[METRICS] {msg.payload}")
                elif msg.type == MsgTypeEnum.TASK_RECEIVED:
                    tid = msg.payload["task_id"]
                    self._received_tasks.setdefault(
                        tid, TaskRecord(**msg.payload)
                    )
                elif msg.type == MsgTypeEnum.TASK_RUNNING:
                    tid = msg.payload["task_id"]
                    rec = self._received_tasks.setdefault(
                        tid,
                        TaskRecord(**msg.payload),
                    )
                    if rec.started_at is None:
                        rec.started_at = datetime.now(timezone.utc)
                elif msg.type == MsgTypeEnum.TASK_COMPLETED:
                    tid = msg.payload["task_id"]
                    if rec := self._received_tasks.get(tid):
                        rec.status = TaskStatusEnum.FINISHED
                        rec.price = msg.payload.get("price", 0.0)
                        rec.ended_at = datetime.now(timezone.utc)
                elif msg.type == MsgTypeEnum.TASK_FAILED:
                    tid = msg.payload["task_id"]
                    if rec := self._received_tasks.get(tid):
                        rec.status = TaskStatusEnum.FAILED
                        rec.ended_at = datetime.now(timezone.utc)
                for queue in self._subscribers:
                    queue.put_nowait(msg)
            except Exception as e:
                logger.warning(f"Malformed message skipped: {e}")

    async def _listen_loop(self) -> None:
        while True:
            writer = None
            try:
                reader, writer = await asyncio.open_unix_connection(
                    self._uds_path
                )
                await self._handshake(reader, writer)
                await self._process_stream(reader)
            except Exception as e:
                logger.error(f"Vsock error: {e}. Retrying in {RETRY_DELAY}s")
                if writer is not None:
                    writer.close()
                await asyncio.sleep(RETRY_DELAY)
