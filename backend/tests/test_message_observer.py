from datetime import datetime, timedelta, timezone

from app.models import TaskRecord, TaskStatusEnum


def test_update_metrics_adds_timestamp(observer):
    observer.update_metrics({"CPU": 12.5, "RAM": 1024})

    metrics = observer.latest_metrics
    assert metrics["CPU"] == 12.5
    assert metrics["RAM"] == 1024
    assert "updated_at" in metrics
    assert metrics is not observer._latest_metrics


def test_update_task_without_started_at_uses_zero_uptime(observer):
    observer.update_task(
        TaskRecord(task_id="t1", price=1.5, status=TaskStatusEnum.RECEIVED)
    )

    reports = observer.latest_tasks
    assert len(reports) == 1
    assert reports[0].id == "t1"
    assert reports[0].upTime == "00:00:00"
    assert reports[0].price == 1.5
    assert reports is not observer.latest_tasks or len(reports) == 1


def test_update_task_computes_uptime_from_started_and_ended(observer):
    started = datetime(2026, 1, 1, tzinfo=timezone.utc)
    ended = started + timedelta(seconds=3661)

    observer.update_task(
        TaskRecord(
            task_id="t2",
            price=3.0,
            status=TaskStatusEnum.FINISHED,
            started_at=started,
            ended_at=ended,
        )
    )

    report = observer.latest_tasks[0]
    assert report.upTime == "1:01"
    assert report.status == TaskStatusEnum.FINISHED


def test_update_task_uses_now_when_ended_at_missing(observer):
    started = datetime.now(timezone.utc) - timedelta(seconds=5)

    observer.update_task(
        TaskRecord(
            task_id="t3",
            price=0.0,
            status=TaskStatusEnum.EXECUTING,
            started_at=started,
        )
    )

    assert observer.latest_tasks[0].upTime != "00:00:00"
