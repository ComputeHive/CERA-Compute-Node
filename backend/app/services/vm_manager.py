import asyncio
import os
from threading import Lock
from typing import Dict, List, Optional

from app.constants import SCRIPT_DIR, TIMEOUT
from app.logging_config import get_logger
from app.services.vsock_listener import VsockListener

logger = get_logger(__name__)


class _VMInstance:

    def __init__(self, node_index: str):
        self._node_index = node_index
        self._running: bool = False
        self._cpu: int = 0  # VCores
        self._ram: int = 0  # MB
        self._disk: int = 0  # MB
        self._process: Optional[asyncio.subprocess.Process] = None
        self._task: Optional[asyncio.Task] = None
        self._exit_code: Optional[int] = None
        self.vsock = VsockListener(node_index)

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def vm_config(self) -> dict:
        return {"cpu": self._cpu, "ram": self._ram, "disk": self._disk}

    async def start(self, cpu: int, ram: int, disk: int) -> None:
        if self._running:
            raise RuntimeError("VM is already running")
        self._cpu = cpu
        self._ram = ram
        self._disk = disk
        env = os.environ.copy()
        env["CERA_NODE_INDEX"] = str(self._node_index)
        cmd = [
            "sudo",
            "-E",
            "bash",
            "run_firecracker.sh",
            str(cpu),
            str(ram),
            str(disk),
        ]
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            env=env,
            cwd=SCRIPT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            exit_code = await asyncio.wait_for(
                self._process.wait(), timeout=2.0
            )
            stderr_output = b""
            if self._process.stderr:
                stderr_output = await self._process.stderr.read()
            if exit_code != 0:
                raise RuntimeError(
                    f"VM process exited immediately (code={exit_code}): "
                    f"{stderr_output.decode(errors='replace').strip()}"
                )
        except asyncio.TimeoutError:
            pass
        await self.vsock.start()
        self._running = True
        self._task = asyncio.create_task(self._write_VM_logs())
        logger.info(
            f"Firecracker VM[{self._node_index}] started "
            f"(pid= {self._process.pid})"
        )

    async def _write_VM_logs(self) -> None:
        assert self._process is not None

        async def _reader(stream: asyncio.StreamReader, tag: str):
            while True:
                line = await stream.readline()
                if not line:
                    break
                decoded = line.decode(errors="replace").rstrip("\n")
                if tag == "stdout":
                    logger.info(f"[Firecracker] {decoded}")
                else:
                    logger.error(f"[Firecracker] {decoded}")

        try:
            await asyncio.gather(
                _reader(self._process.stdout, "stdout"),
                _reader(self._process.stderr, "stderr"),
            )
            self._exit_code = await self._process.wait()
        except asyncio.CancelledError:
            pass
        finally:
            self._running = False
            await self.vsock.stop()
            logger.info(
                f"Firecracker VM[{self._node_index}] exited"
                f" (code= {self._exit_code})"
            )

    async def stop(self) -> None:
        await self.vsock.stop()
        cmd = []
        if self._process:
            cmd = ["sudo", "kill", "-9", str(self._process.pid)]
        try:
            kill_proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await kill_proc.wait()
        except Exception as e:
            logger.warning(f"Failed to pkill firecracker: {e}")
        if self._task and not self._task.done():
            try:
                await asyncio.wait_for(self._task, timeout=TIMEOUT)
            except asyncio.TimeoutError:
                self._task.cancel()
        self._running = False
        logger.info(f"VM[{self._node_index}] Stop completed")


class VMRegistry:
    def __init__(self):
        self._instances: Dict[str, _VMInstance] = {}
        self._lock = Lock()

    def get_or_create(self, node_index: str) -> _VMInstance:
        with self._lock:
            if node_index not in self._instances:
                self._instances[node_index] = _VMInstance(node_index)
            return self._instances[node_index]

    def get(self, node_index: str) -> Optional[_VMInstance]:
        return self._instances.get(node_index)

    def list_running(self) -> List[str]:
        return [
            idx for idx, inst in self._instances.items() if inst.is_running
        ]


vm_manager = VMRegistry()
