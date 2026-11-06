"""Power profiles (power-profiles-daemon) and SOS Gaming Mode."""
from __future__ import annotations

import json
import os
from pathlib import Path

from .proc import have, run

STATE_FILE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "sos-os" / "gaming-mode.json"


def profiles() -> list[str]:
    r = run(["powerprofilesctl", "list"])
    out = []
    for line in r.out.splitlines():
        s = line.strip().lstrip("* ").rstrip(":")
        if s in ("performance", "balanced", "power-saver"):
            out.append(s)
    return out


def current_profile() -> str | None:
    r = run(["powerprofilesctl", "get"])
    return r.out.strip() or None if r.ok else None


def set_profile(name: str) -> bool:
    if name not in ("performance", "balanced", "power-saver"):
        raise ValueError(name)
    return run(["powerprofilesctl", "set", name]).ok


def gaming_mode_active() -> bool:
    return STATE_FILE.exists()


def enable_gaming_mode() -> list[str]:
    """Switch to the performance profile and silence notifications.
    Returns human-readable notes about what was (not) possible."""
    notes = []
    previous = current_profile()
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({"previous_profile": previous}))
    if "performance" in profiles():
        notes.append("Power profile: performance" if set_profile("performance") else "Could not set performance profile")
    else:
        notes.append("This hardware has no 'performance' power profile")
    r = run(["dbus-send", "--session", "--dest=org.freedesktop.Notifications", "--type=method_call",
             "/org/freedesktop/Notifications", "org.freedesktop.DBus.Properties.Set",
             "string:org.freedesktop.Notifications", "string:Inhibited", "variant:boolean:true"])
    notes.append("Notifications: do-not-disturb" if r.ok else "Do-not-disturb not available")
    if have("gamemoderun"):
        notes.append("GameMode installed: use `gamemoderun %command%` in Steam launch options")
    else:
        notes.append("Tip: install the Gaming tool set for GameMode and MangoHud")
    return notes


def disable_gaming_mode() -> None:
    previous = None
    try:
        previous = json.loads(STATE_FILE.read_text()).get("previous_profile")
    except (OSError, ValueError):
        pass
    if previous in ("balanced", "power-saver", "performance"):
        set_profile(previous)
    run(["dbus-send", "--session", "--dest=org.freedesktop.Notifications", "--type=method_call",
         "/org/freedesktop/Notifications", "org.freedesktop.DBus.Properties.Set",
         "string:org.freedesktop.Notifications", "string:Inhibited", "variant:boolean:false"])
    STATE_FILE.unlink(missing_ok=True)
