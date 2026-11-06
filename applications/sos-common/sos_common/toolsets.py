"""Optional tool sets (gaming, developer, NVIDIA) installable from SOS Welcome
and the Control Center. The definitions live in a root-owned JSON file so the
privileged helper never installs anything a user process made up."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_PATH = Path("/usr/share/sos-os/toolsets.json")
PACKAGE_RE = re.compile(r"^[a-z0-9][a-z0-9+.\-]+(:i386)?$")
ID_RE = re.compile(r"^[a-z][a-z0-9-]{1,31}$")
ALLOWED_COMPONENTS = {"main", "contrib", "non-free", "non-free-firmware"}


@dataclass
class Toolset:
    id: str
    name: str
    description: str
    packages: list[str]
    components: list[str] = field(default_factory=list)
    multiarch_i386: bool = False
    warning: str = ""
    recommended_for: list[str] = field(default_factory=list)


def _repo_default() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "toolsets.json"


def toolsets_path() -> Path:
    env = os.environ.get("SOS_TOOLSETS")
    euid = os.geteuid() if hasattr(os, "geteuid") else -1
    if env and euid != 0:  # never honour overrides when running as root
        return Path(env)
    return DEFAULT_PATH if DEFAULT_PATH.exists() else _repo_default()


def validate(raw: dict) -> list[Toolset]:
    sets = []
    for item in raw.get("toolsets", []):
        ts = Toolset(
            id=item["id"], name=item["name"], description=item["description"],
            packages=list(item["packages"]), components=list(item.get("components", [])),
            multiarch_i386=bool(item.get("multiarch_i386", False)), warning=item.get("warning", ""),
            recommended_for=list(item.get("recommended_for", [])),
        )
        if not ID_RE.match(ts.id):
            raise ValueError(f"invalid toolset id {ts.id!r}")
        bad = [p for p in ts.packages if not PACKAGE_RE.match(p)]
        if bad:
            raise ValueError(f"toolset {ts.id}: invalid package names {bad}")
        if any(p.endswith(":i386") for p in ts.packages) and not ts.multiarch_i386:
            raise ValueError(f"toolset {ts.id}: i386 packages require multiarch_i386")
        if not set(ts.components) <= ALLOWED_COMPONENTS:
            raise ValueError(f"toolset {ts.id}: unknown components {ts.components}")
        sets.append(ts)
    ids = [t.id for t in sets]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate toolset ids")
    return sets


def load(path: Path | None = None) -> list[Toolset]:
    return validate(json.loads((path or toolsets_path()).read_text()))


def by_id(toolset_id: str, path: Path | None = None) -> Toolset:
    for ts in load(path):
        if ts.id == toolset_id:
            return ts
    raise KeyError(toolset_id)
