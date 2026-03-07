from typing import Tuple
import os, time

_prev_cpu = None


def _read_cpu_times() -> Tuple[float, float]:
    with open("/proc/stat") as f:
        line = f.readline()
    parts = line.split()
    times = [float(x) for x in parts[1:]]
    idle = times[3]
    total = sum(times)
    return idle, total


def cpu_percent() -> float:
    global _prev_cpu
    idle, total = _read_cpu_times()
    if _prev_cpu is None:
        _prev_cpu = (idle, total)
        time.sleep(0.1)
        idle, total = _read_cpu_times()

    prev_idle, prev_total = _prev_cpu
    _prev_cpu = (idle, total)
    d_total = total - prev_total
    d_idle = idle - prev_idle
    if d_total == 0:
        return 0.0
    return round((1.0 - d_idle / d_total) * 100, 2)


def disk_usage() -> float:
    st = os.statvfs("/")
    total = st.f_blocks * st.f_bsize
    free = st.f_bfree * st.f_bsize
    used = total - free
    return round(used * (1 / pow(1024, 3)), 2)


def memory_usage() -> float:
    with open("/proc/meminfo") as f:
        for line in f:
            parts = line.split()
            key = parts[0].rstrip(":")
            val_kb = float(parts[1])
            if key == "MemFree":
                return val_kb / 1024


def collect_all() -> dict:
    RAM = memory_usage()
    Disk = disk_usage()
    CPU = cpu_percent()
    return {
        "CPU": CPU,
        "RAM": RAM,
        "Disk": Disk,
    }
