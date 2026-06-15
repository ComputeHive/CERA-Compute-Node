import csv
from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Tuple

from executor.models.task import TaskTypeEnum
from pydantic import TypeAdapter
from utils.logger import get_logger

logger = get_logger(__name__)  # TODO: Check if the new Logger has any problems

DELIMITERS = {"txt": " ", "csv": ",", "tsv": "\t"}


def is_header(line: str) -> bool:
    try:
        float(line.strip())
        return False
    except ValueError:
        return True


class FileHandler:
    @staticmethod
    def _detect_header_per_file(file_path: str) -> bool:
        ext = Path(file_path).suffix.lstrip(".")
        if ext not in ("csv", "tsv"):
            return False

        with open(file_path, "rb") as f:
            sample = f.read(2048).decode(errors="replace")
        try:
            return csv.Sniffer().has_header(sample)
        except csv.Error:
            first_line = sample.splitlines()[0] if sample.strip() else ""
            return is_header(first_line)

    @staticmethod
    def _count_lines_per_file(file_path: str, skip_header: bool) -> int:
        with open(file_path, "rb") as f:
            total = sum(1 for _ in f)
        return total - (1 if skip_header else 0)

    @staticmethod
    def _stream_rows_per_file(
        file_path: str,
        params: Dict[str, str],
        skip_header: bool,
        start_row: int,
        task_type: TaskTypeEnum,
    ) -> Iterator[dict[str, Any]]:
        delimiter: str = DELIMITERS[Path(file_path).suffix.lstrip(".")]
        adapters: dict[str, TypeAdapter] = {
            k: TypeAdapter(v) for k, v in params.items()
        }
        with open(file_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if skip_header and i == 0:
                    continue
                real_idx = i - 1 if skip_header else i
                if real_idx < start_row:
                    continue
                raw_str = line.rstrip("\n")

                if len(params) == 1:
                    k = list(params.keys())[0]
                    row = {k: adapters[k].validate_python(raw_str)}
                else:
                    parts = raw_str.split(delimiter)
                    if task_type != TaskTypeEnum.REDUCE:
                        if len(parts) != len(params):
                            raise ValueError(
                                f"Parameter mismatch: {len(parts)} columns "
                                f"found, but function expects {len(params)}"
                            )
                        row = {
                            k: adapters[k].validate_python(parts[idx])
                            for idx, k in enumerate(params.keys())
                        }
                    else:
                        key_part = parts[0]
                        values_part = delimiter.join(parts[1:])

                        values = [
                            FileHandler._parse_value(p)
                            for p in values_part.split(",")
                        ]
                        row = {
                            "key": adapters["key"].validate_python(key_part),
                            "value": adapters["value"].validate_python(values),
                        }
                if row is not None:
                    yield row

    @staticmethod
    @lru_cache
    def _count_lines_multiple_files(file_paths: Tuple[str]) -> List[int]:
        return [
            FileHandler._count_lines_per_file(
                path, FileHandler._detect_header_per_file(path)
            )
            for path in file_paths
        ]

    @staticmethod
    def _parse_value(raw: str) -> Any:
        p = None
        try:
            p = int(raw)
        except ValueError:
            try:
                p = float(raw)
            except ValueError:
                pass
        return p

    @staticmethod
    def total_lines_multiple_files(file_paths: List[str]) -> int:
        return sum(FileHandler._count_lines_multiple_files(tuple(file_paths)))

    @staticmethod
    def stream_rows_multiple_files(
        file_paths: List[str],
        params: Dict[str, str],
        start_row: int,
        task_type: TaskTypeEnum,
    ) -> Iterator[dict]:
        """
        start_row: the global offset of lines
        """
        has_header = [
            FileHandler._detect_header_per_file(path) for path in file_paths
        ]
        file_lines = FileHandler._count_lines_multiple_files(tuple(file_paths))
        start_idx = 0
        while (
            start_idx < len(file_lines) and start_row >= file_lines[start_idx]
        ):
            start_row = start_row - file_lines[start_idx]
            start_idx += 1
        for i, path in enumerate(file_paths):
            if i < start_idx:
                continue
            yield from FileHandler._stream_rows_per_file(
                path,
                params,
                has_header[i],
                start_row,
                task_type,
            )
