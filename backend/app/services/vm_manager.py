import asyncio
from app.services.vsock_listener import vsock_listener
from app.logging_config import get_logger
from threading import Lock
from typing import Optional, List
from app.constants import SCRIPT_DIR, TIMEOUT

# TODO: Add VSOCK bridge

logger = get_logger(__name__)


class VMManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
            return cls._instance

    def __init__(self):
        self._running: bool = False
        self._cpu: int = 0  # VCores
        self._ram: int = 0  # MB
        self._disk: int = 0  # MB
        self._process: Optional[asyncio.subprocess.Process] = None
        self._task: Optional[asyncio.Task] = None
        self._exit_code: Optional[int] = None

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
        cmd = ["sudo", "bash", "run_firecracker.sh", str(cpu), str(ram), str(disk)]
        self._process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=SCRIPT_DIR,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            exit_code = await asyncio.wait_for(self._process.wait(), timeout=2.0)
            stderr_output = b""
            if self._process.stderr:
                stderr_output = await self._process.stderr.read()
            raise RuntimeError(
                f"VM process exited immediately (code={exit_code}): "
                f"{stderr_output.decode(errors='replace').strip()}"
            )
        except asyncio.TimeoutError:
            pass
        self._running = True
        self._task = asyncio.create_task(self._write_VM_logs())
        logger.info(f"Firecracker VM started (pid= {self._process.pid})")
        await vsock_listener.start()

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
            logger.info(f"Firecracker VM exited (code= {self._exit_code})")

    async def stop(self) -> None:
        await vsock_listener.stop()
        cmd = ["sudo", "pkill", "-x", "firecracker"]
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
        logger.info("VM Stop completed")


vm_manager = VMManager()
