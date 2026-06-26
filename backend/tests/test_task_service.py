import io
import json
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import aiohttp
import pytest

from app.core.task_service import TaskService
from app.executor.models.task import (
    DecoratorParamsModel,
    InputFileMetaData,
    TaskModel,
)
from app.models import TaskStatusEnum, TaskTypeEnum
from app.observer import MessageObserver


@pytest.fixture
def observer():
    return MessageObserver()


@pytest.fixture
def session():
    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.fixture
def service(session, observer):
    return TaskService(session, observer)


@pytest.fixture
def task_id():
    return str(uuid4())


def _build_encrypted_task_zip(
    task_id: str, task_dict: dict, code: str = ""
) -> bytes:
    buf = io.BytesIO()
    with ZipFile(buf, "w", ZIP_DEFLATED) as zf:
        zf.writestr(f"task_{task_id}.json", json.dumps(task_dict))
        if code:
            zf.writestr(f"code_{task_id}.md", code)
    return buf.getvalue()


class TestTaskServiceProperties:
    def test_assigned_tasks_reflects_active_map(self, service):
        service._active = {"t1": TaskTypeEnum.MAP, "t2": TaskTypeEnum.REDUCE}
        snapshots = service.assigned_tasks
        assert {s.task_id for s in snapshots} == {"t1", "t2"}
        assert all(
            s.task_status == TaskStatusEnum.EXECUTING for s in snapshots
        )


class TestTaskServicePolling:

    @pytest.mark.asyncio
    async def test_poll_once_skips_duplicate_active_task(
        self, service, session
    ):
        service._active["task-1"] = TaskTypeEnum.MAP
        response = AsyncMock()
        response.raise_for_status = MagicMock()
        response.json = AsyncMock(
            return_value={
                "tasks": [
                    {
                        "task_id": "task-1",
                        "task_type": "map",
                        "task_link": "https://example.com/task.zip",
                    }
                ]
            }
        )
        session.get = AsyncMock(return_value=response)

        with patch.object(service, "_handle_task", new=AsyncMock()) as handle:
            await service._poll_once()

        handle.assert_not_awaited()


def observer_task_status(service: TaskService, task_id: str) -> TaskStatusEnum:
    report = next(r for r in service._observer.latest_tasks if r.id == task_id)
    return report.status


class TestTaskServiceNotifications:
    @pytest.mark.asyncio
    async def test_notify_success_returns_true(self, service, session):
        session.post = AsyncMock()
        ok = await service._notify_success(
            "t1",
            ["https://out"],
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )
        assert ok is True

    @pytest.mark.asyncio
    async def test_notify_success_returns_false_on_client_error(
        self, service, session
    ):
        session.post = AsyncMock(side_effect=aiohttp.ClientError("down"))
        ok = await service._notify_success(
            "t1",
            [],
            datetime.now(timezone.utc),
            datetime.now(timezone.utc),
        )
        assert ok is False

    @pytest.mark.asyncio
    async def test_notify_failure_swallows_client_error(
        self, service, session
    ):
        session.post = AsyncMock(side_effect=aiohttp.ClientError("down"))
        await service._notify_failure("t1")


class TestTaskServiceHandleTask:
    @pytest.mark.asyncio
    async def test_handle_task_success_flow(
        self, service, session, task_id, tmp_path
    ):
        task_dict = {
            "id": task_id,
            "type": "map",
            "resources": {"cpu_cores": 1, "ram_mb": 256, "disk_mb": 512},
            "input_files": [{"file_name": "in.csv", "file_path": "in.csv"}],
        }

        encrypted_zip = _build_encrypted_task_zip(
            task_id,
            task_dict,
            code="```python\ndef map_fn(x):\n    return x\n```",
        )

        download_resp = AsyncMock(
            read=AsyncMock(return_value=encrypted_zip),
        )
        download_resp.raise_for_status = Mock()

        session.get.return_value.__aenter__.return_value = download_resp

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch.object(
                service,
                "_decrypt_and_extract",
                return_value=(task_dict, "code"),
            ),
            patch(
                "app.core.task_service.TaskParser.parse_dict",
                return_value=TaskModel(**task_dict),
            ),
            patch("app.core.task_service.InputResolver") as resolver_cls,
            patch.object(
                service,
                "_run_timed",
                return_value=(True, datetime.now(timezone.utc)),
            ),
            patch.object(
                service,
                "_package_and_upload_output",
                return_value=["https://upload"],
            ),
            patch.object(
                service,
                "_notify_success",
                new=AsyncMock(),
            ) as notify_ok,
        ):
            cfg.task_volume_path.return_value = str(tmp_path / task_id)

            resolver_cls.return_value.resolve_input_files = AsyncMock(
                return_value=["in.csv"]
            )
            resolver_cls.return_value.resolve_inputs.return_value = {}

            await service._handle_task(task_id, "https://download")

        notify_ok.assert_awaited_once()
        assert task_id not in service._active

    @pytest.mark.asyncio
    async def test_handle_task_notifies_failure_when_success_notify_fails(
        self, service, session, task_id, tmp_path
    ):
        task_dict = {
            "id": task_id,
            "type": "map",
            "resources": {"cpu_cores": 1, "ram_mb": 256, "disk_mb": 512},
            "input_files": [{"file_name": "in.csv", "file_path": "in.csv"}],
        }

        download_resp = AsyncMock()
        download_resp.raise_for_status = MagicMock()
        download_resp.read = AsyncMock(return_value=b"zip")
        download_cm = AsyncMock()
        download_cm.__aenter__.return_value = download_resp
        download_cm.__aexit__.return_value = False
        session.get = AsyncMock(return_value=download_cm)

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch.object(
                service,
                "_decrypt_and_extract",
                return_value=(task_dict, "code"),
            ),
            patch(
                "app.core.task_service.TaskParser.parse_dict",
                return_value=TaskModel(**task_dict),
            ),
            patch("app.core.task_service.InputResolver") as resolver_cls,
            patch.object(
                service,
                "_run_timed",
                return_value=(True, datetime.now(timezone.utc)),
            ),
            patch.object(
                service,
                "_package_and_upload_output",
                return_value=["https://upload"],
            ),
            patch.object(
                service, "_notify_success", new=AsyncMock(return_value=False)
            ),
            patch.object(
                service, "_notify_failure", new=AsyncMock()
            ) as notify_fail,
        ):
            cfg.task_volume_path.return_value = str(tmp_path / task_id)
            resolver_cls.return_value.resolve_input_files = AsyncMock(
                return_value=["in.csv"]
            )
            resolver_cls.return_value.resolve_inputs.return_value = {}

            await service._handle_task(task_id, "https://download")

        notify_fail.assert_awaited_once_with(task_id)

    @pytest.mark.asyncio
    async def test_handle_task_failure_updates_observer(
        self, service, session, task_id, tmp_path
    ):
        download_resp = AsyncMock()
        download_resp.raise_for_status = MagicMock()
        download_resp.read = AsyncMock(
            side_effect=RuntimeError("download failed")
        )
        download_cm = AsyncMock()
        download_cm.__aenter__.return_value = download_resp
        download_cm.__aexit__.return_value = False
        session.get = AsyncMock(return_value=download_cm)

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch.object(service, "_notify_failure", new=AsyncMock()),
        ):
            cfg.task_volume_path.return_value = str(tmp_path / task_id)
            await service._handle_task(task_id, "https://download")

        assert observer_task_status(service, task_id) == TaskStatusEnum.FAILED
        assert task_id not in service._active


