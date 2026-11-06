"""Apply Plasma appearance settings using KDE's own command-line tools."""
from __future__ import annotations

import re
from pathlib import Path

from .proc import Result, run

WALLPAPER_DIR = Path("/usr/share/wallpapers")
SOS_SCHEMES = {"dark": "SOSDark", "light": "BreezeLight"}
_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def color_schemes() -> list[str]:
    r = run(["plasma-apply-colorscheme", "--list-schemes"])
    names = []
    for line in r.out.splitlines():
        line = line.strip()
        if line.startswith("*"):
            line = line.lstrip("* ").split(" (")[0]
            names.append(line)
    return names


def apply_color_scheme(name: str) -> Result:
    return run(["plasma-apply-colorscheme", name])


def apply_accent(hex_color: str) -> Result:
    if not _HEX_RE.match(hex_color):
        raise ValueError(f"not a #RRGGBB colour: {hex_color!r}")
    return run(["plasma-apply-colorscheme", "--accent-color", hex_color])


def apply_look_and_feel(package: str = "org.sosos.desktop", reset_layout: bool = False) -> Result:
    argv = ["plasma-apply-lookandfeel", "-a", package]
    if reset_layout:
        argv.append("--resetLayout")
    return run(argv, timeout=60)


def wallpapers() -> list[Path]:
    if not WALLPAPER_DIR.is_dir():
        return []
    return sorted(p for p in WALLPAPER_DIR.iterdir() if (p / "contents" / "images").is_dir())


def apply_wallpaper(path: Path) -> Result:
    return run(["plasma-apply-wallpaperimage", str(path)])


def set_animation_speed(factor: float) -> Result:
    """factor: 0 = instant, 1 = default, larger = slower."""
    factor = max(0.0, min(4.0, factor))
    r = run(["kwriteconfig6", "--file", "kdeglobals", "--group", "KDE",
             "--key", "AnimationDurationFactor", f"{factor:.2f}"])
    if r.ok:
        run(["dbus-send", "--session", "--type=signal", "/KGlobalSettings",
             "org.kde.KGlobalSettings.notifyChange", "int32:3", "int32:0"])
        run(["dbus-send", "--session", "--dest=org.kde.KWin", "/KWin", "org.kde.KWin.reconfigure"])
    return r


def read_kde_config(file: str, group: str, key: str, default: str = "") -> str:
    r = run(["kreadconfig6", "--file", file, "--group", group, "--key", key, "--default", default])
    return r.out.strip() if r.ok else default
