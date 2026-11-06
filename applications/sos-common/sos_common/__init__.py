"""Shared backend and UI helpers for the SOS OS applications.

Modules without a ``qt`` in their name are pure Python (no PyQt import) so
they can be unit-tested anywhere.
"""
from pathlib import Path

_VERSION_FILE = Path(__file__).with_name("VERSION")


def sos_version() -> str:
    """Return the SOS OS version this code was packaged with."""
    for candidate in (_VERSION_FILE, Path(__file__).resolve().parents[3] / "VERSION"):
        try:
            return candidate.read_text().strip()
        except OSError:
            continue
    return "0.0.0-dev"


__all__ = ["sos_version"]
