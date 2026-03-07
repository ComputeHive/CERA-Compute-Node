import asyncio
from app.logging_config import get_logger
from typing import List, Optional
from app.constants import TIMEOUT
from app.services.protocol import Message, MsgTypeEnum

logger = get_logger(__name__)

DEFAULT_UDS_PATH = "/run/cera/firecracker.socket"
GUEST_AGENT_PORT = 5005

RETRY_DELAY = 3
MAX_RETRIES = 5


class VsockListener:
    def __init__(
        self, uds_path: str = DEFAULT_UDS_PATH, guest_port: int = GUEST_AGENT_PORT
    ):
        self._uds_path = uds_path
        self._guest_port = guest_port
        self._subscribers: List[asyncio.Queue] = []
        self._latest_metrics: dict = {}
        self._task: Optional[asyncio.Task] = None

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
        logger.info("Connected to Agent vsock stream")

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
                reader, writer = await asyncio.open_unix_connection(self._uds_path)
                await self._handshake(reader, writer)
                await self._process_stream(reader)
            except Exception as e:
                logger.error(f"Vsock error: {e}. Retrying in {RETRY_DELAY}s")
                if writer is not None:
                    writer.close()
                await asyncio.sleep(RETRY_DELAY)


vsock_listener = VsockListener()
