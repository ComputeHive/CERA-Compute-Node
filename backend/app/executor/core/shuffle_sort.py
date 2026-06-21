import itertools
import json
import os
import subprocess
from abc import abstractmethod
from collections import Counter
from pathlib import Path
from typing import Dict, Iterator, List, Optional

import mmh3
from tqdm import tqdm

from ..models.task import ShuffleSortState, TaskTypeEnum
from ..utils.file_handler import FileHandler

OUTPUT_EXT = ".tsv"


class BaseShuffler:
    _SEED = 42

    def __init__(
        self,
        num_partitions: int,
        data_rows: Iterator[dict[str, str]],
        total_rows: int,
        output_path: str,
        state: ShuffleSortState,
    ):
        self.num_partitions = num_partitions
        self.data_rows = data_rows
        self.total_rows = total_rows
        self.state = state
        self.output_path = output_path
        os.makedirs(Path(self.output_path), exist_ok=True)

    @abstractmethod
    def assign_partition(self, key: str) -> int:
        return mmh3.hash(key, self._SEED, signed=False) % self.num_partitions

    def shuffle_files(self) -> List[str]:
        partition_files = []
        partition_handles = []

        for i in range(self.num_partitions):
            path = (
                Path(self.output_path) / f"part-{i:05d}-unsorted{OUTPUT_EXT}"
            )
            partition_files.append(str(path))

        mode = "a" if self.state.next_row_to_write > 0 else "w"

        try:
            for path in partition_files:
                partition_handles.append(open(path, mode, encoding="utf-8"))

            for line in tqdm(
                self.data_rows,
                desc="Shuffling Data",
                total=self.total_rows,
                initial=self.state.next_row_to_write,
                unit="row",
            ):
                key, value = line.values()
                part_id = self.assign_partition(key)
                partition_handles[part_id].write(f"{key}\t{value}\n")
                self.state.next_row_to_write += 1

        finally:
            for handle in partition_handles:
                handle.close()

        return partition_files


class NormalShuffler(BaseShuffler):
    def assign_partition(self, key: str) -> int:
        return super().assign_partition(key)


# TODO: Change the Shuffling Algorithm for Balancing
# TODO: Save the partition assignment in temp file for error handling
class PartitionBalancingShuffler(BaseShuffler):
    def __init__(
        self,
        num_partitions: int,
        data_rows: Iterator[dict[str, str]],
        total_rows: int,
        output_path: str,
        state: ShuffleSortState,
    ):
        super().__init__(
            num_partitions, data_rows, total_rows, output_path, state
        )
        self.data_rows, self.data_rows_copy = itertools.tee(self.data_rows)
        self.rr_counter = Counter()
        self._keys_file_path = (
            Path(self.output_path) / f"assigned_keys{OUTPUT_EXT}"
        )
        self._distribute_keys()

    def _load_keys(self) -> Optional[Dict[str, Dict[int, int]]]:
        result = None
        if Path(self._keys_file_path).exists():
            with open(self._keys_file_path, 'r') as f:
                result = json.loads(f.read())
        return result

    def _distribute_keys(self):
        loaded_keys = self._load_keys()
        if loaded_keys:
            self.parti_dist = loaded_keys
            try:
                os.remove(self._keys_file_path)
            except OSError:
                pass
            finally:
                return
        freq = Counter()
        for line in self.data_rows_copy:
            key, _ = line.values()
            freq[key] += 1
        keys = list(freq.keys())
        if self.num_partitions > len(keys):
            self.num_partitions = len(keys)
        self.parti_dist = {key: {} for key in keys}
        cur_key_idx = 0
        distri_val = 0
        remainder = self.total_rows % self.num_partitions
        base_size = self.total_rows // self.num_partitions

        for i in range(self.num_partitions):
            remaining_parti_cap = base_size + (1 if i < remainder else 0)
            while remaining_parti_cap > 0 and cur_key_idx < len(keys):
                remaining_in_key = freq[keys[cur_key_idx]] - distri_val
                if remaining_in_key == 0:
                    cur_key_idx += 1
                    distri_val = 0
                    continue
                take = min(remaining_parti_cap, remaining_in_key)
                self.parti_dist[keys[cur_key_idx]][i] = take
                distri_val += take
                remaining_parti_cap -= take
        with open(self._keys_file_path, 'w') as f:
            f.write(json.dumps(self.parti_dist))

    def assign_partition(self, key: str) -> int:
        for partition, value in self.parti_dist[key].items():
            if value == 0:
                continue
            self.parti_dist[key][partition] -= 1
            return partition
        return 0


class ShufflerFactory:
    @staticmethod
    def getShuffler(balance_hot_keys: bool):
        return (
            PartitionBalancingShuffler if balance_hot_keys else NormalShuffler
        )


class SortMerge:

    @staticmethod
    def _sort_partition(input_path: str, output_path: str) -> None:
        sorted_path = input_path[:-13] + f".sorted{OUTPUT_EXT}"
        subprocess.run(
            [
                "sort",
                "-k1,1",
                "-t\t",
                "-T",
                "/data",
                input_path,
                "-o",
                sorted_path,
            ],
            check=True,
        )
        partition_iter = FileHandler.stream_rows_multiple_files(
            [sorted_path],
            {"key": "str", "value": "str"},
            0,
            TaskTypeEnum.SHUFFLE_SORT,
        )

        with open(output_path, "w", encoding="utf-8") as outf:
            for key, group in itertools.groupby(
                partition_iter, lambda x: x["key"]
            ):
                values = ", ".join(dic["value"] for dic in group)
                outf.write(f"{key}\t{values}\n")

        os.remove(sorted_path)
        os.remove(input_path)

    @staticmethod
    def sort_all_partitions(
        unsorted_files: List[str], output_dir: str, state: ShuffleSortState
    ) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        final_files = []
        for i in tqdm(
            range(state.next_file_to_write, len(unsorted_files)),
            initial=state.next_file_to_write,
            total=len(unsorted_files),
            desc="Sorting Partitions",
        ):
            final_path = os.path.join(
                output_dir, f"part-{i+1:05d}{OUTPUT_EXT}"
            )
            SortMerge._sort_partition(unsorted_files[i], final_path)
            final_files.append(final_path)
            state.next_file_to_write = i
        return final_files
