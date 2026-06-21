from datetime import datetime, timedelta, timezone
from typing import Any

from app.models import TaskRecord, TaskReport


class MessageObserver:
    def __init__(self) -> None:
        self._latest_metrics: dict[str, Any] = {}
        self._tasks: dict[str, TaskReport] = {}

    @property
    def latest_metrics(self) -> dict[str, Any]:
        return dict(self._latest_metrics)

    @property
    def latest_tasks(self) -> list[TaskReport]:
        return list(self._tasks.values())

    def update_metrics(self, metrics: dict[str, Any]) -> None:
        self._latest_metrics = {
            **metrics,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

    def update_task(self, rec: TaskRecord) -> None:
        now = datetime.now(timezone.utc)
        if rec.started_at:
            end = rec.ended_at or now
            delta = end - rec.started_at
            total_seconds = delta.total_seconds()
            uptime = str(timedelta(seconds=total_seconds))[:-3]
        else:
            uptime = "00:00:00"
        self._tasks[rec.task_id] = TaskReport(
            id=rec.task_id,
            price=rec.price,
            upTime=uptime,
            status=rec.status,
        )


message_observer = MessageObserver()
