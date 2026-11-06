"""Rate computation for counters (disk and network bytes per second)."""
from __future__ import annotations

import time
from dataclasses import dataclass

import psutil

from sos_common import gpu, system


@dataclass
class Sample:
    cpu_total: float
    cpu_per_core: list[float]
    cpu_freq_mhz: float | None
    ram_used: int
    ram_total: int
    swap_used: int
    swap_total: int
    disk_read_bps: float
    disk_write_bps: float
    net_rx_bps: float
    net_tx_bps: float
    temps: dict[str, float]
    gpus: list[gpu.GpuSample]
    load: tuple[float, float, float]


class Sampler:
    def __init__(self) -> None:
        self._last_t = time.monotonic()
        self._last_disk = psutil.disk_io_counters()
        self._last_net = psutil.net_io_counters()
        psutil.cpu_percent(percpu=True)  # prime the counters

    @staticmethod
    def rate(prev: float, cur: float, dt: float) -> float:
        """Bytes per second; tolerates counter resets (returns 0)."""
        if dt <= 0 or cur < prev:
            return 0.0
        return (cur - prev) / dt

    def sample(self) -> Sample:
        now = time.monotonic()
        dt = now - self._last_t
        self._last_t = now
        per_core = psutil.cpu_percent(percpu=True)
        total = sum(per_core) / len(per_core) if per_core else 0.0
        vm = psutil.virtual_memory()
        sw = psutil.swap_memory()
        disk = psutil.disk_io_counters()
        net = psutil.net_io_counters()
        d_r = d_w = n_rx = n_tx = 0.0
        if disk and self._last_disk:
            d_r = self.rate(self._last_disk.read_bytes, disk.read_bytes, dt)
            d_w = self.rate(self._last_disk.write_bytes, disk.write_bytes, dt)
        if net and self._last_net:
            n_rx = self.rate(self._last_net.bytes_recv, net.bytes_recv, dt)
            n_tx = self.rate(self._last_net.bytes_sent, net.bytes_sent, dt)
        self._last_disk, self._last_net = disk, net
        try:
            freq = psutil.cpu_freq()
            freq_mhz = freq.current if freq else None
        except (OSError, NotImplementedError):
            freq_mhz = None
        try:
            load = psutil.getloadavg()
        except OSError:
            load = (0.0, 0.0, 0.0)
        return Sample(
            cpu_total=total, cpu_per_core=per_core, cpu_freq_mhz=freq_mhz,
            ram_used=vm.total - vm.available, ram_total=vm.total,
            swap_used=sw.used, swap_total=sw.total,
            disk_read_bps=d_r, disk_write_bps=d_w, net_rx_bps=n_rx, net_tx_bps=n_tx,
            temps=system.temperatures(), gpus=gpu.sample(), load=load,
        )
