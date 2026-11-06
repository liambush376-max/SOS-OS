"""Checks against the root filesystem of a built ISO: layout, branding,
services, permissions and packages."""
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]

SOS_FILES = [
    "/usr/bin/sos-settings", "/usr/bin/sos-monitor", "/usr/bin/sos-updater", "/usr/bin/sos-welcome",
    "/usr/bin/sos-devhub", "/usr/bin/sos-quickstats",
    "/usr/libexec/sos-os/sos-helper", "/usr/libexec/sos-os/sos-boot-report",
    "/usr/share/polkit-1/actions/org.sosos.helper.policy",
    "/usr/share/sos-os/toolsets.json",
    "/usr/lib/sos-os/python/sos_common/__init__.py",
    "/usr/share/applications/sos-settings.desktop",
    "/etc/xdg/autostart/sos-welcome.desktop",
    "/usr/lib/systemd/user/sos-update-notifier.timer",
    "/usr/share/color-schemes/SOSDark.colors",
    "/usr/share/plasma/look-and-feel/org.sosos.desktop/metadata.json",
    "/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/layouts/org.kde.plasma.desktop-layout.js",
    "/usr/share/plasma/plasmoids/org.sosos.quickstats/contents/ui/main.qml",
    "/usr/share/wallpapers/SOS-Aurora/contents/images/3840x2160.png",
    "/usr/share/sddm/themes/sos/Main.qml", "/usr/share/sddm/themes/sos/background.png",
    "/usr/share/plymouth/themes/sos/sos.plymouth", "/usr/share/plymouth/themes/sos/logo.png",
    "/usr/share/grub/themes/sos/theme.txt",
    "/etc/calamares/branding/sos/branding.desc",
    "/usr/share/icons/hicolor/scalable/apps/sos-os.svg",
]


@pytest.mark.parametrize("path", SOS_FILES)
def test_sos_files_present(rootfs, path):
    assert rootfs.exists(path), path


def test_filesystem_layout(rootfs):
    for d in ("/usr/bin", "/usr/lib", "/etc", "/var", "/home", "/root", "/tmp", "/boot"):
        assert rootfs.exists(d), d
    # Debian 13 is merged-/usr
    for d in ("/bin", "/sbin", "/lib"):
        assert rootfs.mode(d).startswith("l") and rootfs.link(d).endswith(d.replace("/", "usr/", 1)), d


def test_os_release_branding(rootfs):
    text = rootfs.read("/usr/lib/os-release")
    assert 'NAME="SOS OS"' in text and "ID=sos-os" in text and "ID_LIKE=debian" in text
    assert "@VERSION@" not in text
    version = (REPO / "VERSION").read_text().strip()
    assert f'VERSION_ID="{version}"' in text
    assert rootfs.exists("/usr/lib/os-release.debian"), "Debian's os-release must be diverted, not lost"


def test_kernel_and_initrd(rootfs):
    assert any(p.startswith("/boot/vmlinuz-") for p in rootfs.entries)
    assert any(p.startswith("/boot/initrd.img-") for p in rootfs.entries)


@pytest.mark.parametrize("unit", ["NetworkManager.service", "ufw.service", "sos-boot-report.service"])
def test_required_system_services_enabled(rootfs, unit):
    wants = [p for p in rootfs.entries if p.startswith("/etc/systemd/system/") and ".wants/" in p and p.endswith("/" + unit)]
    assert wants, f"{unit} is not enabled"


def test_update_notifier_enabled_for_users(rootfs):
    assert rootfs.exists("/etc/systemd/user/timers.target.wants/sos-update-notifier.timer")


def test_default_target_is_graphical(rootfs):
    assert rootfs.link("/etc/systemd/system/default.target").endswith("graphical.target")


def test_display_manager_is_sddm_with_sos_theme(rootfs):
    assert "sddm" in rootfs.link("/etc/systemd/system/display-manager.service")
    assert "Current=sos" in rootfs.read("/etc/sddm.conf.d/10-sos.conf")


def test_firewall_enabled(rootfs):
    assert re.search(r"^ENABLED=yes", rootfs.read("/etc/ufw/ufw.conf"), re.M)


def test_plymouth_theme_selected(rootfs):
    assert re.search(r"^Theme=sos", rootfs.read("/etc/plymouth/plymouthd.conf"), re.M)


def test_calamares_uses_sos_branding(rootfs):
    assert re.search(r"^branding:\s*sos", rootfs.read("/etc/calamares/settings.conf"), re.M)


def test_desktop_defaults(rootfs):
    kg = rootfs.read("/etc/xdg/kdeglobals")
    assert "LookAndFeelPackage=org.sosos.desktop" in kg and "ColorScheme=SOSDark" in kg


def test_no_ssh_server(rootfs):
    assert not rootfs.exists("/usr/sbin/sshd")


def test_helper_permissions(rootfs):
    for p in ("/usr/libexec/sos-os/sos-helper", "/usr/bin/sos-settings"):
        assert rootfs.mode(p) == "-rwxr-xr-x", p
        assert rootfs.owner(p) == "root/root", p
    assert rootfs.mode("/usr/share/sos-os/toolsets.json") == "-rw-r--r--"


def test_no_world_writable_files(rootfs):
    bad = [p for p, (mode, _o, _t) in rootfs.entries.items()
           if mode[0] == "-" and mode[8] == "w"]
    assert bad == []


def test_world_writable_dirs_are_sticky(rootfs):
    bad = [p for p, (mode, _o, _t) in rootfs.entries.items()
           if mode[0] == "d" and mode[8] == "w" and mode[9] not in "tT"]
    assert bad == []


def test_sudoers_permissions(rootfs):
    for p, (mode, owner, _t) in rootfs.entries.items():
        if p.startswith("/etc/sudoers.d/") and mode[0] == "-":
            assert mode == "-r--r-----" and owner == "root/root", p


def test_no_password_hashes_baked_in(rootfs):
    for line in rootfs.read("/etc/shadow").splitlines():
        user, pw = line.split(":")[:2]
        assert not pw.startswith("$"), f"account {user} has a password hash in the image"


REQUIRED_PACKAGES = ["sos-os-core", "linux-image-amd64", "live-boot", "plasma-workspace", "sddm", "calamares",
                     "python3-pyqt6", "python3-psutil", "ufw", "firefox-esr", "network-manager", "mesa-vulkan-drivers",
                     "shim-signed", "pipewire-audio", "plymouth"]


@pytest.mark.parametrize("pkg", REQUIRED_PACKAGES)
def test_required_package_installed(packages, pkg):
    assert pkg in packages
