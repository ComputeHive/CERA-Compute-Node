import asyncio
import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from zipfile import ZIP_DEFLATED, ZipFile

import aiohttp

from app.config import app_config
from app.constants import ENDPOINTS
from app.core.container_manager import ContainerManager
from app.core.security.aes import AES
from app.core.security.ecdh import ECDHKeyGenerator
from app.enums import EndpointsEnum
from app.executor.models.task import (
    ExecutionConfig,
    ExecutorTaskPayload,
    TaskModel,
)
from app.executor.utils.logging_config import get_logger
from app.executor.utils.state_manager import StateManager
from app.models import (
    ReceivedTask,
    TaskRecord,
    TaskSnapShot,
    TaskStatusEnum,
    TaskTypeEnum,
)
from app.observer import MessageObserver
from app.utils.code_extractor import CodeExtractor
from app.utils.input_resolver import InputResolver
from app.utils.lib import calculate_compute_price
from app.utils.supabase_storage import FINISHED_NODES_BUCKET, supabase_storage
from app.utils.task_parser import TaskParser

logger = get_logger(__name__)


class TaskService:
    def __init__(self, session: aiohttp.ClientSession, queue: MessageObserver):
        self._session = session
        self._observer = queue
        self._active: dict[str, TaskTypeEnum] = {}

    @property
    def assigned_tasks(self) -> List[TaskSnapShot]:
        return [
            TaskSnapShot(
                task_id=tid,
                task_type=TaskTypeEnum(ttype),
                task_status=TaskStatusEnum.EXECUTING,
            )
            for tid, ttype in self._active.items()
        ]

    async def run_poller(self):
        while True:
            await asyncio.sleep(app_config.TASK_POLL_INTERVAL)
            try:
                await self._poll_once()
            except aiohttp.ClientError as exc:
                logger.error("Task polling failed: %s", exc)

    async def _poll_once(self) -> None:
        resp = await self._session.get(
            ENDPOINTS[EndpointsEnum.RECEIVE_TASKS_ENDPOINT],
            params={"tasks_number": 1},
            headers=app_config.HEADERS,
        )
        resp.raise_for_status()
        tasks = await resp.json()
        received_tasks = [
            ReceivedTask(
                task_id=t["task_id"],
                task_type=TaskTypeEnum(t["task_type"]),
                task_link=t["task_link"],
            )
            for t in tasks["tasks"]
        ]
        logger.info("Received %d Tasks", len(received_tasks))
        for task in received_tasks:
            if task.task_id in self._active:
                continue
            self._active[task.task_id] = task.task_type
            self._observer.update_task(
                TaskRecord(
                    task_id=task.task_id,
                    price=0.0,
                    status=TaskStatusEnum.RECEIVED,
                )
            )
            logger.info("Task %s accepted", task.task_id)
            asyncio.create_task(
                self._handle_task(task.task_id, task.task_link)
            )

    async def _notify_success(
        self,
        task_id: str,
        output_links: list,
        started_at: datetime,
        ended_at: datetime,
    ) -> bool:
        try:
            finished_task = {
                "task_id": task_id,
                "output_links": output_links,
                "started_at": started_at.isoformat(),
                "ended_at": ended_at.isoformat(),
            }
            await self._session.post(
                ENDPOINTS[EndpointsEnum.TASK_FINISHED_ENDPOINT],
                json=finished_task,
                headers=app_config.HEADERS,
            )
            logger.debug("Notification sent for task %s", task_id)
            return True
        except aiohttp.ClientError as exc:
            logger.error(
                "Failed to send finished task %s to coordinator: %s",
                task_id,
                exc,
            )
            return False

    async def _notify_failure(self, task_id: str) -> None:
        try:
            logger.debug("Notifying failure for task %s", task_id)
            await self._session.post(
                ENDPOINTS[EndpointsEnum.TASK_FAILED_ENDPOINT],
                json={"task_id": task_id},
                headers=app_config.HEADERS,
            )
        except aiohttp.ClientError as exc:
            logger.error(
                "Failed to notify task %s failure to coordinator: %s",
                task_id,
                exc,
            )

    async def _handle_task(self, task_id: str, presigned_url: str) -> None:
        parent_dir = Path(app_config.task_volume_path(task_id))
        parent_dir.mkdir(parents=True, exist_ok=True)
        logger.info("Start Downloading task %s files", task_id)
        try:
            async with self._session.get(presigned_url) as resp:
                resp.raise_for_status()
                encrypted_zip = await resp.read()
            task_dict, code_content = await asyncio.to_thread(
                self._decrypt_and_extract, task_id, encrypted_zip
            )
            task = await asyncio.to_thread(TaskParser.parse_dict, task_dict)
            resolver = InputResolver(self._session, parent_dir)
            input_files = await resolver.resolve_input_files(
                None
                if task.type == TaskTypeEnum.FUNCTION_WITH_INPUT
                else task.input_files
            )
            inputs = resolver.resolve_inputs(
                task.inputs
                if task.type == TaskTypeEnum.FUNCTION_WITH_INPUT
                else None
            )
            started_at = datetime.now(timezone.utc)
            success, ended_at = await asyncio.to_thread(
                self._run, task, code_content, input_files, inputs, parent_dir
            )
            if success:
                output_links = await asyncio.to_thread(
                    self._package_and_upload_output, task_id, task.type
                )
                logger.info(
                    "Task %s finished, output_links: %s", task_id, output_links
                )
                notified = await self._notify_success(
                    task_id, output_links, started_at, ended_at
                )
                if not notified:
                    await self._notify_failure(task_id)
        except Exception as exc:
            logger.exception(
                "Unhandled error handling task %s: %s", task_id, exc
            )
            await self._notify_failure(task_id)
            self._observer.update_task(
                TaskRecord(
                    task_id=task_id, price=0.0, status=TaskStatusEnum.FAILED
                )
            )
        finally:
            self._active.pop(task_id, None)

    def _decrypt_and_extract(
        self, task_id: str, encrypted_zip: bytes
    ) -> tuple[dict, str]:
        aes_key = ECDHKeyGenerator.get_shared_aes_key(
            app_config.COORDINATOR_ID
        )
        zip_bytes = AES(aes_key).decrypt(encrypted_zip)
        code_content = ""
        with ZipFile(io.BytesIO(zip_bytes), 'r') as zf:
            task_content = zf.read(f"task_{task_id}.json").decode("utf-8")
            task_dict = json.loads(task_content)
            code_filename = f"code_{task_id}.md"
            if code_filename in zf.namelist():
                code_content = zf.read(code_filename).decode("utf-8")
                print(f"Code content: {code_content}")
        return task_dict, code_content

    def _run(
        self,
        task: TaskModel,
        code_content: str,
        input_files: List[str],
        inputs: Dict[str, Any],
        parent_dir: Path,
    ) -> tuple[bool, datetime]:
        flattened_code = None
        if task.type != TaskTypeEnum.SHUFFLE_SORT:
            flattened_code = CodeExtractor().extract_from_string(code_content)
        task_deps = (
            ""
            if task.type == TaskTypeEnum.SHUFFLE_SORT
            else flattened_code.requirements
        )
        task_volume = str(parent_dir)
        state_volume = str(app_config.state_dir)
        volumes = {
            task_volume: {"bind": task_volume, "mode": "rw"},
            state_volume: {"bind": state_volume, "mode": "rw"},
        }
        state_path = app_config.state_path(str(task.id))
        cfg = ExecutionConfig(
            resources=task.resources, volumes=volumes, state_path=state_path
        )
        state = StateManager(state_path).load()
        payload = ExecutorTaskPayload(
            id=task.id,
            task_type=task.type,
            num_of_partitions=task.resources.num_of_partitions,
            balance_partitions=task.resources.balanced_partition,
            flattened_code=flattened_code,
            input_files=input_files,
            input_params=inputs,
            config=cfg,
            output_path=app_config.output_path(task.type, str(task.id)),
        )
        current_attempt = state.retry if state else 0
        start_time = datetime.now(timezone.utc)
        self._observer.update_task(
            TaskRecord(
                task_id=str(payload.id),
                price=0.0,
                status=TaskStatusEnum.EXECUTING,
                started_at=start_time,
            )
        )
        succeeded = ContainerManager().execute(
            current_attempt, task_deps, payload
        )
        end_time = datetime.now(timezone.utc)
        delta = end_time - start_time
        price = calculate_compute_price(
            float(delta.total_seconds()),
            payload.config.resources.cpu_cores,
            payload.config.resources.disk_mb,
            payload.config.resources.ram_mb,
        )
        self._observer.update_task(
            TaskRecord(
                task_id=str(payload.id),
                price=price,
                status=(
                    TaskStatusEnum.FINISHED
                    if succeeded
                    else TaskStatusEnum.FAILED
                ),
                started_at=start_time,
                ended_at=end_time,
            )
        )
        if succeeded:
            print("Execution Succeeded")
        return succeeded, end_time

    def _package_and_upload_output(
        self, task_id: str, task_type: TaskTypeEnum
    ) -> List[str]:
        output_path = Path(app_config.output_path(task_type, task_id))
        if task_type != TaskTypeEnum.SHUFFLE_SORT:
            zip_path = output_path.parent / f"output_{task_id}.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
                zf.write(output_path, output_path.name)
            object_name = f"{task_id}.zip"
            try:
                output_link = supabase_storage.upload_encrypted_and_get_url(
                    FINISHED_NODES_BUCKET, object_name, zip_path.read_bytes()
                )
                return [output_link]
            finally:
                zip_path.unlink(missing_ok=True)
        output_links = []
        for part_file in sorted(output_path.rglob("part-*")):
            zip_path = output_path.parent / f"{part_file.stem}_{task_id}.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
                zf.write(part_file, part_file.name)
            object_name = f"{task_id}/{part_file.stem}.zip"
            try:
                output_link = supabase_storage.upload_encrypted_and_get_url(
                    FINISHED_NODES_BUCKET, object_name, zip_path.read_bytes()
                )
                output_links.append(output_link)
            finally:
                zip_path.unlink(missing_ok=True)
        return output_links
