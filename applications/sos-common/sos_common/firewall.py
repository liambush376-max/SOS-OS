"""ufw firewall status (read without root from ufw.conf)."""
from __future__ import annotations

from pathlib import Path

UFW_CONF = Path("/etc/ufw/ufw.conf")


def parse_enabled(text: str) -> bool:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("ENABLED="):
            return line.split("=", 1)[1].strip().strip('"').lower() == "yes"
    return False


def enabled() -> bool | None:
    try:
        return parse_enabled(UFW_CONF.read_text())
    except OSError:
        return None
