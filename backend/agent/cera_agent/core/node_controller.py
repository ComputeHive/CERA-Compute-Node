from pathlib import Path
from zipfile import ZipFile

from cera_agent.config import app_config
from cera_agent.core.container_manager import ContainerManager
from cera_agent.executor.utils.state_manager import StateManager
from cera_agent.utils.code_extractor import CodeExtractor
from cera_agent.utils.input_resolver import InputResolver
from cera_agent.utils.task_parser import TaskParser
from core.security.aes import AES
from core.security.ecdh import ECDHKeyGenerator
from executor.models.task import (
    ExecutionConfig,
    ExecutorTaskPayload,
    TaskTypeEnum,
)


class NodeController:
    def __init__(self):
        pass

    def handle_task_bytes(self, task_id: str, encrypted_zip: bytes) -> bool:
        aes_key = ECDHKeyGenerator.get_shared_aes_key(
            app_config.COORDINATOR_ID
        )
        zip_bytes = AES(aes_key).decrypt(encrypted_zip)
        parent_dir = Path(app_config.task_volume_path(task_id))
        zip_path = parent_dir / "task_{task_id}.zip"
        task_path = str(parent_dir / "task_{task_id}.json")
        code_path = str(parent_dir / "code_{task_id}.json")
        zip_path.write_bytes(zip_bytes)
        with ZipFile(zip_path, 'r') as zf:
            zf.extractall(parent_dir)
        zip_path.unlink()

        return self._run(task_path, code_path)

    def _run(self, task_path: str, code_path: str) -> bool:
        try:
            task = TaskParser.parse_file(task_path)
            flattened_code = None
            inputs = None
            input_files = None
            input_resolver = InputResolver()
            if task.type != TaskTypeEnum.SHUFFLE_SORT:
                flattened_code = CodeExtractor().extract_from_file(code_path)
            if task.type == TaskTypeEnum.FUNCTION_WITH_INPUT:
                inputs = input_resolver.resolve_inputs(task.inputs)
            else:
                input_files = input_resolver.resolve_input_files(
                    task.input_files
                )
            task_deps = (
                ""
                if task.type == TaskTypeEnum.SHUFFLE_SORT
                else flattened_code.requirements
            )
            volumes = {
                app_config.task_volume_path(str(task.id)): {
                    "bind": app_config.task_volume_path(str(task.id)),
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
