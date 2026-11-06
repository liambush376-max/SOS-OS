"""live-build configuration sanity: package lists, hooks, boot options."""
import re

from conftest import REPO

ISO = REPO / "iso"


def package_lists():
    pkgs = {}
    for f in sorted((ISO / "config" / "package-lists").glob("*.list.chroot")):
        for line in f.read_text().splitlines():
            line = line.split("#", 1)[0].strip()
            if line:
                pkgs.setdefault(line, []).append(f.name)
    return pkgs


def test_package_names_are_valid():
    for name in package_lists():
        assert re.fullmatch(r"[a-z0-9][a-z0-9+.\-]+", name), name


def test_no_duplicate_packages():
    dups = {k: v for k, v in package_lists().items() if len(v) > 1}
    assert dups == {}


def test_required_packages_listed():
    pkgs = package_lists()
    for p in ("live-boot", "live-config", "linux-image-amd64", "kde-plasma-desktop", "sddm", "calamares",
              "python3-pyqt6", "python3-psutil", "ufw", "plymouth", "shim-signed", "network-manager"):
        assert p in pkgs, p


def test_no_ssh_server_by_default():
    assert "openssh-server" not in package_lists()


def test_auto_config_options():
    cfg = (ISO / "auto" / "config").read_text()
    for opt in ("--distribution trixie", "--architectures amd64", "--binary-images iso-hybrid",
                "--bootloaders \"syslinux,grub-efi\"", "--security true", "--uefi-secure-boot enable",
                "live-config.username=sos", "--debian-installer none"):
        assert opt in cfg, opt
    assert "non-free-firmware" in cfg


def test_hooks_have_shebang_and_set_e():
    hooks = sorted((ISO / "config" / "hooks" / "live").glob("*.hook.chroot"))
    assert hooks
    for h in hooks:
        text = h.read_text()
        assert text.startswith("#!/bin/sh"), h.name
        assert "\nset -e" in text, h.name
        assert "\r\n" not in text, f"{h.name} has CRLF line endings"


def test_shell_scripts_use_lf():
    for f in list((REPO / "scripts").glob("*.sh")) + list((ISO / "auto").iterdir()):
        assert b"\r\n" not in f.read_bytes(), f
