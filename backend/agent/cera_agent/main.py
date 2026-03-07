import asyncio
import socket

from cera_agent.metrics import collect_all
from cera_agent.protocol import metrics_report

LISTEN_PORT = 5005
METRICS_INTERVAL = 2
AF_VSOCK = 40
VMADDR_CID_ANY = 0xFFFFFFFF


class MetricsSender:
    def __init__(self, writer: asyncio.StreamWriter):
        self._writer = writer

    async def run(self) -> None:
        while True:
            data = await asyncio.to_thread(collect_all)
            msg = metrics_report(data["CPU"], data["RAM"], data["Disk"])
            self._writer.write(msg.encode())
            await self._writer.drain()
            await asyncio.sleep(METRICS_INTERVAL)


class Agent:
    async def _handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        writer.write(b"OK\n")
        await writer.drain()
        sender = MetricsSender(writer)
        try:
            await sender.run()
        finally:
            writer.close()

    async def start(self) -> None:
        sock = socket.socket(AF_VSOCK, socket.SOCK_STREAM)
        sock.bind((VMADDR_CID_ANY, LISTEN_PORT))
        sock.setblocking(False)
        server = await asyncio.start_server(self._handle_connection, sock=sock)
        async with server:
            await server.serve_forever()

    def run(self) -> None:
        asyncio.run(self.start())


if __name__ == "__main__":
    Agent().run()
