"""Unit tests for the pure-Python backends (no Qt, no root, no network)."""
import json

import pytest

from sos_common import apt, firewall, gpu, network, releases, sources, system, toolsets
from sos_devhub import repos
from sos_monitor.sampler import Sampler
from sos_updater import notify
from sos_welcome import checks

LSPCI = '''00:02.0 "VGA compatible controller" "Intel Corporation" "Raptor Lake-S GT1 [UHD Graphics 770]" -r04 -p00 "ASUSTeK" "Device 8882"
\tDriver: i915
\tModule: i915
01:00.0 "VGA compatible controller" "NVIDIA Corporation" "AD104 [GeForce RTX 4070]" -ra1 -p00 "Micro-Star" "Device 5111"
\tDriver: nouveau
00:14.0 "USB controller" "Intel Corporation" "Raptor Lake USB 3.2" -r11 -p30 "ASUSTeK" "Device 8882"
\tDriver: xhci_hcd
03:00.0 "Display controller" "Advanced Micro Devices, Inc. [AMD/ATI]" "Navi 31" -rc8 "Sapphire" "Device e471"
\tDriver: amdgpu
'''


def test_parse_lspci_finds_gpus_and_drivers():
    g = system.parse_lspci_mm(LSPCI)
    assert [x.vendor_key for x in g] == ["intel", "nvidia", "amd"]
    assert [x.driver for x in g] == ["i915", "nouveau", "amdgpu"]


def test_gpu_advice_recommends_nvidia_driver():
    advice = checks.gpu_advice(system.parse_lspci_mm(LSPCI))
    nv = [a for a in advice if a[1] == "NVIDIA graphics"][0]
    assert nv[0] == "warn" and "NVIDIA proprietary driver" in nv[2]
    assert any(a[1] == "AMD graphics" and a[0] == "ok" for a in advice)


def test_memory_and_disk_checks():
    assert checks.check_memory(16 * 2**30)[0] == "ok"
    assert checks.check_memory(3 * 2**30)[0] == "warn"
    assert checks.check_disk(100 * 2**30)[0] == "ok"
    assert checks.check_disk(5 * 2**30)[0] == "warn"


def test_parse_os_release_quotes_and_comments():
    rel = system.parse_os_release('# c\nNAME="SOS OS"\nID=sos-os\nEMPTY=\nBAD LINE\n')
    assert rel == {"NAME": "SOS OS", "ID": "sos-os", "EMPTY": ""}


def test_hottest_cpu_temperature_prefers_cpu_sensors():
    assert system.hottest_cpu_temperature({"coretemp Package id 0": 55.0, "nvme Composite": 70.0}) == 55.0
    assert system.hottest_cpu_temperature({"acpitz": 40.0}) == 40.0
    assert system.hottest_cpu_temperature({}) is None


def test_human_bytes():
    assert system.human_bytes(512) == "512 B"
    assert system.human_bytes(1536) == "1.5 KiB"
    assert system.human_bytes(3 * 2**30) == "3.0 GiB"


def test_parse_upgradable():
    out = """Listing... Done
firefox-esr/stable-security 128.5.0esr-1~deb13u1 amd64 [upgradable from: 128.4.0esr-1~deb13u1]
libc6/stable 2.41-12 amd64 [upgradable from: 2.41-11]
garbage line
"""
    ups = apt.parse_upgradable(out)
    assert [u.name for u in ups] == ["firefox-esr", "libc6"]
    assert ups[0].is_security and not ups[1].is_security
    assert ups[1].old_version == "2.41-11" and ups[1].new_version == "2.41-12"


def test_notify_message():
    assert notify.message(1, 0) == ("1 update available", "Open SOS Updater to install them.")
    title, body = notify.message(5, 2)
    assert title == "5 updates available" and body.startswith("2 of them are security updates")


def test_nmcli_terse_escaping():
    assert network.split_terse(r"wlan0:wifi:connected:My\:Net") == ["wlan0", "wifi", "connected", "My:Net"]
    devs = network.parse_devices("wlan0:wifi:connected:Home\nlo:loopback:unmanaged:\n")
    assert len(devs) == 1 and devs[0].connection == "Home"


def test_parse_wifi_dedupes_and_sorts():
    nets = network.parse_wifi(" :Cafe:40:WPA2\n*:Home:70:WPA3\n :Cafe:80:WPA2\n : :10:\n")
    assert [n.ssid for n in nets] == ["Home", "Cafe"]
    assert nets[0].in_use and nets[1].signal == 80


def test_parse_nvidia_smi():
    s = gpu.parse_nvidia_smi("NVIDIA GeForce RTX 4070, 37, 52, 1024, 12282\n")
    assert s[0].busy_percent == 37 and s[0].temp_c == 52
    assert s[0].vram_used == 1024 * 2**20 and s[0].vram_total == 12282 * 2**20
    assert gpu.parse_nvidia_smi("[N/A], [N/A], [N/A], [N/A], [N/A]")[0].busy_percent is None


