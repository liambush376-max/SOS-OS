"""SOS OS release checks against the GitHub Releases API (read-only, no
authentication). Release *upgrades* are not automated yet: the updater only
reports a newer SOS release and links to its notes."""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

DEFAULT_API = "https://api.github.com/repos/liambush376-max/SOS-OS/releases"
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.\-]+))?$")


def parse_version(v: str) -> tuple:
    m = _SEMVER_RE.match(v.strip())
    if not m:
        raise ValueError(f"not a semantic version: {v!r}")
    major, minor, patch, pre = m.groups()
    # A release without a pre-release tag sorts after any pre-release.
    pre_key = (1,) if pre is None else (0,) + tuple(
        (0, int(p)) if p.isdigit() else (1, p) for p in pre.split("."))
    return (int(major), int(minor), int(patch), pre_key)


def is_newer(candidate: str, current: str) -> bool:
    return parse_version(candidate) > parse_version(current)


@dataclass
class Release:
    tag: str
    name: str
    url: str
    prerelease: bool


def api_url() -> str:
    try:
        for line in Path("/etc/sos-release").read_text().splitlines():
            if line.startswith("SOS_RELEASES_API="):
                return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return DEFAULT_API


def pick_latest(releases: list[dict], include_prerelease: bool) -> Release | None:
    best = None
    for r in releases:
        if r.get("draft"):
            continue
        if r.get("prerelease") and not include_prerelease:
            continue
        try:
            key = parse_version(r["tag_name"])
        except (KeyError, ValueError):
            continue
        if best is None or key > best[0]:
            best = (key, Release(r["tag_name"], r.get("name") or r["tag_name"], r.get("html_url", ""),
                                 bool(r.get("prerelease"))))
    return best[1] if best else None


def latest(include_prerelease: bool = True, timeout: float = 10.0) -> Release | None:
    req = urllib.request.Request(api_url(), headers={
        "Accept": "application/vnd.github+json", "User-Agent": "sos-updater"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 (fixed https URL)
        return pick_latest(json.loads(resp.read().decode()), include_prerelease)
