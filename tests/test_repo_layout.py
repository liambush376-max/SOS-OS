"""The repository has the structure the build scripts and docs rely on."""
import re

import pytest
from conftest import REPO

REQUIRED = [
    "LICENSE", "README.md", "CONTRIBUTING.md", "CHANGELOG.md", "SECURITY.md", "VERSION",
    ".github/workflows/build-iso.yml", ".github/workflows/test.yml",
    ".github/workflows/release.yml", ".github/workflows/lint.yml",
    ".github/pull_request_template.md", ".github/ISSUE_TEMPLATE/bug_report.yml",
    "iso/auto/config", "iso/auto/build", "iso/auto/clean",
    "scripts/build-iso.sh", "scripts/build-packages.sh", "scripts/build-in-container.sh",
    "scripts/validate-iso.sh", "scripts/qemu-boot-test.sh",
    "packages/sos-os-core/DEBIAN/control",
    "branding/logos/sos-logo.svg", "branding/wallpapers/sos-aurora.svg",
    "desktop/themes/color-schemes/SOSDark.colors",
    "desktop/themes/look-and-feel/org.sosos.desktop/metadata.json",
    "desktop/sddm/sos/Main.qml", "desktop/plymouth/sos/sos.script", "desktop/grub/sos/theme.txt",
    "installer/calamares/branding/sos/branding.desc",
    "docs/BUILDING.md", "docs/INSTALL.md", "docs/STATUS.md", "docs/TESTING.md", "docs/MAINTAINERS.md",
]

APPS = ["sos-settings", "sos-monitor", "sos-updater", "sos-welcome", "sos-devhub"]


@pytest.mark.parametrize("path", REQUIRED)
def test_required_file_exists(path):
    assert (REPO / path).is_file(), path


def test_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?", (REPO / "VERSION").read_text().strip())


def test_license_is_gpl3():
    assert "GNU GENERAL PUBLIC LICENSE" in (REPO / "LICENSE").read_text()[:200]
    assert "Version 3" in (REPO / "LICENSE").read_text()[:200]


@pytest.mark.parametrize("app", APPS)
def test_app_has_launcher_desktop_file_and_icon(app):
    d = REPO / "applications" / app
    assert (d / "bin" / app).is_file()
    assert (d / f"{app}.desktop").is_file()
    assert (d / app.replace("-", "_") / "__main__.py").is_file()
    assert (REPO / "branding" / "icons" / f"{app}.svg").is_file()


def test_no_secrets_committed():
    pattern = re.compile(
        r"-----BEGIN (RSA |OPENSSH |EC |PGP )?PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"
        r"|AKIA[0-9A-Z]{16}")
    skip = {".git", "out", "chroot", "cache", "binary", "__pycache__"}
    offenders = []
    for f in REPO.rglob("*"):
        if skip & set(f.relative_to(REPO).parts):
            continue
        if f.is_file() and f.suffix not in (".png", ".iso", ".deb") and f.name != "LICENSE":
            try:
                if pattern.search(f.read_text(errors="ignore")):
                    offenders.append(str(f.relative_to(REPO)))
            except OSError:
                pass
    assert offenders == []