def test_sources_oneline_adds_components_to_debian_only():
    text = ("deb http://deb.debian.org/debian/ trixie main non-free-firmware\n"
            "deb [signed-by=/usr/share/keyrings/x.gpg] https://example.com/repo stable main\n"
            "deb http://security.debian.org/debian-security/ trixie-security main\n")
    out = sources.add_components_oneline(text, ["contrib", "non-free"])
    lines = out.splitlines()
    assert lines[0] == "deb http://deb.debian.org/debian/ trixie main non-free-firmware contrib non-free"
    assert lines[1] == "deb [signed-by=/usr/share/keyrings/x.gpg] https://example.com/repo stable main"
    assert lines[2].endswith("main contrib non-free")
    assert sources.add_components_oneline(out, ["contrib"]) == out  # idempotent


def test_sources_deb822():
    text = ("Types: deb\nURIs: http://deb.debian.org/debian\nSuites: trixie trixie-updates\n"
            "Components: main\nSigned-By: /usr/share/keyrings/debian-archive-keyring.gpg\n\n"
            "Types: deb\nURIs: https://example.org/apt\nSuites: x\nComponents: main\n")
    out = sources.add_components_deb822(text, ["contrib"])
    assert "Components: main contrib\nSigned-By" in out
    assert out.endswith("Components: main\n")


def test_semver_ordering():
    assert releases.is_newer("v0.2.0", "0.1.0")
    assert releases.is_newer("1.0.0", "1.0.0-rc.1")
    assert releases.is_newer("1.0.0-rc.2", "1.0.0-rc.1")
    assert not releases.is_newer("v0.1.0", "0.1.0")
    with pytest.raises(ValueError):
        releases.parse_version("latest")


def test_pick_latest_release():
    data = [
        {"tag_name": "v0.1.0", "prerelease": True, "draft": False, "html_url": "u1"},
        {"tag_name": "v0.3.0", "prerelease": False, "draft": True, "html_url": "draft"},
        {"tag_name": "v0.2.0", "prerelease": True, "draft": False, "html_url": "u2"},
        {"tag_name": "nightly", "prerelease": True, "draft": False},
    ]
    assert releases.pick_latest(data, include_prerelease=True).tag == "v0.2.0"
    assert releases.pick_latest(data, include_prerelease=False) is None


def test_firewall_parse():
    assert firewall.parse_enabled("# comment\nENABLED=yes\nLOGLEVEL=low\n")
    assert not firewall.parse_enabled("ENABLED=no\n")
    assert not firewall.parse_enabled("")


def test_toolset_validation_rejects_bad_input(tmp_path):
    def write(obj):
        p = tmp_path / "t.json"
        p.write_text(json.dumps(obj))
        return p

    good = {"id": "x-tools", "name": "X", "description": "d", "packages": ["git"]}
    assert toolsets.load(write({"toolsets": [good]}))[0].id == "x-tools"
    for bad in (
        {**good, "packages": ["git; rm -rf /"]},
        {**good, "id": "../etc"},
        {**good, "packages": ["wine:i386"]},  # i386 without multiarch flag
        {**good, "components": ["evil"]},
    ):
        with pytest.raises(ValueError):
            toolsets.load(write({"toolsets": [bad]}))
    with pytest.raises(ValueError):
        toolsets.load(write({"toolsets": [good, good]}))


@pytest.mark.parametrize("text,expected", [
    ("torvalds/linux", "https://github.com/torvalds/linux.git"),
    ("owner/repo.git", "https://github.com/owner/repo.git"),
    ("https://github.com/owner/repo", "https://github.com/owner/repo"),
    ("git@github.com:owner/repo.git", "git@github.com:owner/repo.git"),
    ("https://gitlab.com/group/sub/proj.git", "https://gitlab.com/group/sub/proj.git"),
])
def test_devhub_normalise_url(text, expected):
    assert repos.normalise_url(text) == expected


@pytest.mark.parametrize("text", [
    "https://user:ghp_secret@github.com/o/r.git", "file:///etc/passwd", "--upload-pack=evil", "", "a b c",
])
def test_devhub_rejects_unsafe_urls(text):
    with pytest.raises(ValueError):
        repos.normalise_url(text)


def test_devhub_dir_name_and_projects(tmp_path):
    assert repos.repo_dir_name("https://github.com/o/my-repo.git") == "my-repo"
    assert repos.repo_dir_name("git@github.com:o/thing.git") == "thing"
    (tmp_path / "b" / ".git").mkdir(parents=True)
    (tmp_path / "a" / ".git").mkdir(parents=True)
    (tmp_path / "not-a-repo").mkdir()
    assert [p.name for p in repos.projects(tmp_path)] == ["a", "b"]


def test_sampler_rate_handles_resets():
    assert Sampler.rate(100, 300, 2.0) == 100
    assert Sampler.rate(300, 100, 1.0) == 0.0  # counter reset
    assert Sampler.rate(0, 10, 0) == 0.0


def test_sampler_produces_sane_values():
    s = Sampler().sample()
    assert 0 <= s.cpu_total <= 100
    assert s.ram_total > 0 and 0 < s.ram_used <= s.ram_total
    assert s.disk_read_bps >= 0 and s.net_rx_bps >= 0
