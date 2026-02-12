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
