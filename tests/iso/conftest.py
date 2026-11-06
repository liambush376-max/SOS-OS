"""Fixtures for tests against a built ISO's root filesystem.

Enabled by scripts/validate-iso.sh, which sets SOS_SQUASHFS (path to the
extracted live/filesystem.squashfs) and SOS_PACKAGES (live-build package
manifest). Without them every test here is skipped.
"""
import os
import subprocess
from pathlib import Path

import pytest

SQUASHFS = os.environ.get("SOS_SQUASHFS")


def pytest_collection_modifyitems(config, items):
    if not SQUASHFS:
        skip = pytest.mark.skip(reason="SOS_SQUASHFS not set (run scripts/validate-iso.sh)")
        for item in items:
            if "tests/iso" in str(item.fspath).replace("\\", "/"):
                item.add_marker(skip)


class RootFS:
    def __init__(self, image: str, workdir: Path):
        self.image = image
        self.dir = workdir / "root"
        out = subprocess.run(["unsquashfs", "-lls", image], capture_output=True, text=True, check=True).stdout
        # "-rwxr-xr-x root/root  1234 2026-11-05 10:00 squashfs-root/usr/bin/x"
        # symlinks: "lrwxrwxrwx root/root 7 2026-11-05 10:00 squashfs-root/bin -> usr/bin"
        self.entries: dict[str, tuple[str, str, str]] = {}
        for line in out.splitlines():
            parts = line.split(None, 5)
            if len(parts) < 6 or parts[0][0] not in "-dlcbps" or not parts[5].startswith("squashfs-root"):
                continue
            path = parts[5][len("squashfs-root"):]
            target = ""
            if parts[0].startswith("l") and " -> " in path:
                path, target = path.split(" -> ", 1)
            self.entries["/" + path.lstrip("/") if path else "/"] = (parts[0], parts[1], target)

    def exists(self, path: str) -> bool:
        return path in self.entries

    def mode(self, path: str) -> str:
        return self.entries[path][0]

    def owner(self, path: str) -> str:
        return self.entries[path][1]

    def link(self, path: str) -> str:
        return self.entries[path][2]

    def read(self, path: str) -> str:
        dest = self.dir
        subprocess.run(["unsquashfs", "-f", "-no-progress", "-d", str(dest), self.image, path.lstrip("/")],
                       capture_output=True, check=True)
        return (dest / path.lstrip("/")).read_text(errors="replace")


@pytest.fixture(scope="session")
def rootfs(tmp_path_factory):
    return RootFS(SQUASHFS, tmp_path_factory.mktemp("rootfs"))


@pytest.fixture(scope="session")
def packages():
    path = os.environ.get("SOS_PACKAGES", "")
    if not path or not Path(path).is_file():
        pytest.skip("package manifest not available")
    return {line.split()[0].split(":")[0] for line in Path(path).read_text().splitlines() if line.strip()}
