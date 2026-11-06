"""Every SOS application starts, builds its main window and exits cleanly.

Runs headless with QT_QPA_PLATFORM=offscreen. Skipped when PyQt6 is missing.
"""
import os
import subprocess
import sys

import pytest
from conftest import REPO

pytest.importorskip("PyQt6.QtWidgets")

APPS = ["sos_settings", "sos_monitor", "sos_updater", "sos_welcome", "sos_devhub"]


@pytest.mark.parametrize("module", APPS)
def test_app_self_test(module, tmp_path):
    env = dict(os.environ)
    env.update({
        "QT_QPA_PLATFORM": "offscreen",
        "SOS_NO_NETWORK": "1",
        "PYTHONPATH": os.pathsep.join(str(p) for p in sorted((REPO / "applications").iterdir()) if p.is_dir()),
        "HOME": str(tmp_path),
        "XDG_CONFIG_HOME": str(tmp_path / ".config"),
        "XDG_STATE_HOME": str(tmp_path / ".state"),
        "XDG_RUNTIME_DIR": str(tmp_path),
    })
    p = subprocess.run([sys.executable, "-m", module, "--self-test"], env=env, capture_output=True,
                       text=True, timeout=120)
    assert p.returncode == 0, p.stdout + p.stderr
    assert "SELFTEST-OK" in p.stdout, p.stdout + p.stderr
    assert "Traceback" not in p.stderr, p.stderr
