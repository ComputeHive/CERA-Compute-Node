import pytest

from app.executor.models.task import TaskTypeEnum
from app.executor.utils.file_handler import FileHandler, is_header


def test_numeric_line_is_not_header():
    assert is_header("42.5") is False


def test_text_line_is_header():
    assert is_header("name,age") is True


def test_detect_header_non_tabular_extension(tmp_path):
    path = tmp_path / "data.txt"
    path.write_text("a b\n1 2\n", encoding="utf-8")
    assert FileHandler._detect_header_per_file(str(path)) is False


def test_detect_header_csv_with_sniffer(tmp_path):
    path = tmp_path / "data.csv"
    path.write_text("name,age\nAlice,30\n", encoding="utf-8")
    assert FileHandler._detect_header_per_file(str(path)) is True


def test_count_lines_respects_header_skip(tmp_path):
    path = tmp_path / "data.tsv"
    path.write_text("k\tv\na\t1\nb\t2\n", encoding="utf-8")
    assert FileHandler._count_lines_per_file(str(path), skip_header=True) == 2
    assert FileHandler._count_lines_per_file(str(path), skip_header=False) == 3


def test_parse_value_coercion():
    assert FileHandler._parse_value("42") == 42
    assert FileHandler._parse_value("3.14") == 3.14
    assert FileHandler._parse_value("'hello'") == "hello"


def test_stream_single_column_txt(tmp_path):
    path = tmp_path / "nums.txt"
    path.write_text("1\n2\n3\n", encoding="utf-8")
    rows = list(
        FileHandler._stream_rows_per_file(
            str(path),
            {"x": "int"},
            skip_header=False,
            start_row=1,
            task_type=TaskTypeEnum.MAP,
        )
    )
    assert rows == [{"x": 2}, {"x": 3}]


def test_stream_multi_column_mismatch_raises(tmp_path):
    path = tmp_path / "bad.csv"
    path.write_text("1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Parameter mismatch"):
        list(
            FileHandler._stream_rows_per_file(
                str(path),
                {"a": "int", "b": "int"},
                skip_header=False,
                start_row=0,
                task_type=TaskTypeEnum.MAP,
            )
        )


def test_stream_reduce_rows(tmp_path):
    path = tmp_path / "reduce.csv"
    path.write_text("k,1,2,3\n", encoding="utf-8")
    rows = list(
        FileHandler._stream_rows_per_file(
            str(path),
            {"key": "str", "value": "list"},
            skip_header=False,
            start_row=0,
            task_type=TaskTypeEnum.REDUCE,
        )
    )
    assert rows == [{"key": "k", "value": [1, 2, 3]}]


def test_total_and_stream_across_multiple_files(tmp_path):
    first = tmp_path / "a.tsv"
    second = tmp_path / "b.tsv"
    first.write_text("k\tv\na\t1\n", encoding="utf-8")
    second.write_text("b\t2\nc\t3\n", encoding="utf-8")

    assert (
        FileHandler.total_lines_multiple_files([str(first), str(second)]) == 4
    )

    rows = list(
        FileHandler.stream_rows_multiple_files(
            [str(first), str(second)],
            {"key": "str", "value": "str"},
            start_row=2,
            task_type=TaskTypeEnum.SHUFFLE_SORT,
        )
    )
    assert rows[1] == {"key": "c", "value": "3"}
