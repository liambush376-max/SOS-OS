"""Backend of /usr/bin/sos-quickstats (panel widget data source)."""
from __future__ import annotations

import json

import psutil

from .system import hottest_cpu_temperature, temperatures


def snapshot() -> dict:
    cpu = psutil.cpu_percent(interval=0.25)
    ram = psutil.virtual_memory().percent
    temp = hottest_cpu_temperature(temperatures())
    return {"cpu": round(cpu, 1), "ram": round(ram, 1), "temp": None if temp is None else round(temp, 1)}


def main() -> int:
    print(json.dumps(snapshot()))
    return 0
