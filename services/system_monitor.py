from __future__ import annotations

import platform
import time
from dataclasses import dataclass

import psutil


@dataclass
class SystemStats:
    cpu_percent: float
    cpu_freq_ghz: float
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    net_recv_kbps: float
    net_sent_kbps: float


class SystemMonitor:
    def __init__(self) -> None:
        self._last_net_time = time.time()
        self._last_recv = 0
        self._last_sent = 0

        counters = psutil.net_io_counters()
        if counters:
            self._last_recv = counters.bytes_recv
            self._last_sent = counters.bytes_sent

        psutil.cpu_percent(interval=None)

    def get_stats(self) -> SystemStats:
        cpu_percent = psutil.cpu_percent(interval=None)

        freq = psutil.cpu_freq()
        cpu_freq_ghz = (freq.current / 1000.0) if freq else 0.0

        vm = psutil.virtual_memory()
        memory_used_gb = vm.used / (1024 ** 3)
        memory_total_gb = vm.total / (1024 ** 3)

        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        du = psutil.disk_usage(disk_path)
        disk_used_gb = du.used / (1024 ** 3)
        disk_total_gb = du.total / (1024 ** 3)

        recv_kbps, sent_kbps = self._get_network_speed()

        return SystemStats(
            cpu_percent=cpu_percent,
            cpu_freq_ghz=cpu_freq_ghz,
            memory_percent=vm.percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=du.percent,
            disk_used_gb=disk_used_gb,
            disk_total_gb=disk_total_gb,
            net_recv_kbps=recv_kbps,
            net_sent_kbps=sent_kbps,
        )

    def _get_network_speed(self) -> tuple[float, float]:
        now = time.time()
        elapsed = max(now - self._last_net_time, 0.001)

        counters = psutil.net_io_counters()
        if not counters:
            return 0.0, 0.0

        recv_delta = max(counters.bytes_recv - self._last_recv, 0)
        sent_delta = max(counters.bytes_sent - self._last_sent, 0)

        self._last_recv = counters.bytes_recv
        self._last_sent = counters.bytes_sent
        self._last_net_time = now

        recv_kbps = (recv_delta / 1024.0) / elapsed
        sent_kbps = (sent_delta / 1024.0) / elapsed
        return recv_kbps, sent_kbps