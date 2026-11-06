"""Pure functions to add archive components (contrib, non-free, ...) to APT
source definitions in both the one-line and deb822 formats. Only entries that
point at official Debian mirrors are touched."""
from __future__ import annotations

DEBIAN_HOSTS = ("deb.debian.org", "security.debian.org", "ftp.debian.org", "httpredir.debian.org")


def _is_debian_uri(uri: str) -> bool:
    return any(h in uri for h in DEBIAN_HOSTS) or ".debian.org/" in uri


def add_components_oneline(text: str, components: list[str]) -> str:
    out = []
    for line in text.splitlines():
        stripped = line.strip()
        parts = stripped.split()
        if parts and parts[0] in ("deb", "deb-src") and len(parts) >= 4:
            idx = 1
            if parts[1].startswith("["):  # options like [arch=amd64 signed-by=...]
                while idx < len(parts) and not parts[idx].endswith("]"):
                    idx += 1
                idx += 1
            if idx + 1 < len(parts) and _is_debian_uri(parts[idx]):
                comps = parts[idx + 2:]
                for c in components:
                    if c not in comps:
                        comps.append(c)
                line = " ".join(parts[:idx + 2] + comps)
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def add_components_deb822(text: str, components: list[str]) -> str:
    stanzas = text.split("\n\n")
    result = []
    for st in stanzas:
        lines = st.split("\n")
        uris = " ".join(ln.split(":", 1)[1] for ln in lines if ln.lower().startswith("uris:"))
        if _is_debian_uri(uris):
            for i, ln in enumerate(lines):
                if ln.lower().startswith("components:"):
                    comps = ln.split(":", 1)[1].split()
                    for c in components:
                        if c not in comps:
                            comps.append(c)
                    lines[i] = "Components: " + " ".join(comps)
        result.append("\n".join(lines))
    return "\n\n".join(result)