class TestTaskServiceRunPaths:
    def test_decrypt_and_extract_reads_task_and_code(self, service, task_id):
        task_dict = {
            "id": task_id,
            "type": "map",
            "input_files": [{"file_name": "a"}],
        }
        zip_bytes = _build_encrypted_task_zip(task_id, task_dict, code="# fn")

        with (
            patch("app.core.task_service.ECDHKeyGenerator.get_shared_aes_key"),
            patch("app.core.task_service.AES") as aes_cls,
        ):
            aes_cls.return_value.decrypt.return_value = zip_bytes
            parsed_task, code = service._decrypt_and_extract(
                task_id, b"encrypted"
            )

        assert parsed_task["id"] == task_id
        assert code == "# fn"

    def test_run_failure_updates_observer_failed(self, service, tmp_path):
        raw = {"file_name": "in.csv", "file_path": "in.csv"}
        task = TaskModel(
            id=uuid4(),
            type=TaskTypeEnum.SHUFFLE_SORT,
            resources=DecoratorParamsModel(
                cpu_cores=1,
                ram_mb=256,
                disk_mb=512,
                num_of_partitions=2,
            ),
            input_files=[InputFileMetaData(**raw, link=None)],
        )

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch("app.core.task_service.StateManager") as state_mgr_cls,
            patch("app.core.task_service.ContainerManager") as docker_cls,
        ):
            cfg.task_volume_path.return_value = str(tmp_path)
            cfg.state_dir = str(tmp_path / "state")
            cfg.state_path.return_value = str(
                tmp_path / "state" / "state.json"
            )
            cfg.output_path.return_value = str(tmp_path)
            state_mgr_cls.return_value.load.return_value = MagicMock(retry=0)
            docker_cls.return_value.execute.return_value = False

            ok = service._run(task, "", ["in.tsv"], {}, tmp_path)

        assert ok is False
        assert any(
            r.status == TaskStatusEnum.FAILED
            for r in service._observer.latest_tasks
        )

    def test_run_timed_returns_success_flag_and_end_time(self, service):
        with patch.object(service, "_run", return_value=True):
            success, ended = service._run_timed(
                MagicMock(), "code", [], {}, Path("/tmp")
            )
        assert success is True
        assert ended.tzinfo == timezone.utc

    def test_package_and_upload_single_output(
        self, service, task_id, tmp_path
    ):
        output_file = tmp_path / f"task_{task_id}.csv"
        output_file.write_text("1,2\n", encoding="utf-8")

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch(
                "app.core.task_service.supabase_storage.upload_encrypted_and_get_url",
                return_value="https://signed",
            ),
        ):
            cfg.output_path.return_value = str(output_file)
            links = service._package_and_upload_output(
                task_id, TaskTypeEnum.MAP
            )

        assert links == ["https://signed"]

    def test_package_and_upload_shuffle_sort_partitions(
        self, service, task_id, tmp_path
    ):
        part = tmp_path / "part-00000.tsv"
        part.write_text("a\t1\n", encoding="utf-8")

        with (
            patch("app.core.task_service.app_config") as cfg,
            patch(
                "app.core.task_service.supabase_storage.upload_encrypted_and_get_url",
                return_value="https://part",
            ),
        ):
            cfg.output_path.return_value = str(tmp_path)
            links = service._package_and_upload_output(
                task_id, TaskTypeEnum.SHUFFLE_SORT
            )

        assert links == ["https://part"]
