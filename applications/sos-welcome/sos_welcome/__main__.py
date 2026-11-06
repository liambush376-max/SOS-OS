"""SOS Welcome: first-boot setup (theme, hardware checks, optional tool sets)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

from sos_common import plasma, sos_version, system, toolsets
from sos_common.qt_widgets import Card, HelperRunner, LogView, explain_helper_exit, label, page

from . import checks

DONE_FILE = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "sos-welcome-done"
LOGO = "/usr/share/sos-os/branding/sos-logo.png"
STATUS_ICON = {"ok": "#38D696", "warn": "#FFB240", "info": "#8C92BA"}


class WelcomeWindow(QMainWindow):
    def __init__(self, start_page: str = "") -> None:
        super().__init__()
        self.setWindowTitle("Welcome to SOS OS")
        self.resize(900, 640)
        self.helper = HelperRunner(self)
        self.queue: list[tuple[str, ...]] = []

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(16, 16, 16, 16)
        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        nav = QHBoxLayout()
        self.back = QPushButton("Back")
        self.next = QPushButton("Next")
        self.next.setObjectName("Primary")
        self.step = label("", "Dim")
        nav.addWidget(self.back)
        nav.addStretch(1)
        nav.addWidget(self.step)
        nav.addStretch(1)
        nav.addWidget(self.next)
        outer.addLayout(nav)
        self.setCentralWidget(central)

        self.page_ids = ["welcome", "look", "hardware", "toolsets", "done"]
        for build in (self.build_welcome, self.build_look, self.build_hardware, self.build_toolsets, self.build_done):
            self.stack.addWidget(build())
        self.back.clicked.connect(lambda: self.go(self.stack.currentIndex() - 1))
        self.next.clicked.connect(self.on_next)
        self.go(self.page_ids.index(start_page) if start_page in self.page_ids else 0)

    # --- navigation ------------------------------------------------------
    def go(self, i: int) -> None:
        i = max(0, min(self.stack.count() - 1, i))
        self.stack.setCurrentIndex(i)
        self.back.setEnabled(i > 0)
        self.next.setText("Finish" if i == self.stack.count() - 1 else "Next")
        self.step.setText(f"Step {i + 1} of {self.stack.count()}")

    def on_next(self) -> None:
        if self.stack.currentIndex() == self.stack.count() - 1:
            self.finish()
        else:
            self.go(self.stack.currentIndex() + 1)

    def finish(self) -> None:
        if self.dont_show.isChecked():
            DONE_FILE.parent.mkdir(parents=True, exist_ok=True)
            DONE_FILE.write_text(f"{sos_version()}\n")
        self.close()

    # --- pages -----------------------------------------------------------
    def build_welcome(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.addStretch(1)
        logo = QLabel()
        pix = QPixmap(LOGO)
        if not pix.isNull():
            logo.setPixmap(pix.scaled(140, 140, Qt.AspectRatioMode.KeepAspectRatio,
                                      Qt.TransformationMode.SmoothTransformation))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)
        t = label("Welcome to SOS OS", "Title")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t)
        s = label(f"Version {sos_version()}. Let's set up your system: pick a look, check your hardware "
                  "and add optional gaming or developer tools.", "Subtitle", wrap=True)
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(s)
        if system.is_live_session():
            live = label("You're running the live system. Changes are lost when you restart unless you "
                         "install SOS OS using the icon on the desktop.", "Dim", wrap=True)
            live.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay.addWidget(live)
        lay.addStretch(2)
        return w

    def build_look(self) -> QWidget:
        scroll, lay = page("Choose your look", "You can change this any time in SOS Control Center.")
        row = QHBoxLayout()
        self.look_msg = label("", "Dim")
        for title, desc, scheme, wallpaper in (
            ("SOS Dark", "Deep navy with electric-blue and purple accents (default).", "SOSDark", "SOS-Aurora"),
            ("SOS Nebula", "SOS Dark with the Nebula wallpaper.", "SOSDark", "SOS-Nebula"),
            ("Light", "KDE Breeze Light with SOS accents.", "BreezeLight", "SOS-Aurora"),
        ):
            card = Card(title)
            card.body.addWidget(label(desc, "Dim", wrap=True))
            b = QPushButton("Use this")
            b.clicked.connect(lambda _=False, s=scheme, wp=wallpaper, t=title: self.apply_look(s, wp, t))
            card.body.addWidget(b)
            row.addWidget(card)
        lay.addLayout(row)
        lay.addWidget(self.look_msg)
        lay.addStretch(1)
        return scroll

    def apply_look(self, scheme: str, wallpaper: str, title: str) -> None:
        r = plasma.apply_color_scheme(scheme)
        wp = plasma.WALLPAPER_DIR / wallpaper
        if wp.is_dir():
            plasma.apply_wallpaper(wp)
        self.look_msg.setText(f"Applied {title}." if r.ok else f"Could not apply theme: {r.err.strip()}")

    def build_hardware(self) -> QWidget:
        scroll, lay = page("Hardware check", "What SOS OS found on this computer.")
        card = Card()
        for status, title, detail in checks.run_all():
            card.body.addWidget(label(
                f'<span style="color:{STATUS_ICON[status]}">●</span> <b>{title}</b>: {detail}', wrap=True))
        lay.addWidget(card)
        lay.addStretch(1)
        return scroll

    def build_toolsets(self) -> QWidget:
        scroll, lay = page("Optional tools", "Installed from the signed Debian archive. You'll be asked "
                                             "for your password. Internet access required.")
        self.toolset_boxes: dict[str, QCheckBox] = {}
        try:
            sets = toolsets.load()
        except (OSError, ValueError) as exc:
            sets = []
            lay.addWidget(label(f"Tool sets unavailable: {exc}", wrap=True))
        vendors = {g.vendor_key for g in system.gpus()}
        for ts in sets:
            card = Card(ts.name)
            card.body.addWidget(label(ts.description, "Dim", wrap=True))
            if ts.warning:
                card.body.addWidget(label(f"⚠ {ts.warning}", wrap=True))
            box = QCheckBox(f"Install {ts.name}")
            if ts.recommended_for and not (vendors & set(ts.recommended_for)):
                box.setText(box.text() + " (not recommended for your hardware)")
            card.body.addWidget(box)
            self.toolset_boxes[ts.id] = box
            if any(p == "steam-installer" for p in ts.packages):
                self.steam_license = QCheckBox("I accept the Steam Subscriber Agreement "
                                               "(https://store.steampowered.com/subscriber_agreement/)")
                self.steam_license.setEnabled(False)
                box.toggled.connect(self.steam_license.setEnabled)
                card.body.addWidget(self.steam_license)
            lay.addWidget(card)
        self.install_btn = QPushButton("Install selected")
        self.install_btn.setObjectName("Primary")
        self.install_btn.clicked.connect(self.install_selected)
        lay.addWidget(self.install_btn)
        self.log = LogView()
        self.helper.output.connect(self.log.append_text)
        self.helper.done.connect(self.on_helper_done)
        lay.addWidget(self.log)
        return scroll

    def install_selected(self) -> None:
        self.queue = []
        for ts_id, box in self.toolset_boxes.items():
            if not box.isChecked():
                continue
            args: tuple[str, ...] = ("install-toolset", ts_id)
            if ts_id == "gaming":
                if not self.steam_license.isChecked():
                    self.log.append_text("Steam needs the licence checkbox ticked; skipping the Gaming tool set.\n")
                    continue
                args += ("--accept-steam-license",)
            self.queue.append(args)
        if not self.queue:
            self.log.append_text("Nothing selected.\n")
            return
        self.install_btn.setEnabled(False)
        self.helper.start_helper(*self.queue.pop(0))

    def on_helper_done(self, code: int) -> None:
        self.log.append_text(f"\n{explain_helper_exit(code)}\n")
        if code == 0 and self.queue:
            self.helper.start_helper(*self.queue.pop(0))
        else:
            self.queue = []
            self.install_btn.setEnabled(True)

    def build_done(self) -> QWidget:
        scroll, lay = page("You're all set", "A few places to go next:")
        for app, text in (
            ("SOS Control Center", "appearance, Gaming Mode, firewall and hardware info"),
            ("SOS System Monitor", "live CPU, GPU, memory and temperatures"),
            ("SOS Updater", "keep the system patched; it also notifies you automatically"),
            ("SOS DevHub", "clone GitHub repositories and open projects"),
        ):
            lay.addWidget(label(f"<b>{app}</b>: {text}", wrap=True))
        self.dont_show = QCheckBox("Don't show this window at startup again")
        self.dont_show.setChecked(True)
        lay.addWidget(self.dont_show)
        lay.addStretch(1)
        return scroll


def main() -> int:
    from sos_common.qt_app import base_parser, make_app, run_window

    parser = base_parser("SOS Welcome")
    parser.add_argument("--autostart", action="store_true", help="exit unless this is the first login")
    parser.add_argument("--page", default="", help="open a specific page (welcome, look, hardware, toolsets, done)")
    args = parser.parse_args()
    if args.autostart and (DONE_FILE.exists() or system.is_live_session()):
        return 0
    app = make_app("sos-welcome", "SOS Welcome", "sos-welcome")
    return run_window(app, lambda: WelcomeWindow(args.page), args.self_test)


if __name__ == "__main__":
    sys.exit(main())
