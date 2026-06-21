import psutil

from app.enums import MsgTypeEnum
from app.models import Message


class Metrics:

    @staticmethod
    def _cpu_percent() -> float:
        return round(psutil.cpu_percent(interval=0.1), 2)

    @staticmethod
    def _disk_usage() -> float:
        free_bytes = psutil.disk_usage("/").free
        return round(free_bytes / (1024 ** 2), 2)

    @staticmethod
    def _memory_usage() -> float:
        free_bytes = psutil.virtual_memory().available
        return round(free_bytes / (1024 ** 2), 2)

    @staticmethod
    def collect_metrics() -> dict:
        return {
            "CPU": Metrics._cpu_percent(),
            "RAM": Metrics._memory_usage(),
            "Disk": Metrics._disk_usage(),
        }


def metrics_report(
    cpu_percent: float, ram_percent: float, free_disk: float
) -> Message:
    return Message(
        type=MsgTypeEnum.METRICS_REPORT,
        payload={"CPU": cpu_percent, "RAM": ram_percent, "Disk": free_disk},
    )


def task_annonce_status(task_id: str, status: MsgTypeEnum) -> Message:
    payload = {}
    match status:
        case MsgTypeEnum.TASK_RECEIVED:
            payload = {"message": f"{task_id} received"}
        case MsgTypeEnum.TASK_FAILED:
            payload = {"message": f"{task_id} failed, try again"}
        case MsgTypeEnum.TASK_RUNNING:
            payload = {"message": f"{task_id} start running"}
    return Message(type=status, payload=payload)


def task_completed(task_id: str, price: float) -> Message:
    return Message(
        type=MsgTypeEnum.TASK_COMPLETED,
        payload={
            "message": f"{task_id} completed. Price: {price}",
        },
    )


def calculate_price(
    delta_time_in_sec, cpu_cores: float, disk_mb: float, ram_mb: float
):
    return (
        cpu_cores * 0.4 + ram_mb * 0.025 + disk_mb * 0.001
    ) * delta_time_in_sec
