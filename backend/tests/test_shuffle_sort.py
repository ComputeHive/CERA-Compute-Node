import json
import time
from pathlib import Path
from unittest.mock import patch

from app.executor.core.shuffle_sort import (
    OUTPUT_EXT,
    NormalShuffler,
    PartitionBalancingShuffler,
    SortMerge,
)
from app.executor.models.task import ShuffleSortState, TaskTypeEnum


def _row_stream(rows):
    for key, value in rows:
        yield {"key": key, "value": value}


def test_shuffle_writes_partition_files(tmp_path):
    output = tmp_path / "out"
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    rows = _row_stream([("a", "1"), ("b", "2"), ("a", "3")])

    shuffler = NormalShuffler(
        num_partitions=2,
        data_rows=rows,
        total_rows=3,
        output_path=str(output),
        state=state,
    )
    paths = shuffler.shuffle_files()

    assert len(paths) == 2
    assert state.next_row_to_write == 3
    written = "".join(Path(p).read_text(encoding="utf-8") for p in paths)
    assert "a\t" in written
    assert "b\t" in written


def test_distribute_keys_from_existing_assignment_file(tmp_path):
    output = tmp_path / "out"
    output.mkdir()
    keys_file = output / f"assigned_keys{OUTPUT_EXT}"
    keys_file.write_text(json.dumps({"a": {"0": 2}}), encoding="utf-8")

    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    shuffler = PartitionBalancingShuffler(
        num_partitions=2,
        data_rows=_row_stream([("a", "1"), ("a", "2")]),
        total_rows=2,
        output_path=str(output),
        state=state,
    )

    assert shuffler.parti_dist == {"a": {"0": 2}}
    assert not keys_file.exists()


def test_distribute_keys_persists_new_assignment(tmp_path):
    output = tmp_path / "out"
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    rows = _row_stream([("hot", "1"), ("hot", "2"), ("cold", "3")])

    shuffler = PartitionBalancingShuffler(
        num_partitions=2,
        data_rows=rows,
        total_rows=3,
        output_path=str(output),
        state=state,
    )

    keys_file = output / f"assigned_keys{OUTPUT_EXT}"
    assert keys_file.exists()
    assert sum(shuffler.parti_dist["hot"].values()) == 2


def test_assign_partition_skips_zero_buckets(tmp_path):
    output = tmp_path / "out"
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    shuffler = PartitionBalancingShuffler(
        num_partitions=2,
        data_rows=_row_stream([("k", "1"), ("k", "2")]),
        total_rows=2,
        output_path=str(output),
        state=state,
    )
    shuffler.parti_dist = {"k": {0: 0, 1: 1}}
    assert shuffler.assign_partition("k") == 1


def test_num_partitions_capped_by_unique_keys(tmp_path):
    output = tmp_path / "out"
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    shuffler = PartitionBalancingShuffler(
        num_partitions=5,
        data_rows=_row_stream([("only", "1")]),
        total_rows=1,
        output_path=str(output),
        state=state,
    )
    assert shuffler.num_partitions == 1


def test_sort_partition_merges_duplicate_keys(tmp_path):
    input_path = tmp_path / f"part-00000-unsorted{OUTPUT_EXT}"
    input_path.write_text("", encoding="utf-8")
    sorted_path = tmp_path / f"part-00000.sorted{OUTPUT_EXT}"
    output_path = tmp_path / f"part-00000{OUTPUT_EXT}"

    def fake_run(cmd, check):
        assert check is True
        assert cmd[0] == "sort"
        sorted_path.write_text("a\t1\na\t2\nb\t3\n", encoding="utf-8")

    with (
        patch("app.executor.core.shuffle_sort.subprocess.run", fake_run),
        patch(
            "app.executor.core.shuffle_sort.FileHandler.stream_rows_multiple_files",
            return_value=iter(
                [
                    {"key": "a", "value": "1"},
                    {"key": "a", "value": "2"},
                    {"key": "b", "value": "3"},
                ]
            ),
        ),
    ):
        SortMerge._sort_partition(str(input_path), str(output_path))

    assert output_path.read_text(encoding="utf-8") == "a\t1, 2\nb\t3\n"
    assert not input_path.exists()
    assert not sorted_path.exists()


def test_sort_all_partitions_resumes_from_state(tmp_path):
    unsorted = [str(tmp_path / "u0.tsv"), str(tmp_path / "u1.tsv")]
    for path in unsorted:
        Path(path).write_text("", encoding="utf-8")
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT, updated_at=time.time()
    )
    state = ShuffleSortState(
        task_type=TaskTypeEnum.SHUFFLE_SORT,
        next_file_to_write=1,
        updated_at=time.time(),
    )

    with patch.object(
        SortMerge,
        "_sort_partition",
        side_effect=lambda _, out: Path(out).write_text("ok\n"),
    ) as sort_mock:
        results = SortMerge.sort_all_partitions(
            unsorted, str(tmp_path / "final"), state
        )

    sort_mock.assert_called_once()
    assert len(results) == 1
    assert state.next_file_to_write == 1
