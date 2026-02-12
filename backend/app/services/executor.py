import subprocess
from threading import Lock
from typing import List


class BashExecutor:
    _instance = None
    _lock: Lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
        return cls._instance

    def run(self, cmd: List[str]) -> subprocess.CompletedProcess:
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result
        except Exception as e:
            return subprocess.CompletedProcess(
                args=cmd, returncode=1, stdout="", stderr=f"error: {str(e)}"
            )


executor = BashExecutor()
