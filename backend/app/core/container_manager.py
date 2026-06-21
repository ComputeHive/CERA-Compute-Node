import os
import threading
import time
from hashlib import sha256
from pathlib import Path

import docker
import requests
from docker.errors import ImageNotFound

from app.executor.models.task import ExecutorTaskPayload
from app.executor.utils.logging_config import get_logger

logger = get_logger(__name__)


class ContainerManager:
    def __init__(self) -> None:
        self.client = docker.from_env()
        self.project_root = Path(__file__).resolve().parents[1]
        self.executor_dir = self.project_root / "executor"
        self.image_tag = ""

    def _write_task_requirements(self, deps: str):
        self.requirements_file = self.executor_dir / "task_requirements.txt"
        with open(self.requirements_file, "w") as f:
            f.write(deps)

    def _calculate_hash_image(self):

        h = sha256()
        for path in sorted(self.executor_dir.rglob("*")):
            if (
                not path.is_file()
                or "__pycache__" in path.parts
                or path.suffix in {".pyc"}
            ):
                continue
            rel = str(path.relative_to(self.executor_dir))
            string = f"PATH:{rel} CONTENT"
            h.update(string.encode())
            with open(path, "rb") as f:
                while chunk := f.read(8192):
                    h.update(chunk)
        return h.hexdigest()[:16]

    def _ensure_image(self) -> bool:
        self.image_tag = f"executor:{self._calculate_hash_image()}"
        try:
            self.client.images.get(self.image_tag)
            logger.debug("Image %s already exists", self.image_tag)
            return True
        except ImageNotFound:
            return False

    def build_image(self, deps: str) -> None:
        logger.info("Building executor image: %s", self.image_tag)
        self._write_task_requirements(deps)
        stream = self.client.api.build(
            path=str(self.executor_dir),
            dockerfile=".dockerfile",
            tag=self.image_tag,
            rm=False,
            decode=True,
        )
        for chunk in stream:
            if "stream" in chunk:
                logger.debug(chunk["stream"].rstrip())

            elif "error" in chunk:
                logger.error("Image build error: %s", chunk["error"])
                raise RuntimeError(chunk["error"])
        try:
            os.remove(self.requirements_file)
        except OSError:
            pass
        logger.info("Image build completed %s", self.image_tag)

    def execute(
        self, curr_attempt: int, deps: str, payload: ExecutorTaskPayload
    ) -> bool:
        max_retries = payload.config.resources.max_retries
        attempt = curr_attempt
        succeeded = False
        for attempt in range(curr_attempt, max_retries + 1):
            logger.info(
                "Task %s attempt %d/%d",
                payload.id,
                attempt + 1,
                max_retries + 1,
            )
            try:
                exit_code = self._run_container(deps, payload)
                if exit_code == 0:
                    succeeded = True
                    break
                else:
                    logger.warning(
                        "Task %s exited with code %d", payload.id, exit_code
                    )
                    raise TimeoutError(
                        "Timeout Exceeded, Consider increase timeout"
                    )
            except (Exception, KeyboardInterrupt, TimeoutError) as exc:
                logger.warning(
                    "Execution error for task %s: %s", payload.id, exc
                )
                if attempt < max_retries:
                    logger.info("\n Retrying in 0.5 seconds")
                    time.sleep(0.5)
        if attempt == max_retries:
            logger.error("Task %s failed after maximum retries", payload.id)
        return succeeded

    def _run_container(
        self,
        deps: str,
        payload: ExecutorTaskPayload,
    ) -> int:
        if not self._ensure_image():
            self.build_image(deps)
        payload_json = payload.model_dump_json()
        logger.info(
            "Starting container for task %s (image: %s)",
            payload.id,
            self.image_tag,
        )
        container = self.client.containers.run(
            image=self.image_tag,
            command=[
                "python",
                "-u",
                "-m",
                "executor.main",
                "--payload",
                payload_json,
            ],
            detach=True,
            remove=True,
            mem_limit=f"{payload.config.resources.ram_mb}m",
            cpu_shares=payload.config.resources.cpu_cores * 1_024,
            volumes=payload.config.volumes,
            user=f"{os.getuid()}:{os.getgid()}",
            network_mode="none",
        )

        def stream_logs():
            try:
                output = container.attach(
                    stream=True, logs=True, stdout=True, stderr=True
                )
                for line in output:
                    print((line).decode(errors="replace"), end="", flush=True)
            except Exception:
                pass

        stream_thread = threading.Thread(target=stream_logs, daemon=True)
        stream_thread.start()

        result = None
        try:
            result = container.wait(
                timeout=payload.config.resources.timeout_seconds
            )
            return int(result.get("StatusCode", 2))
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectionError,
            KeyboardInterrupt,
        ):
            logger.warning(
                "Task %s container exceeded timeout of %ds. Killing Container",
                payload.id,
                payload.config.resources.timeout_seconds,
            )
            try:
                container.kill()
                result = container.wait(timeout=0.25)
            except Exception:
                pass
            finally:
                return 137
        finally:
            stream_thread.join(timeout=5)
