import os
import time
from typing import Optional, Tuple

from app.enums import MsgTypeEnum
from app.models import Message


class Metrics:

    _prev_cpu: Optional[Tuple[float, float]] = None

    @staticmethod
    def _read_cpu_times() -> Tuple[float, float]:
        with open("/proc/stat") as f:
            line = f.readline()
        parts = line.split()
        times = [float(x) for x in parts[1:]]
        idle = times[3]
        total = sum(times)
        return idle, total

    @staticmethod
    def _cpu_percent() -> float:
        idle, total = Metrics._read_cpu_times()
        if Metrics._prev_cpu is None:
            Metrics._prev_cpu = (idle, total)
            time.sleep(0.1)
            idle, total = Metrics._read_cpu_times()

        prev_idle, prev_total = Metrics._prev_cpu
        Metrics._prev_cpu = (idle, total)
        d_total = total - prev_total
        d_idle = idle - prev_idle
        if d_total == 0:
            return 0.0
        return round((1.0 - d_idle / d_total) * 100, 2)

    @staticmethod
    def _disk_usage() -> float:
        st = os.statvfs("/")
        free = st.f_bfree * st.f_bsize
        return round(free * (1 / pow(1024, 2)), 2)

    @staticmethod
    def _memory_usage() -> float:
        with open("/proc/meminfo") as f:
            for line in f:
                parts = line.split()
                key = parts[0].rstrip(":")
                val_kb = float(parts[1])
                if key == "MemFree":
                    return val_kb / 1024
            return 0.0

    @staticmethod
    def collect_metrics() -> dict:
        RAM = Metrics._memory_usage()
        Disk = Metrics._disk_usage()
        CPU = Metrics._cpu_percent()
        return {
            "CPU": CPU,
            "RAM": RAM,
            "Disk": Disk,
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
        cpu_cores * 0.4 + ram_mb * 0.25 + disk_mb * 0.1
    ) * delta_time_in_sec
