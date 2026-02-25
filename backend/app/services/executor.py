import asyncio
from threading import Lock
from typing import Optional, List, AsyncGenerator


class BashExecutor:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    async def _stream_reader(
        self, stream: asyncio.StreamReader, queue: asyncio.Queue, is_stdout=False
    ):
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded_line = line.decode()
            if not is_stdout:
                decoded_line = "[ERROR]: " + decoded_line
            await queue.put(decoded_line)

    async def _wait_process(
        self, process: asyncio.subprocess.Process, queue: asyncio.Queue
    ) -> None:
        await process.wait()
        await queue.put(("__EXIT__", process.returncode))

    async def run(
        self, cmd: List[str], cwd: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        queue = asyncio.Queue()
        stdout_task = asyncio.create_task(
            self._stream_reader(process.stdout, queue, True)
        )
        stderr_task = asyncio.create_task(self._stream_reader(process.stderr, queue))
        wait_task = asyncio.create_task(self._wait_process(process, queue))
        try:
            while True:
                item = await queue.get()
                if isinstance(item, tuple) and item[0] == "__EXIT__":
                    yield item
                    break
                yield item
        except asyncio.CancelledError:
            stderr_task.cancel()
            stdout_task.cancel()
            wait_task.cancel()
            try:
                process.kill()
            except:
                pass
            raise


executor = BashExecutor()
