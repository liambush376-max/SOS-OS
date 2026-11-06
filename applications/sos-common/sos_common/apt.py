"""Read-only APT queries (no root needed). Changes go through sos-helper."""
from __future__ import annotations

import re
from dataclasses import dataclass

from .proc import run

# e.g. "firefox-esr/stable-security 128.5.0esr-1~deb13u1 amd64 [upgradable from: 128.4.0esr-1~deb13u1]"
_UPGRADABLE_RE = re.compile(
    r"^(?P<name>[a-z0-9][a-z0-9+.\-]*)/(?P<suite>\S+)\s+(?P<new>\S+)\s+(?P<arch>\S+)"
    r"\s+\[upgradable from:\s*(?P<old>[^\]]+)\]"
)


@dataclass
class Upgrade:
    name: str
    suite: str
    new_version: str
    old_version: str
    arch: str

    @property
    def is_security(self) -> bool:
        return "security" in self.suite


def parse_upgradable(text: str) -> list[Upgrade]:
    out = []
    for line in text.splitlines():
        m = _UPGRADABLE_RE.match(line.strip())
        if m:
            out.append(Upgrade(m["name"], m["suite"], m["new"], m["old"].strip(), m["arch"]))
    return out


def upgradable() -> list[Upgrade]:
    """Packages with pending upgrades according to the current package lists.
    Lists are refreshed by Debian's apt-daily.timer or `sos-helper refresh`."""
    r = run(["apt", "list", "--upgradable"], timeout=60, env={"LC_ALL": "C.UTF-8", "PATH": "/usr/bin:/bin"})
    return parse_upgradable(r.out) if r.ok else []


def is_installed(package: str) -> bool:
    r = run(["dpkg-query", "-W", "-f=${db:Status-Status}", package])
    return r.ok and r.out.strip() == "installed"
