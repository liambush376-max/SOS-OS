"""GPU utilisation and temperature readers.

* AMD (amdgpu): /sys/class/drm/cardN/device/gpu_busy_percent + hwmon
* Intel (i915/xe): no unprivileged utilisation counter exists; we report the
  current/max frequency ratio and label it as such.
* NVIDIA (proprietary driver): nvidia-smi.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .proc import have, run
from .system import SYS


@dataclass
class GpuSample:
    name: str
    vendor: str
    busy_percent: float | None  # None = not available
    metric: str  # what busy_percent means: "utilisation" or "frequency"
    temp_c: float | None = None
    vram_used: int | None = None  # bytes
    vram_total: int | None = None


def _read_float(path: Path) -> float | None:
    try:
        return float(path.read_text().strip())
    except (OSError, ValueError):
        return None


def _hwmon_temp(device: Path) -> float | None:
    for hw in sorted((device / "hwmon").glob("hwmon*")):
        t = _read_float(hw / "temp1_input")
        if t is not None:
            return t / 1000.0
    return None


def parse_nvidia_smi(text: str) -> list[GpuSample]:
    """Parse `nvidia-smi --query-gpu=name,utilization.gpu,temperature.gpu,
    memory.used,memory.total --format=csv,noheader,nounits`."""
    samples = []
    for line in text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            continue

        def num(s: str) -> float | None:
            try:
                return float(s)
            except ValueError:
                return None

        used, total = num(parts[3]), num(parts[4])
        samples.append(GpuSample(
            name=parts[0], vendor="nvidia", busy_percent=num(parts[1]), metric="utilisation",
            temp_c=num(parts[2]),
            vram_used=int(used * 1024 * 1024) if used is not None else None,
            vram_total=int(total * 1024 * 1024) if total is not None else None,
        ))
    return samples


def _drm_cards() -> list[Path]:
    drm = SYS / "class" / "drm"
    return sorted(p for p in drm.glob("card[0-9]*") if "-" not in p.name)


def sample() -> list[GpuSample]:
    samples: list[GpuSample] = []
    for card in _drm_cards():
        dev = card / "device"
        driver = ""
        try:
            driver = (dev / "driver").resolve().name
        except OSError:
            pass
        if driver == "amdgpu":
            vram_used = _read_float(dev / "mem_info_vram_used")
            vram_total = _read_float(dev / "mem_info_vram_total")
            samples.append(GpuSample(
                name=f"AMD GPU ({card.name})", vendor="amd",
                busy_percent=_read_float(dev / "gpu_busy_percent"), metric="utilisation",
                temp_c=_hwmon_temp(dev),
                vram_used=int(vram_used) if vram_used is not None else None,
                vram_total=int(vram_total) if vram_total is not None else None,
            ))
        elif driver in ("i915", "xe"):
            cur = _read_float(card / "gt_cur_freq_mhz") or _read_float(card / "gt_act_freq_mhz")
            mx = _read_float(card / "gt_max_freq_mhz")
            busy = (100.0 * cur / mx) if (cur is not None and mx) else None
            samples.append(GpuSample(
                name=f"Intel GPU ({card.name})", vendor="intel",
                busy_percent=busy, metric="frequency", temp_c=_hwmon_temp(dev),
            ))
    if have("nvidia-smi"):
        r = run(["nvidia-smi",
                 "--query-gpu=name,utilization.gpu,temperature.gpu,memory.used,memory.total",
                 "--format=csv,noheader,nounits"], timeout=5)
        if r.ok:
            samples.extend(parse_nvidia_smi(r.out))
    return samples
