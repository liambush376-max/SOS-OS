"""SOS Updater: signed Debian package updates through the polkit helper,
plus SOS release checks."""
from __future__ import annotations

import os
import platform
import sys

from PyQt6.QtCore import QThread, QUrl, pyqtSignal
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout, QMainWindow, QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

from sos_common import apt, releases, sos_version, system
from sos_common.qt_widgets import Card, HelperRunner, LogView, explain_helper_exit, label


class ReleaseCheck(QThread):
    result = pyqtSignal(object, str)

    def run(self) -> None:
        try:
            self.result.emit(releases.latest(include_prerelease=True), "")
        except Exception as exc:  # network errors, rate limits, JSON errors
            self.result.emit(None, str(exc))


class UpdaterWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SOS Updater")
        self.resize(900, 700)
        self.helper = HelperRunner(self)
        self.helper.output.connect(lambda t: self.log.append_text(t))
        self.helper.done.connect(self.on_helper_done)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(label("Software updates", "Title"))

        rel = system.os_release()
        info = Card("This system")
        info.body.addWidget(label(
            f"{rel.get('PRETTY_NAME', 'SOS OS')} · SOS {sos_version()} · Debian {system.debian_version()} · "
            f"kernel {platform.release()}", "Dim", wrap=True))
        self.release_label = label("Checking for new SOS OS releases…", "Dim", wrap=True)
        info.body.addWidget(self.release_label)
        self.release_button = QPushButton("View release notes")
        self.release_button.hide()
        info.body.addWidget(self.release_button)
        lay.addWidget(info)

        pkgs = Card("Package updates")
        self.status = label("", "Dim", wrap=True)
        pkgs.body.addWidget(self.status)
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Package", "Installed", "New version", "Source"])
        self.tree.setRootIsDecorated(False)
        self.tree.setMinimumHeight(220)
        pkgs.body.addWidget(self.tree, 1)
        row = QHBoxLayout()
        self.check_btn = QPushButton("Check for updates")
        self.install_btn = QPushButton("Install updates")
        self.install_btn.setObjectName("Primary")
        self.install_btn.setEnabled(False)
        row.addWidget(self.check_btn)
        row.addStretch(1)
        row.addWidget(self.install_btn)
        pkgs.body.addLayout(row)
        lay.addWidget(pkgs, 1)

        self.log = LogView()
        self.log.setMaximumHeight(200)
        lay.addWidget(self.log)
        self.setCentralWidget(central)

        self.check_btn.clicked.connect(self.check)
        self.install_btn.clicked.connect(self.install)
        self._pending_action = ""
        self.load_list()

        self.rel_thread = ReleaseCheck(self)
        self.rel_thread.result.connect(self.on_release)
        if os.environ.get("SOS_NO_NETWORK"):
            self.release_label.setText("Release check skipped (offline mode).")
        else:
            self.rel_thread.start()
            # The HTTP request times out after 10 s; never destroy a running thread.
            QApplication.instance().aboutToQuit.connect(lambda: self.rel_thread.wait(12000))

    # --- package updates -------------------------------------------------
    def load_list(self) -> None:
        ups = apt.upgradable()
        self.tree.clear()
        for u in ups:
            item = QTreeWidgetItem([u.name, u.old_version, u.new_version, u.suite])
            if u.is_security:
                item.setToolTip(0, "Security update")
                item.setText(3, u.suite + "  (security)")
            self.tree.addTopLevelItem(item)
        for c in range(4):
            self.tree.resizeColumnToContents(c)
        sec = sum(u.is_security for u in ups)
        if ups:
            self.status.setText(f"{len(ups)} update(s) available, {sec} security. "
                                "All packages are verified against Debian's signing keys by APT.")
        else:
            self.status.setText("Your system is up to date (according to the last package list refresh).")
        self.install_btn.setEnabled(bool(ups))

    def busy(self, on: bool) -> None:
        self.check_btn.setEnabled(not on)
        self.install_btn.setEnabled(not on and self.tree.topLevelItemCount() > 0)

    def check(self) -> None:
        self._pending_action = "refresh"
        self.busy(True)
        self.helper.start_helper("refresh")

    def install(self) -> None:
        self._pending_action = "upgrade"
        self.busy(True)
        self.helper.start_helper("upgrade")

    def on_helper_done(self, code: int) -> None:
        self.log.append_text(f"\n{explain_helper_exit(code)}\n")
        self.busy(False)
        self.load_list()

    # --- SOS releases ----------------------------------------------------
    def on_release(self, rel, error: str) -> None:
        if error:
            self.release_label.setText(f"Could not check for SOS OS releases ({error}).")
            return
        if rel is None:
            self.release_label.setText("No SOS OS releases have been published yet.")
            return
        current = sos_version()
        try:
            newer = releases.is_newer(rel.tag, current)
        except ValueError:
            newer = False
        if newer:
            kind = "pre-release" if rel.prerelease else "release"
            self.release_label.setText(
                f"SOS OS {rel.tag} ({kind}) is available. In-place release upgrades aren't automated yet: "
                "read the release notes for upgrade steps.")
            self.release_button.show()
            self.release_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(rel.url)))
        else:
            self.release_label.setText(f"You are running the latest SOS OS release ({current}).")


def main() -> int:
    if "--notify" in sys.argv:
        from .notify import main as notify_main
        return notify_main()
    from sos_common.qt_app import base_parser, make_app, run_window

    parser = base_parser("SOS Updater")
    parser.add_argument("--notify", action="store_true", help="show a notification if updates are pending")
    args = parser.parse_args()
    app = make_app("sos-updater", "SOS Updater", "sos-updater")
    return run_window(app, UpdaterWindow, args.self_test)


if __name__ == "__main__":
    sys.exit(main())
