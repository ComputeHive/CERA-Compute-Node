import pytest

from app.executor.models.flattenedcode import FlattenedCode
from app.executor.utils.file_handler import FileHandler


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
