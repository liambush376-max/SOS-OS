"""The privileged helper only accepts its fixed allowlist of actions."""
import importlib.machinery
import importlib.util
import os

import pytest
from conftest import REPO

HELPER = REPO / "applications/sos-common/libexec/sos-helper"


@pytest.fixture
def helper(monkeypatch):
    loader = importlib.machinery.SourceFileLoader("sos_helper", str(HELPER))
    spec = importlib.util.spec_from_loader("sos_helper", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    calls = []
    monkeypatch.setattr(mod, "run", lambda argv: calls.append(argv) or 0)
    monkeypatch.setattr(mod, "enable_components", lambda comps: calls.append(["enable", *comps]) or False)
    monkeypatch.setattr(mod.toolsets, "DEFAULT_PATH", REPO / "applications/sos-common/data/toolsets.json")
    monkeypatch.setattr(os, "geteuid", lambda: 0, raising=False)
    monkeypatch.setattr(mod.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "i386\n"})())
    mod.calls = calls
    return mod


def test_requires_root(helper, monkeypatch):
    monkeypatch.setattr(os, "geteuid", lambda: 1000, raising=False)
    assert helper.main(["refresh"]) == 1
    assert helper.calls == []


@pytest.mark.parametrize("argv", [
    ["rm", "-rf", "/"],
    ["refresh", "extra"],
    ["firewall", "reset"],
    ["install-toolset", "../../etc/passwd"],
    ["install-toolset", "gaming", "--yes"],
    ["install-toolset", "does-not-exist"],
])
def test_rejects_unknown_or_malformed(helper, argv):
    assert helper.main(argv) == 2
    assert [c for c in helper.calls if c[0] != "enable"] == []


def test_steam_requires_explicit_licence_acceptance(helper):
    assert helper.main(["install-toolset", "gaming"]) == 3
    assert helper.calls == []


def test_refresh_and_upgrade_commands(helper):
    assert helper.main(["refresh"]) == 0
    assert helper.main(["upgrade"]) == 0
    cmds = [c[c.index("apt-get") + len(helper.APT_OPTS) + 1:] for c in helper.calls]
    assert cmds == [["update"], ["update"], ["-y", "--with-new-pkgs", "upgrade"]]


def test_install_developer_toolset_uses_json_packages(helper):
    assert helper.main(["install-toolset", "developer"]) == 0
    install = helper.calls[-1]
    assert install[0] == "apt-get" and "install" in install
    assert "gh" in install and "podman" in install


def test_firewall(helper):
    assert helper.main(["firewall", "enable"]) == 0
    assert helper.calls[-1] == ["ufw", "--force", "enable"]
