"""Configuration files are syntactically valid and consistent with each other."""
import configparser
import json
import xml.etree.ElementTree as ET

import pytest
from conftest import REPO

from sos_common import toolsets
from sos_common.system import parse_os_release

ROOTFS = REPO / "desktop" / "configuration" / "rootfs"


def ini(path, strict=True):
    cp = configparser.ConfigParser(interpolation=None, strict=strict)
    cp.optionxform = str
    cp.read_string(path.read_text())
    return cp


@pytest.mark.parametrize("path", sorted((REPO / "desktop").glob("**/metadata.json")) + [REPO / "branding/wallpapers/wallpapers.json"])
def test_json_valid(path):
    json.loads(path.read_text())


def test_look_and_feel_metadata():
    meta = json.loads((REPO / "desktop/themes/look-and-feel/org.sosos.desktop/metadata.json").read_text())
    assert meta["KPlugin"]["Id"] == "org.sosos.desktop"
    assert meta["KPackageStructure"] == "Plasma/LookAndFeel"


def test_plasmoid_metadata():
    meta = json.loads((REPO / "desktop/widgets/org.sosos.quickstats/metadata.json").read_text())
    assert meta["KPlugin"]["Id"] == "org.sosos.quickstats"
    assert (REPO / "desktop/widgets/org.sosos.quickstats/contents/ui/main.qml").is_file()


def test_layout_uses_installed_widgets_and_wallpaper():
    js = (REPO / "desktop/themes/look-and-feel/org.sosos.desktop/contents/layouts/"
          "org.kde.plasma.desktop-layout.js").read_text()
    assert "org.sosos.quickstats" in js
    ids = {w["id"] for w in json.loads((REPO / "branding/wallpapers/wallpapers.json").read_text())["wallpapers"]}
    assert "SOS-Aurora" in ids and "/usr/share/wallpapers/SOS-Aurora/" in js


def test_color_scheme():
    cp = ini(REPO / "desktop/themes/color-schemes/SOSDark.colors")
    assert cp["General"]["Name"] == "SOS Dark"
    for group in ("Colors:Window", "Colors:View", "Colors:Button", "Colors:Selection"):
        for key in ("BackgroundNormal", "ForegroundNormal"):
            parts = cp[group][key].split(",")
            assert len(parts) == 3 and all(0 <= int(p) <= 255 for p in parts)


def test_kdeglobals_defaults_point_at_sos():
    cp = ini(ROOTFS / "etc/xdg/kdeglobals")
    assert cp["General"]["ColorScheme"] == "SOSDark"
    assert cp["KDE"]["LookAndFeelPackage"] == "org.sosos.desktop"


def test_sddm_theme():
    meta = ini(REPO / "desktop/sddm/sos/metadata.desktop")["SddmGreeterTheme"]
    assert meta["QtVersion"] == "6"
    assert meta["MainScript"] == "Main.qml"
    assert ini(ROOTFS / "etc/sddm.conf.d/10-sos.conf")["Theme"]["Current"] == "sos"
    qml = (REPO / "desktop/sddm/sos/Main.qml").read_text()
    assert "sddm.login(" in qml and "onLoginFailed" in qml


def test_plymouth_theme():
    cp = ini(REPO / "desktop/plymouth/sos/sos.plymouth")
    assert cp["Plymouth Theme"]["ModuleName"] == "script"
    script = (REPO / "desktop/plymouth/sos/sos.script").read_text()
    assert "SetDisplayPasswordFunction" in script, "LUKS password prompt must be supported"


def test_os_release_template():
    rel = parse_os_release((ROOTFS / "usr/lib/os-release").read_text())
    assert rel["NAME"] == "SOS OS" and rel["ID"] == "sos-os" and rel["ID_LIKE"] == "debian"
    assert rel["VERSION_CODENAME"] == "trixie"


def test_polkit_policy_matches_helper_path():
    root = ET.parse(REPO / "applications/sos-common/data/org.sosos.helper.policy").getroot()
    action = root.find("action")
    assert action.get("id") == "org.sosos.helper"
    annot = {a.get("key"): a.text for a in action.findall("annotate")}
    assert annot["org.freedesktop.policykit.exec.path"] == "/usr/libexec/sos-os/sos-helper"
    assert action.find("defaults/allow_any").text == "no"
    assert action.find("defaults/allow_active").text.startswith("auth_admin")


def test_toolsets_valid():
    sets = toolsets.load(REPO / "applications/sos-common/data/toolsets.json")
    assert {t.id for t in sets} == {"gaming", "nvidia", "developer"}
    dev = next(t for t in sets if t.id == "developer")
    for p in ("git", "gh", "gcc", "clang", "python3", "podman", "openssh-client"):
        assert p in dev.packages


DESKTOP_FILES = sorted(REPO.glob("applications/*/*.desktop")) + sorted(REPO.glob("installer/live/*.desktop"))


@pytest.mark.parametrize("path", DESKTOP_FILES, ids=lambda p: p.name)
def test_desktop_files(path):
    entry = ini(path)["Desktop Entry"]
    for key in ("Type", "Name", "Exec", "Icon"):
        assert entry.get(key), key
    exe = entry["Exec"].split()[0]
    if exe.startswith("sos-"):
        assert (REPO / "applications" / exe / "bin" / exe).is_file(), exe
        assert (REPO / "branding/icons" / f"{entry['Icon']}.svg").is_file()


def test_systemd_units_parse():
    for unit in list(REPO.glob("applications/*/systemd/*")) + list(ROOTFS.glob("usr/lib/systemd/system/*")):
        cp = ini(unit, strict=False)
        assert "Unit" in cp, unit


def test_package_control_template():
    ctl = (REPO / "packages/sos-os-core/DEBIAN/control").read_text()
    assert "Version: @VERSION@" in ctl and "Architecture: all" in ctl
    for f in ("preinst", "postinst", "postrm"):
        assert (REPO / "packages/sos-os-core/DEBIAN" / f).read_text().startswith("#!/bin/sh")


def test_calamares_branding():
    desc = (REPO / "installer/calamares/branding/sos/branding.desc").read_text()
    assert "componentName: sos" in desc
    assert 'slideshow:               "show.qml"' in desc


def test_workflows_yaml():
    yaml = pytest.importorskip("yaml")
    for wf in (REPO / ".github/workflows").glob("*.yml"):
        doc = yaml.safe_load(wf.read_text())
        assert "jobs" in doc, wf.name
        assert "permissions" in doc, f"{wf.name} must declare least-privilege permissions"
        for job in doc["jobs"].values():
            for step in job.get("steps", []):
                uses = step.get("uses", "")
                if uses and not uses.startswith("./"):
                    ref = uses.split("@", 1)[1]
                    assert len(ref) == 40, f"{wf.name}: {uses} must be pinned to a full commit SHA"
