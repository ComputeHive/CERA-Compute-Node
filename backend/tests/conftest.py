from unittest.mock import AsyncMock
from uuid import uuid4

import aiohttp
import pytest

from app.core.task_service import TaskService
from app.executor.models.flattenedcode import FlattenedCode
from app.executor.utils.file_handler import FileHandler
from app.observer import MessageObserver


@pytest.fixture(autouse=True)
def clear_file_handler_cache():
    FileHandler._count_lines_multiple_files.cache_clear()
    yield
    FileHandler._count_lines_multiple_files.cache_clear()


@pytest.fixture
def sample_flattened_code() -> FlattenedCode:
    return FlattenedCode(
        requirements="",
        code_deps="",
        function_content=(
            "def double(x):\n"
            "    return x * 2\n"
            "\n"
            "def add(a, b):\n"
            "    return a + b\n"
        ),
        function_name="double",
    )


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
