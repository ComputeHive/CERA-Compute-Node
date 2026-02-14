import asyncio
from threading import Lock
from typing import Optional, List, Callable
import subprocess
import os
import sys


class BashExecutor:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    async def _stream_reader(
        self, stream: asyncio.StreamReader, callback_func: Callable
    ):
        output = []
        while True:
            line = await stream.readline()
            if not line:
                break
            decoded_line = line.decode()
            callback_func(decoded_line)
            output.append(decoded_line)
        return "".join(output)

    async def run(
        self, cmd: List[str], cwd: Optional[str] = None
    ) -> subprocess.CompletedProcess:
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_task = asyncio.create_task(
                self._stream_reader(process.stdout, sys.stdout.write)
            )
            stderr_task = asyncio.create_task(
                self._stream_reader(process.stderr, sys.stderr.write)
            )
            stdout_result, stderr_result = await asyncio.gather(
                stdout_task, stderr_task
            )
            return_code = await process.wait()
            return subprocess.CompletedProcess(
                args=cmd,
                returncode=return_code,
                stdout=stdout_result,
                stderr=stderr_result,
            )
        except Exception as e:
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr=str(e)
            )


executor = BashExecutor()
