import os
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

from pydantic import TypeAdapter

from executor.models.task import (
    InputFileMetaData,
    InputItem,
    InputSourceTypeEnum,
)
from utils.logger import get_logger

logger = get_logger(__name__)  # TODO: Check if the new Logger has any problems


_SAFE_TYPES = {
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "list": list,
    "dict": dict,
}


class InputResolver:

    DOWNLOAD_DIR: str = "/tmp/executor_inputs"

    def resolve_input_files(
        self,
        input_files: Optional[List[InputFileMetaData]],
    ) -> List[str]:

        if not input_files:
            return []

        os.makedirs(self.DOWNLOAD_DIR, exist_ok=True)

        download_tasks: List[tuple[int, InputFileMetaData]] = []
        resolved: Dict[int, str] = {}

        for idx, meta in enumerate(input_files):
            if meta.link is not None:
                download_tasks.append((idx, meta))
            elif meta.file_path is not None:
                if not os.path.exists(meta.file_path):
                    raise FileNotFoundError(
                        f"Local input file not found: {meta.file_path}"
                    )
                resolved[idx] = os.path.abspath(meta.file_path)
                logger.info("Local file resolved: %s", resolved[idx])
            else:
                raise ValueError(
                    f"Input file '{meta.file_name}' has neither 'link' nor"
                    "'file_path'."
                )

        # Download remote files concurrently.
        if download_tasks:
            self._download_concurrent(download_tasks, resolved)

        return [resolved[i] for i in range(len(input_files))]

    def resolve_inputs(
        self,
        inputs: Optional[Dict[str, InputItem]],
    ) -> Dict[str, Any]:

        if not inputs:
            return {}

        resolved: Dict[str, Any] = {}
        for name, item in inputs.items():
            if item.source in (
                InputSourceTypeEnum.DEFAULT,
                InputSourceTypeEnum.FUNCTION_OUTPUT,
            ):
                target_type = _SAFE_TYPES.get(item.type)
                if not target_type:
                    raise ValueError(
                        f"Unsupported input type for safety: {item.type}"
                    )
                adapter = TypeAdapter(target_type)
                resolved[name] = adapter.validate_python(item.value)
                logger.debug(
                    "Input '%s' resolved to %s (%s)",
                    name,
                    resolved[name],
                    item.type,
                )
            else:
                raise ValueError(f"Unknown input source type: {item.source}")
        return resolved

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _download_concurrent(
        self,
        tasks: List[tuple[int, InputFileMetaData]],
        resolved: Dict[int, str],
    ) -> None:
        """Download multiple remote files using a thread pool."""
        with ThreadPoolExecutor(max_workers=min(8, len(tasks))) as pool:
            futures = {
                pool.submit(self._download_file, meta): idx
                for idx, meta in tasks
            }
            for future in as_completed(futures):
                idx = futures[future]
                resolved[idx] = future.result()

    def _download_file(self, meta: InputFileMetaData) -> str:
        """Download a single file and return its local absolute path."""
        dest = os.path.join(self.DOWNLOAD_DIR, meta.file_name)
        logger.info("Downloading %s → %s", meta.link, dest)
        urllib.request.urlretrieve(str(meta.link), dest)
        logger.info("Download complete: %s", dest)
        return os.path.abspath(dest)
