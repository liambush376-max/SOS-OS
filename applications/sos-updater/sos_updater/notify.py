"""`sos-updater --notify`: run by the sos-update-notifier user timer.

Debian's apt-daily.timer refreshes the package lists as root; this only reads
them and shows a desktop notification. No Qt needed."""
from __future__ import annotations

from sos_common import apt
from sos_common.proc import run


def message(n: int, security: int) -> tuple[str, str]:
    title = f"{n} update{'s' if n != 1 else ''} available"
    body = "Open SOS Updater to install them."
    if security:
        body = f"{security} of them {'is a security update' if security == 1 else 'are security updates'}. " + body
    return title, body


def main() -> int:
    ups = apt.upgradable()
    if not ups:
        return 0
    title, body = message(len(ups), sum(u.is_security for u in ups))
    urgency = "critical" if any(u.is_security for u in ups) else "normal"
    run(["notify-send", "--app-name=SOS Updater", "--icon=sos-updater", f"--urgency={urgency}", title, body])
    return 0
