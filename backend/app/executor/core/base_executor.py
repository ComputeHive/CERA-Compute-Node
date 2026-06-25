# import multiprocessing
import os
from collections.abc import Iterator
from concurrent.futures import (
    FIRST_COMPLETED,
    ProcessPoolExecutor,
    as_completed,
    wait,
)
from pathlib import Path
from typing import Any, List

from tqdm import tqdm

from ..constants import SHUFFLE_SORT_PARAMS
from ..models.flattenedcode import FlattenedCode
from ..models.task import FileProcessingState, ShuffleSortState, TaskTypeEnum
from ..utils.file_handler import FileHandler
from ..utils.worker import worker, worker_init
from .shuffle_sort import OUTPUT_EXT, ShufflerFactory, SortMerge


class BaseExecutor:

    def __init__(
        self,
        cpu_cores: int,
    ) -> None:
        self.cpu_cores = cpu_cores

    def run_micro_batches(
        self,
        rows: Iterator[dict],
        output_path: str,
        total: int,
        flattened_code: FlattenedCode,
        state: FileProcessingState,
        batch_size: int = 1000,
    ) -> None:

        self.pool = ProcessPoolExecutor(
            max_workers=self.cpu_cores,
            initializer=worker_init,
            initargs=(flattened_code,),
        )
        futures: dict = {}
        write_buf: dict = {}
        next_to_flush = state.next_row_to_write
        submitted = next_to_flush
        print("I'm inside the streaming runner")
        parent_path = Path(output_path).parent
        os.makedirs(parent_path, exist_ok=True)
        mode = "a" if state.next_row_to_write > 0 else "w"
        with (
            open(output_path, mode) as out_f,
            tqdm(
                total=total,
                initial=next_to_flush,
                desc=f"Retry {state.retry}",
                unit="row",
            ) as progress_bar,
        ):
            try:
                max_inflight = self.cpu_cores * 4

                while True:
                    while len(futures) < max_inflight:
                        batch = []
                        try:
                            for _ in range(batch_size):
                                batch.append(next(rows))
                        except StopIteration:
                            pass

                        if not batch:
                            break

                        futures[
                            self.pool.submit(
                                worker,
                                flattened_code.function_name,
                                batch,
                            )
                        ] = (
                            submitted,
                            len(batch),
                        )
                        submitted += len(batch)
                    if not futures:
                        break

                    done, _ = wait(
                        futures,
                        return_when=FIRST_COMPLETED,
                    )
                    for future in done:
                        base_idx, _ = futures.pop(future)
                        try:
                            results = future.result()
                            if isinstance(results, list):
                                for i, res in enumerate(results):
                                    write_buf[base_idx + i] = str(res)
                            else:
                                write_buf[base_idx] = str(results)
                        except Exception as exc:
                            raise RuntimeError(
                                f"Worker failed: {exc}"
                            ) from exc
                        while next_to_flush in write_buf:
                            future_result = (
                                str(write_buf.pop(next_to_flush))
                                .removeprefix('(')
                                .replace('"', '')
                                .removesuffix(")")
                                .replace('"', '')
                            )
                            out_f.write(future_result + "\n")
                            progress_bar.update(1)
                            next_to_flush += 1
                            state.next_row_to_write = next_to_flush

            finally:
                self.pool.shutdown(wait=False, cancel_futures=True)

    def run_macro_task(
        self,
        flattened_code: FlattenedCode,
        output_path: str,
        kwargs: dict,
    ) -> Any:

        self.pool = ProcessPoolExecutor(
            max_workers=self.cpu_cores,
            initializer=worker_init,
            initargs=(flattened_code,),
        )
        try:
            future = self.pool.submit(
                worker, flattened_code.function_name, kwargs
            )
            result = future.result()
            return result

        except Exception as exc:
            raise RuntimeError(f"Macro worker failed: {exc}") from exc
        finally:
            with open(output_path, "w") as out_f:
                out_f.write(str(result))
            self.pool.shutdown(wait=False, cancel_futures=True)

    def run_shuffle_sort(
        self,
        num_of_partitions: int,
        input_files: List[str],
        output_path: str,
        state: ShuffleSortState,
        balance_partitions=False,
    ):
        if state.merge_completed:
            return

        total_rows = FileHandler.total_lines_multiple_files(input_files)
        state.total = total_rows
        shuffled_paths = (
            state.partition_files if state.shuffle_completed else []
        )
        try:
            if state.next_row_to_write > 0:
                print(f"Resuming Shuffle from row {state.next_row_to_write}")
            if state.next_row_to_write == state.total:
                state.shuffle_completed = True
            if not state.shuffle_completed:
                data_rows = FileHandler.stream_rows_multiple_files(
                    input_files,
                    SHUFFLE_SORT_PARAMS,
                    state.next_row_to_write,
                    TaskTypeEnum.SHUFFLE_SORT,
                )
                shuffler = ShufflerFactory.getShuffler(balance_partitions)(
                    num_of_partitions,
                    data_rows,
                    total_rows,
                    output_path,
                    state,
                )
                shuffled_paths = shuffler.shuffle_files()
                state.partition_files = shuffled_paths
                state.shuffle_completed = True
            if state.total == num_of_partitions and state.shuffle_completed:
                state.merge_completed = True
            if not state.merge_completed:
                state.total = num_of_partitions
                with ProcessPoolExecutor(max_workers=self.cpu_cores) as pool:
                    futures = {}
                    for i, unsorted_path in enumerate(shuffled_paths):
                        final_path = os.path.join(
                            output_path, f"part-{i:05d}{OUTPUT_EXT}"
                        )
                        job = pool.submit(
                            SortMerge._sort_partition,
                            unsorted_path,
                            final_path,
                        )
                        futures[job] = final_path
                    completed_count = 0
                    for job in tqdm(
                        as_completed(futures),
                        total=len(futures),
                        desc="Sorting Partitions",
                    ):
                        job.result()
                        completed_count += 1
                        state.next_file_to_write = completed_count
                state.merge_completed = True
        except Exception as exc:
            raise RuntimeError(f"Shuffle Sort pipeline failed: {exc}") from exc
