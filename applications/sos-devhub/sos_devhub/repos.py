"""Repository URL handling and project discovery (no Qt)."""
from __future__ import annotations

import re
import shutil
from pathlib import Path

# owner/repo shorthand, https URLs and scp-style SSH URLs.
_SHORTHAND = re.compile(r"^(?P<owner>[A-Za-z0-9](?:[A-Za-z0-9-]{0,38}))/(?P<repo>[A-Za-z0-9._-]+)$")
_HTTPS = re.compile(r"^https://(?P<host>[A-Za-z0-9.-]+)(?::\d+)?/(?P<path>[A-Za-z0-9._~/-]+?)(?:\.git)?/?$")
_SSH = re.compile(r"^(?:ssh://)?git@(?P<host>[A-Za-z0-9.-]+)[:/](?P<path>[A-Za-z0-9._~/-]+?)(?:\.git)?$")

EDITORS = [("code", "VS Code"), ("codium", "VSCodium"), ("kate", "Kate"), ("kwrite", "KWrite")]


def normalise_url(text: str) -> str:
    """Return a clone URL for user input or raise ValueError.

    Credentials embedded in URLs (https://user:token@...) are rejected; sign
    in with the GitHub CLI or an SSH key instead."""
    t = text.strip()
    if "@" in t.split("://", 1)[-1].split("/", 1)[0] and t.startswith("https://"):
        raise ValueError("URLs containing credentials are not accepted. Sign in with the GitHub CLI instead.")
    m = _SHORTHAND.match(t)
    if m:
        return f"https://github.com/{m['owner']}/{m['repo'].removesuffix('.git')}.git"
    if _HTTPS.match(t) or _SSH.match(t):
        return t
    raise ValueError("Enter owner/repo, an https:// URL or a git@host:owner/repo URL.")


def repo_dir_name(url: str) -> str:
    name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
    name = name.removesuffix(".git")
    if not name or name in (".", "..") or "/" in name:
        raise ValueError(f"cannot derive a folder name from {url!r}")
    return name


def projects(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((p for p in root.iterdir() if (p / ".git").exists()), key=lambda p: p.name.lower())


def available_editors() -> list[tuple[str, str]]:
    return [(cmd, name) for cmd, name in EDITORS if shutil.which(cmd)]
