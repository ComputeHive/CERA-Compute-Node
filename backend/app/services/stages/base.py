from __future__ import annotations

import asyncio
import enum
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncGenerator, List, Dict, Optional, Any


class StageStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageResult:
    status: StageStatus = StageStatus.PENDING
    return_code: int = -1
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


class StageContext:
    def __init__(self) -> None:
        self._store: Dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default=default)

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value


class Stage(ABC):
    SCRIPTS_DIR: str = os.path.join(os.path.dirname(__file__), "../../../scripts")

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.result = StageResult()

    async def run(
        self, context: StageContext, params: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        self.result.status = StageStatus.RUNNING
        params = params or {}
        yield self._sse(
            "stage_start", {"stage": self.name, "description": self.description}
        )
        try:
            async for line in self.execute(context, params):
                yield line
            self.result.status = StageStatus.COMPLETED
            self.result.message = f"Stage '{self.name}' completed successfully"
        except Exception as e:
            self.result.status = StageStatus.FAILED
            self.result.message = str(e)
            yield self._sse("error", {"stage": self.name, "error": str(e)})
        yield self._sse(
            "stage_end",
            {
                "stage": self.name,
                "status": self.result.status.value,
                "return_code": self.result.return_code,
                "message": self.result.message,
                "data": self.result.data,
            },
        )

    @abstractmethod
    async def execute(
        self, context: StageContext, params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        if False:
            yield
    