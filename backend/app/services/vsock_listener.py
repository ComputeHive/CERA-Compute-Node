import asyncio
import hashlib
import json
import os
from pathlib import Path
from typing import List, Optional

from app.constants import TIMEOUT
from app.lib.utils import load_node_config
from app.logging_config import get_logger
from app.services.protocol import Message, MsgTypeEnum

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
        node_idx = int(
            hashlib.md5(self._node_index.encode()).hexdigest()[:2], 16
        )
        self._uds_path = f"/run/cera/node_{node_idx}/firecracker.socket"
        os.makedirs(os.path.dirname(self._uds_path), exist_ok=True)

        os.makedirs(Path(self._uds_path).parent, exist_ok=True)

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
        response = await asyncio.wait_for(reader.readline(), timeout=TIMEOUT)
        if not response.decode().strip().startswith("OK"):
            raise ConnectionError("Vsock handshake failed")
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
            logger.info(f"Provisioned identity for user: {cfg.username}")

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
