"""Hardware and OS information gathered from /proc, /sys and standard tools."""
from __future__ import annotations

import os
import platform
import re
from dataclasses import dataclass, field
from pathlib import Path

import psutil

from .proc import run

SYS = Path(os.environ.get("SOS_SYSFS_ROOT", "/sys"))


def parse_os_release(text: str) -> dict[str, str]:
    data = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        data[key] = value.strip().strip('"').strip("'")
    return data


def os_release() -> dict[str, str]:
    for path in ("/etc/os-release", "/usr/lib/os-release"):
        try:
            return parse_os_release(Path(path).read_text())
        except OSError:
            continue
    return {"PRETTY_NAME": platform.platform()}


def debian_version() -> str:
    try:
        return Path("/etc/debian_version").read_text().strip()
    except OSError:
        return "unknown"


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "Unknown CPU"


@dataclass
class GpuInfo:
    slot: str
    vendor: str
    name: str
    driver: str = ""

    @property
    def vendor_key(self) -> str:
        v = self.vendor.lower()
        words = set(re.findall(r"[a-z]+", v))
        if "nvidia" in words:
            return "nvidia"
        if "intel" in words:
            return "intel"
        if words & {"amd", "ati"} or "advanced micro" in v:
            return "amd"
        if "red hat" in v or "virtio" in self.name.lower() or "vmware" in v or "innotek" in v:
            return "virtual"
        return "other"


_LSPCI_RE = re.compile(r'^(\S+) "([^"]*)" "([^"]*)" "([^"]*)"')


def parse_lspci_mm(text: str) -> list[GpuInfo]:
    """Parse `lspci -mm -k` output, returning display controllers only."""
    gpus: list[GpuInfo] = []
    current: GpuInfo | None = None
    for line in text.splitlines():
        m = _LSPCI_RE.match(line)
        if m:
            slot, cls, vendor, device = m.groups()
            current = None
            if cls.startswith(("VGA compatible controller", "3D controller", "Display controller")):
                current = GpuInfo(slot=slot, vendor=vendor, name=device)
                gpus.append(current)
        elif current is not None and line.strip().startswith("Driver:"):
            current.driver = line.split(":", 1)[1].strip()
    return gpus


def gpus() -> list[GpuInfo]:
    r = run(["lspci", "-mm", "-k"])
    return parse_lspci_mm(r.out) if r.ok else []


def is_uefi() -> bool:
    return (SYS / "firmware" / "efi").is_dir()


def secure_boot_state() -> str:
    """'enabled', 'disabled', 'not-uefi' or 'unknown'."""
    if not is_uefi():
        return "not-uefi"
    r = run(["mokutil", "--sb-state"])
    text = (r.out + r.err).lower()
    if "enabled" in text:
        return "enabled"
    if "disabled" in text:
        return "disabled"
    # Fall back to the EFI variable (last byte of SecureBoot-<guid>)
    efivars = SYS / "firmware" / "efi" / "efivars"
    try:
        for var in efivars.glob("SecureBoot-*"):
            return "enabled" if var.read_bytes()[-1:] == b"\x01" else "disabled"
    except OSError:
        pass
    return "unknown"


def virtualization() -> str:
    r = run(["systemd-detect-virt"])
    return r.out.strip() if r.out.strip() else "none"


def is_live_session() -> bool:
    try:
        return "boot=live" in Path("/proc/cmdline").read_text()
    except OSError:
        return False


@dataclass
class DiskInfo:
    device: str
    mountpoint: str
    fstype: str
    total: int
    used: int

    @property
    def percent(self) -> float:
        return 100.0 * self.used / self.total if self.total else 0.0


def disks() -> list[DiskInfo]:
    out = []
    seen = set()
    for part in psutil.disk_partitions(all=False):
        if part.device in seen or part.fstype in ("squashfs", "iso9660", "overlay"):
            continue
        seen.add(part.device)
        try:
            u = psutil.disk_usage(part.mountpoint)
        except OSError:
            continue
        out.append(DiskInfo(part.device, part.mountpoint, part.fstype, u.total, u.used))
    return out


def temperatures() -> dict[str, float]:
    """Return {label: °C} for every sensor psutil can read."""
    result: dict[str, float] = {}
    try:
        sensors = psutil.sensors_temperatures()
    except (AttributeError, OSError):
        return result
    for chip, entries in sensors.items():
        for i, e in enumerate(entries):
            if e.current is None or e.current <= 0:
                continue
            label = f"{chip} {e.label}" if e.label else (chip if len(entries) == 1 else f"{chip} #{i}")
            result[label] = float(e.current)
    return result


def hottest_cpu_temperature(temps: dict[str, float]) -> float | None:
    preferred = [v for k, v in temps.items() if k.split()[0] in ("coretemp", "k10temp", "zenpower", "cpu_thermal")]
    pool = preferred or list(temps.values())
    return max(pool) if pool else None


def human_bytes(n: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(n) < 1024 or unit == "TiB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024
    return f"{n:.1f} TiB"


@dataclass
class Summary:
    os_name: str
    sos_version: str
    debian: str
    kernel: str
    hostname: str
    cpu: str
    cores: int
    threads: int
    ram_total: int
    uefi: bool
    secure_boot: str
    virt: str
    gpus: list[GpuInfo] = field(default_factory=list)
    disks: list[DiskInfo] = field(default_factory=list)


def summary() -> Summary:
    from . import sos_version

    rel = os_release()
    return Summary(
        os_name=rel.get("PRETTY_NAME", "SOS OS"),
        sos_version=sos_version(),
        debian=debian_version(),
        kernel=platform.release(),
        hostname=platform.node(),
        cpu=cpu_model(),
        cores=psutil.cpu_count(logical=False) or 0,
        threads=psutil.cpu_count(logical=True) or 0,
        ram_total=psutil.virtual_memory().total,
        uefi=is_uefi(),
        secure_boot=secure_boot_state(),
        virt=virtualization(),
        gpus=gpus(),
        disks=disks(),
    )
