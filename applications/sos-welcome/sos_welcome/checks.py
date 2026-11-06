"""First-boot hardware checks. Each check returns (status, title, detail)
where status is "ok", "warn" or "info"."""
from __future__ import annotations

import shutil

import psutil

from sos_common import system
from sos_common.proc import have, run

Check = tuple[str, str, str]


def check_memory(total: int) -> Check:
    gib = total / 2**30
    if gib >= 8:
        return "ok", "Memory", f"{gib:.1f} GiB, plenty for desktop use and most games."
    if gib >= 4:
        return "warn", "Memory", f"{gib:.1f} GiB. Fine for the desktop, but games and containers may need 8 GiB or more."
    return "warn", "Memory", f"{gib:.1f} GiB is below the recommended 4 GiB minimum."


def check_disk(free: int) -> Check:
    gib = free / 2**30
    if gib >= 20:
        return "ok", "Free disk space", f"{gib:.0f} GiB free."
    return "warn", "Free disk space", f"Only {gib:.0f} GiB free; tool sets and games need more."


def gpu_advice(gpus: list[system.GpuInfo]) -> list[Check]:
    if not gpus:
        return [("info", "Graphics", "No GPU detected via PCI (common in some VMs).")]
    out = []
    for g in gpus:
        key = g.vendor_key
        name = f"{g.vendor} {g.name}"
        if key == "nvidia":
            if g.driver == "nvidia":
                out.append(("ok", "NVIDIA graphics", f"{name}: proprietary driver active."))
            else:
                out.append(("warn", "NVIDIA graphics",
                            f"{name} is using '{g.driver or 'no driver'}'. For gaming, install the "
                            "'NVIDIA proprietary driver' tool set."))
        elif key in ("amd", "intel"):
            out.append(("ok", f"{key.upper() if key == 'amd' else 'Intel'} graphics",
                        f"{name}: open-source Mesa driver ({g.driver or 'loading'}) with Vulkan included."))
        elif key == "virtual":
            out.append(("info", "Virtual GPU", f"{name}: running in a virtual machine."))
        else:
            out.append(("info", "Graphics", name))
    return out


def run_all() -> list[Check]:
    checks: list[Check] = [check_memory(psutil.virtual_memory().total)]
    try:
        checks.append(check_disk(shutil.disk_usage("/").free))
    except OSError:
        pass
    if system.is_uefi():
        sb = system.secure_boot_state()
        checks.append(("ok", "Firmware", f"UEFI boot, Secure Boot {sb}."))
    else:
        checks.append(("info", "Firmware", "Legacy BIOS boot."))
    checks.extend(gpu_advice(system.gpus()))
    if have("vulkaninfo"):
        r = run(["vulkaninfo", "--summary"], timeout=20)
        checks.append(("ok", "Vulkan", "Vulkan devices available.") if r.ok and "deviceName" in r.out
                      else ("warn", "Vulkan", "No Vulkan device found."))
    temps = system.temperatures()
    checks.append(("ok", "Sensors", f"{len(temps)} temperature sensor(s) readable.") if temps
                  else ("info", "Sensors", "No temperature sensors exposed (normal in VMs)."))
    r = run(["nmcli", "networking", "connectivity"])
    conn = r.out.strip()
    checks.append(("ok", "Internet", "Connected.") if conn == "full"
                  else ("warn", "Internet", f"Connectivity: {conn or 'unknown'}. Tool sets need internet access."))
    virt = system.virtualization()
    if virt != "none":
        checks.append(("info", "Virtual machine", f"Running under {virt}."))
    return checks
