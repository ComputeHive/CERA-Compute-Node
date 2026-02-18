from __future__ import annotations
from typing import Any, AsyncGenerator, Dict
from .base import Stage, StageContext


class BuildImageStage(Stage):
    def __init__(self) -> None:
        super().__init__(
            name="build ubuntu image",
            description="Build the firecracker vm root filesystem image",
        )

    async def execute(
        self, context: StageContext, params: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        build_method: str = params.get("method", "normal")
        yield self._sse(
            "info", {"message": f"Building image with method '{build_method}'"}
        )
        
