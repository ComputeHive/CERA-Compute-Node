import asyncio
import socket

import aiohttp
from cera_agent.config import app_config
from cera_agent.core.node_controller import NodeController
from cera_agent.core.services.heartbeat import HeartbeatService
from cera_agent.core.services.task_poller import TaskPollerService
from cera_agent.key_exchange import bootstrap_key_exchange
from cera_agent.models import Message, MsgTypeEnum
from cera_agent.utils.lib import Metrics, metrics_report
from cera_agent.vsock_queue import VsockQueue

LISTEN_PORT = 5005
METRICS_INTERVAL = 2


class MetricsSender:
    def __init__(self, queue: VsockQueue):
        self._queue = queue

    async def run(self) -> None:
        while True:
            data = await asyncio.to_thread(Metrics.collect_metrics)
            msg = metrics_report(data["CPU"], data["RAM"], data["Disk"])
            await self._queue.put(msg)
            await asyncio.sleep(METRICS_INTERVAL)


class Agent:
    async def _read_provision(self, reader: asyncio.StreamReader) -> None:
        raw = await reader.readline()
        msg = Message.decode(raw)
        if msg.type != MsgTypeEnum.IDENTITY_PROVISION:
            raise ConnectionError(
                f"Expected Identity provision, got {msg.type}"
            )
        app_config.provision(msg.payload["token"], msg.payload["node_index"])

    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        writer.write(b"OK\n")
        await writer.drain()
        await self._read_provision(reader)
        queue = VsockQueue()
        controller = NodeController()
        async with aiohttp.ClientSession() as session:
            await bootstrap_key_exchange(session)
            tasks = [
                asyncio.create_task(queue.drain_loop(writer)),
                asyncio.create_task(MetricsSender(queue).run()),
                asyncio.create_task(HeartbeatService(session).run()),
                asyncio.create_task(
                    TaskPollerService(session, queue, controller).run()
                ),
            ]
            try:
                await asyncio.gather(*tasks)
            finally:
                for t in tasks:
                    t.cancel()
                writer.close()

    async def start(self) -> None:
        sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        sock.bind((socket.VMADDR_CID_ANY, LISTEN_PORT))
        sock.setblocking(False)
        server = await asyncio.start_server(self._handle_connection, sock=sock)
        async with server:
            await server.serve_forever()

    def run(self) -> None:
        asyncio.run(self.start())


if __name__ == "__main__":
    Agent().run()
