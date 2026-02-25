import asyncio
from typing import Optional,List
from app.constants import SCRIPT_DIR
class VMManager:
    def __init__(self):
        self._process:Optional[asyncio.subprocess.Process] = None
        self._log_lines:list[str] = []
        self._log_index:int = 0
        self._running :bool = False
        self._task:Optional[asyncio.Task] = None
    @property
    def is_running(self) -> bool:
        return self._running
    
    async def start(self,*args:List[int]):
        if self._running:
            raise RuntimeError("VM is already running")
        cmd = ["sudo","bash","run_firecracker.sh"]
        cwd = SCRIPT_DIR
        self._log_lines.clear()
        self._log_index = 0
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        self._running = True
        self._task = asyncio.create_task(self._collect_output)
    async def _collect_output(self):
        pass
    async def stop(self):
        pass