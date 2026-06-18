import json
import os
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

from ..constants import CHECKPOINT_INTERVAL
from ..models.task import TaskState, TaskStateAdapter


class StateManager:
    def __init__(self, state_path: str) -> None:
        self.state_path = state_path

    def load(self) -> Optional[TaskState]:
        if not os.path.exists(self.state_path):
            path = Path(self.state_path).parent
            path.mkdir(parents=True, exist_ok=True)
            return None
        with open(self.state_path, "r") as f:
            return TaskStateAdapter.validate_python(json.load(f))

    def save(self, state: TaskState) -> None:
        dir_name = os.path.dirname(self.state_path) or "."
        fd, tmp_path = tempfile.mkstemp(
            prefix=".state_", dir=dir_name, text=True
        )
        try:
            self._write_and_replace(fd, tmp_path, state)
        finally:
            self._remove_tmp(tmp_path)

    def remove(self) -> None:
        try:
            os.remove(self.state_path)
        except OSError as e:
            print(e)

    def _write_and_replace(
        self, fd: int, tmp_path: str, state: TaskState
    ) -> None:
        state.updated_at = time.time()
        with os.fdopen(fd, "w") as f:
            json.dump(state.model_dump(), f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, self.state_path)

    def _remove_tmp(self, tmp_path: str) -> None:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError as e:
                print(e)


# TODO: Refactor when necessary
class StateWriter:

    def __init__(
        self,
        state_manager: StateManager,
    ) -> None:
        self.state_manager = state_manager

        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._state: Optional[TaskState] = None

    def start(self, state: TaskState) -> None:
        self._state = state
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self, *, save: bool = True) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=CHECKPOINT_INTERVAL * 2)
            self._thread = None
        if self._state is not None and save:
            self.state_manager.save(self._state)

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            self._stop_event.wait(timeout=CHECKPOINT_INTERVAL)
            if self._state is not None:
                try:
                    self.state_manager.save(self._state)
                except OSError as e:
                    print(e)
