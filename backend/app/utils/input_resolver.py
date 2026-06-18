import asyncio
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp
from pydantic import TypeAdapter

from app.executor.models.task import (
    InputFileMetaData,
    InputItem,
    InputSourceTypeEnum,
)


class InputResolver:
    def __init__(self, session: aiohttp.ClientSession, download_dir: Path):
        self._session = session
        self._download_dir = download_dir

    async def resolve_input_files(
        self,
        input_files: Optional[List[InputFileMetaData]],
    ) -> List[str]:

        if not input_files:
            return []

        self._download_dir.mkdir(parents=True, exist_ok=True)
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

            else:
                raise ValueError(
                    f"Input file '{meta.file_name}' has neither 'link' nor"
                    "'file_path'."
                )

        if download_tasks:
            download_tasks_fn = [
                self._download_file(meta) for _, meta in download_tasks
            ]
            paths = await asyncio.gather(*download_tasks_fn)
            for (idx, _), path in zip(download_tasks, paths):
                resolved[idx] = path

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

                adapter = TypeAdapter(item.type)
                resolved[name] = adapter.validate_python(item.value)

            else:
                raise ValueError(f"Unknown input source type: {item.source}")
        return resolved

    async def _download_file(self, meta: InputFileMetaData) -> str:
        destination = self._download_dir / meta.file_name
        async with self._session.get(str(meta.link)) as resp:
            resp.raise_for_status()
            destination.write_bytes(await resp.read())
        if zipfile.is_zipfile(destination):
            with zipfile.ZipFile(destination) as zf:
                extracted_name = zf.namelist()[0]
                zf.extract(extracted_name, self._download_dir)
            destination.unlink()
            meta.file_name = extracted_name
            meta.file_path = str(self._download_dir / extracted_name)
        else:
            meta.file_path = str(destination)

        return meta.file_path
