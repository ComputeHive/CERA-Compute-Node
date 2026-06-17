import asyncio
import json
from pathlib import Path
from typing import Any, Dict, List
from zipfile import ZIP_DEFLATED, ZipFile

import aiohttp
from cera_agent.config import app_config
from cera_agent.constants import ENDPOINTS
from cera_agent.core.container_manager import ContainerManager
from cera_agent.executor.models.task import (
    ExecutionConfig,
    ExecutorTaskPayload,
    TaskModel,
)
from cera_agent.executor.utils.state_manager import StateManager
from cera_agent.models import (
    EndpointsEnum,
    MsgTypeEnum,
    ReceivedTask,
    TaskSnapShot,
    TaskStatusEnum,
    TaskTypeEnum,
)
from cera_agent.utils.code_extractor import CodeExtractor
from cera_agent.utils.input_resolver import InputResolver
from cera_agent.utils.lib import task_annonce_status, task_completed
from cera_agent.utils.supabase_storage import (
    FINISHED_NODES_BUCKET,
    supabase_storage,
)
from cera_agent.utils.task_parser import TaskParser
from cera_agent.vsock_queue import VsockQueue
from core.security.aes import AES
from core.security.ecdh import ECDHKeyGenerator


class TaskService:
    def __init__(self, session: aiohttp.ClientSession, queue: VsockQueue):
        self._session = session
        self._queue = queue
        self._active: dict[str, str] = {}

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
                print(f"[Poller] GET failed: {exc}")

    async def _poll_once(self) -> None:
        resp = await self._session.get(
            ENDPOINTS[EndpointsEnum.RECEIVE_TASKS_ENDPOINT],
            params={"tasks_number": 3},
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
        for task in received_tasks:

            if task.task_id in self._active:
                continue
            self._active[task.task_id] = task.task_type
            asyncio.create_task(
                self._handle_task(  # TODO: Handle Payment
                    task.task_id, task.task_link, 0.0
                )
            )

    async def _handle_task(
        self, task_id: str, presigned_url: str, price: float
    ) -> None:
        parent_dir = Path(app_config.task_volume_path(task_id))
        parent_dir.mkdir(parents=True, exist_ok=True)
        await self._queue.put(
            task_annonce_status(task_id, MsgTypeEnum.TASK_RECEIVED)
        )
        try:
            async with self._session.get(presigned_url) as resp:
                resp.raise_for_status()
                encrypted_zip = await resp.read()
            task_path, code_path = await asyncio.to_thread(
                self._decrypt_and_extract, task_id, encrypted_zip, parent_dir
            )
            task = await asyncio.to_thread(TaskParser.parse_file, task_path)
            resolver = InputResolver(self._session, parent_dir)
            input_files = resolver.resolve_input_files(
                None
                if task.type == TaskTypeEnum.FUNCTION_WITH_INPUT
                else task.input_files
            )
            inputs = resolver.resolve_inputs(
                task.inputs
                if task.type == TaskTypeEnum.FUNCTION_WITH_INPUT
                else None
            )
            await self._queue.put(
                task_annonce_status(task_id, MsgTypeEnum.TASK_RUNNING)
            )
            success = await asyncio.to_thread(
                self._run, task, code_path, input_files, inputs, parent_dir
            )

            if success:
                # TODO: Add the payment Step to  the coordinator
                await self._queue.put(task_completed(task_id, price))
                output_links = await asyncio.to_thread(
                    self._package_and_upload_output, task_id, task.type
                )
                try:
                    resp = await self._session.post(
                        ENDPOINTS[EndpointsEnum.TASK_FINISHED_ENDPOINT],
                        json=json.dumps(
                            {"task_id": task_id, "output_link": output_links}
                        ),
                        headers=app_config.HEADERS,
                    )
                except aiohttp.ClientError as exc:
                    print(
                        "[Poller] failed to send finished task to coordinator:"
                        f" {exc}"
                    )
            else:
                await self._queue.put(
                    task_annonce_status(task_id, MsgTypeEnum.TASK_FAILED)
                )
                try:
                    resp = await self._session.post(
                        ENDPOINTS[EndpointsEnum.TASK_FAILED_ENDPOINT],
                        json=json.dumps(
                            {
                                "task_id": task_id,
                            }
                        ),
                        headers=app_config.HEADERS,
                    )
                except aiohttp.ClientError as exc:
                    print(
                        "[Poller] failed to send finished task to coordinator:"
                        f" {exc}"
                    )
        except Exception as exc:
            print(f"[Poller] task{task_id} raised: {exc}")
            await self._queue.put(
                task_annonce_status(task_id, MsgTypeEnum.TASK_FAILED)
            )
        finally:
            self._active.pop(task_id, None)

    def _decrypt_and_extract(
        self, task_id: str, encrypted_zip: bytes, parent_dir: Path
    ) -> tuple[str, str]:
        aes_key = ECDHKeyGenerator.get_shared_aes_key(
            app_config.COORDINATOR_ID
        )
        zip_bytes = AES(aes_key).decrypt(encrypted_zip)
        zip_path = parent_dir / f"task_{task_id}.zip"
        task_path = str(parent_dir / f"task_{task_id}.json")
        code_path = str(parent_dir / f"code_{task_id}.json")
        zip_path.write_bytes(zip_bytes)
        with ZipFile(zip_path, 'r') as zf:
            zf.extractall(parent_dir)
        zip_path.unlink()

        return task_path, code_path

    def _run(
        self,
        task: TaskModel,
        code_path: str,
        input_files: List[str],
        inputs: Dict[str, Any],
        parent_dir: Path,
    ) -> bool:
        try:
            flattened_code = None
            if task.type != TaskTypeEnum.SHUFFLE_SORT:
                flattened_code = CodeExtractor().extract_from_file(code_path)

            task_deps = (
                ""
                if task.type == TaskTypeEnum.SHUFFLE_SORT
                else flattened_code.requirements
            )
            task_volume = str(parent_dir)
            volumes = {
                task_volume: {
                    "bind": task_volume,
                    "mode": 'rw',
                },
                app_config.state_dir: {"bind": "/data", "mode": "rw"},
            }
            cfg = ExecutionConfig(resources=task.resources, volumes=volumes)
            state = StateManager(app_config.state_path(task.id)).load()
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
            docker_controller = ContainerManager()
            current_attempt = state.retry if state else 0
            succeeded = docker_controller.execute(
                current_attempt, task_deps, payload
            )
            if succeeded:
                print("Execution Succeeded")
                return succeeded
        except Exception:
            pass
        return False

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
                supabase_storage.upload(
                    FINISHED_NODES_BUCKET, object_name, zip_path.read_bytes()
                )
                return [
                    supabase_storage.generate_presigned_url(
                        FINISHED_NODES_BUCKET, object_name
                    )
                ]
            finally:
                zip_path.unlink(missing_ok=True)

        output_links = []
        for part_file in sorted(output_path.rglob("part-*")):
            zip_path = output_path.parent / f"{part_file.stem}_{task_id}.zip"
            with ZipFile(zip_path, "w", ZIP_DEFLATED) as zf:
                zf.write(part_file, part_file.name)
            object_name = f"{task_id}/{part_file.stem}.zip"
            try:
                supabase_storage.upload(
                    FINISHED_NODES_BUCKET, object_name, zip_path.read_bytes()
                )
                output_links.append(
                    supabase_storage.generate_presigned_url(
                        FINISHED_NODES_BUCKET, object_name
                    )
                )
            finally:
                zip_path.unlink(missing_ok=True)
        return output_links
