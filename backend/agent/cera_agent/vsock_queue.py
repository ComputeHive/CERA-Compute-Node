import asyncio

from cera_agent.models import Message


class VsockQueue:
    def __init__(self) -> None:
        self._q: asyncio.Queue[Message] = asyncio.Queue()

    async def put(self, msg: Message) -> None:
        await self._q.put(msg)

    async def drain_loop(self, writer: asyncio.StreamWriter) -> None:
        while True:
            msg = await self._q.get()
            writer.write(msg.encode())
            await writer.drain()
