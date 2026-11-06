"""SOS Control Center: appearance, performance, hardware, network, security,
updates and personalisation."""
from __future__ import annotations

import re
import subprocess
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QColorDialog, QComboBox, QGridLayout, QHBoxLayout, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QSlider,
)

from sos_common import apt, firewall, network, plasma, power, sos_version, system, toolsets
from sos_common.proc import have, run
from sos_common.qt_app import base_parser, make_app, run_window
from sos_common.qt_widgets import (
    Card, HelperRunner, LogView, SidebarWindow, explain_helper_exit, label, page, status_dot,
)

HOSTNAME_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)$")
ACCENTS = [("Electric blue", "#2F7BFF"), ("Purple", "#9B3DFF"), ("Cyan", "#22D3EE"),
           ("Magenta", "#E040FB"), ("Emerald", "#38D696")]


def launch(*argv: str) -> None:
    if have(argv[0]):
        subprocess.Popen(list(argv), start_new_session=True)  # noqa: S603


class AppearancePage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Appearance", "Theme, accent colour and wallpaper.")
        self.feedback = label("", "Dim", wrap=True)

        theme = Card("Theme")
        row = QHBoxLayout()
        for title, scheme in (("SOS Dark", "SOSDark"), ("Breeze Light", "BreezeLight"), ("Breeze Dark", "BreezeDark")):
            b = QPushButton(title)
            b.clicked.connect(lambda _=False, s=scheme: self.result(plasma.apply_color_scheme(s), f"Colour scheme: {s}"))
            row.addWidget(b)
        theme.body.addLayout(row)
        reset = QPushButton("Restore the full SOS OS look (theme, splash, wallpaper)")
        reset.clicked.connect(lambda: self.result(plasma.apply_look_and_feel(), "SOS OS look applied"))
        theme.body.addWidget(reset)
        lay.addWidget(theme)

        accent = Card("Accent colour")
        arow = QHBoxLayout()
        for name, hexc in ACCENTS:
            b = QPushButton(name)
            b.setStyleSheet(f"QPushButton {{ border: 2px solid {hexc}; }}")
            b.clicked.connect(lambda _=False, c=hexc: self.result(plasma.apply_accent(c), f"Accent: {c}"))
            arow.addWidget(b)
        custom = QPushButton("Custom…")
        custom.clicked.connect(self.pick_accent)
        arow.addWidget(custom)
        accent.body.addLayout(arow)
        lay.addWidget(accent)

        wp = Card("Wallpaper")
        self.wp_list = QListWidget()
        self.wp_list.setMaximumHeight(160)
        self.wallpapers = plasma.wallpapers()
        for p in self.wallpapers:
            self.wp_list.addItem(p.name.replace("-", " "))
        if not self.wallpapers:
            self.wp_list.addItem("(no wallpapers found in /usr/share/wallpapers)")
        apply_wp = QPushButton("Set as wallpaper")
        apply_wp.clicked.connect(self.apply_wallpaper)
        wp.body.addWidget(self.wp_list)
        wp.body.addWidget(apply_wp)
        lay.addWidget(wp)

        anim = Card("Animation speed")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 200)
        try:
            self.slider.setValue(int(float(plasma.read_kde_config("kdeglobals", "KDE", "AnimationDurationFactor", "0.75")) * 100))
        except ValueError:
            self.slider.setValue(75)
        anim.body.addWidget(label("Left = instant, right = slow and smooth", "Dim"))
        anim.body.addWidget(self.slider)
        self.slider.sliderReleased.connect(
            lambda: self.result(plasma.set_animation_speed(self.slider.value() / 100), "Animation speed updated"))
        lay.addWidget(anim)

        lay.addWidget(self.feedback)
        lay.addStretch(1)

    def result(self, r, ok_text: str) -> None:
        self.feedback.setText(ok_text if r.ok else f"Failed: {(r.err or r.out).strip()}")

    def pick_accent(self) -> None:
        c = QColorDialog.getColor(QColor("#2F7BFF"), self.widget, "Accent colour")
        if c.isValid():
            self.result(plasma.apply_accent(c.name()), f"Accent: {c.name()}")

    def apply_wallpaper(self) -> None:
        i = self.wp_list.currentRow()
        if 0 <= i < len(self.wallpapers):
            self.result(plasma.apply_wallpaper(self.wallpapers[i]), "Wallpaper set")


class PerformancePage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Performance", "Power profiles and Gaming Mode.")
        prof = Card("Power profile")
        self.combo = QComboBox()
        self.profiles = power.profiles()
        self.combo.addItems(self.profiles or ["power-profiles-daemon not running"])
        cur = power.current_profile()
        if cur in self.profiles:
            self.combo.setCurrentIndex(self.profiles.index(cur))
        self.combo.setEnabled(bool(self.profiles))
        self.combo.activated.connect(self.set_profile)
        prof.body.addWidget(self.combo)
        lay.addWidget(prof)

        gm = Card("Gaming Mode")
        gm.body.addWidget(label(
            "Switches to the performance profile and turns on do-not-disturb. KWin already suspends "
            "compositing effects for full-screen games. For per-game tuning, launch games with GameMode "
            "(`gamemoderun %command%` in Steam).", "Dim", wrap=True))
        self.gm_button = QPushButton()
        self.gm_button.setObjectName("Primary")
        self.gm_button.clicked.connect(self.toggle_gaming)
        self.gm_notes = label("", "Dim", wrap=True)
        gm.body.addWidget(self.gm_button)
        gm.body.addWidget(self.gm_notes)
        lay.addWidget(gm)
        lay.addStretch(1)
        self.refresh()

    def set_profile(self, idx: int) -> None:
        power.set_profile(self.profiles[idx])

    def refresh(self) -> None:
        self.gm_button.setText("Turn Gaming Mode off" if power.gaming_mode_active() else "Turn Gaming Mode on")

    def toggle_gaming(self) -> None:
        if power.gaming_mode_active():
            power.disable_gaming_mode()
            self.gm_notes.setText("Gaming Mode off: previous settings restored.")
        else:
            self.gm_notes.setText("\n".join(power.enable_gaming_mode()))
        cur = power.current_profile()
        if cur in self.profiles:
            self.combo.setCurrentIndex(self.profiles.index(cur))
        self.refresh()


class HardwarePage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Hardware", "What SOS OS detected on this machine.")
        s = system.summary()
        grid = QGridLayout()
        rows = [
            ("Operating system", s.os_name),
            ("SOS OS version", s.sos_version),
            ("Debian base", s.debian),
            ("Kernel", s.kernel),
            ("Hostname", s.hostname),
            ("Processor", f"{s.cpu} ({s.cores} cores / {s.threads} threads)"),
            ("Memory", system.human_bytes(s.ram_total)),
            ("Firmware", "UEFI" if s.uefi else "Legacy BIOS"),
            ("Secure Boot", s.secure_boot),
            ("Virtualisation", s.virt),
        ]
        for i, g in enumerate(s.gpus):
            rows.append((f"GPU {i + 1}", f"{g.vendor} {g.name}  [driver: {g.driver or 'none'}]"))
        for d in s.disks:
            rows.append((f"Disk {d.mountpoint}", f"{d.device} {d.fstype}: {system.human_bytes(d.used)} of "
                                                 f"{system.human_bytes(d.total)} ({d.percent:.0f}%)"))
        card = Card()
        for r, (k, v) in enumerate(rows):
            grid.addWidget(label(k, "Dim"), r, 0, Qt.AlignmentFlag.AlignTop)
            grid.addWidget(label(v, wrap=True), r, 1)
        grid.setColumnStretch(1, 1)
        card.body.addLayout(grid)
        lay.addWidget(card)
        mon = QPushButton("Open SOS System Monitor")
        mon.clicked.connect(lambda: launch("sos-monitor"))
        lay.addWidget(mon)
        lay.addStretch(1)


class NetworkPage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Network", "Connections are managed by NetworkManager. "
                                           "Passwords are entered in Plasma's network dialog, never here.")
        self.dev_card = Card("Devices")
        self.dev_label = label("", wrap=True)
        self.dev_card.body.addWidget(self.dev_label)
        lay.addWidget(self.dev_card)

        wifi = Card("Wi-Fi")
        row = QHBoxLayout()
        self.wifi_toggle = QPushButton()
        self.wifi_toggle.clicked.connect(self.toggle_wifi)
        rescan = QPushButton("Scan")
        rescan.clicked.connect(lambda: self.refresh(rescan=True))
        row.addWidget(self.wifi_toggle)
        row.addWidget(rescan)
        row.addStretch(1)
        wifi.body.addLayout(row)
        self.nets = QListWidget()
        self.nets.setMinimumHeight(200)
        wifi.body.addWidget(self.nets)
        lay.addWidget(wifi)

        full = QPushButton("Open full network settings (connect, VPN, hotspot)")
        full.clicked.connect(lambda: launch("systemsettings", "kcm_networkmanagement"))
        lay.addWidget(full)
        lay.addStretch(1)
        self.refresh()

    def refresh(self, rescan: bool = False) -> None:
        devs = network.devices()
        self.dev_label.setText("<br>".join(
            f"{status_dot(d.state.startswith('connected'))} <b>{d.name}</b> ({d.type}): {d.state}"
            + (f", {d.connection}" if d.connection else "") for d in devs) or "nmcli unavailable")
        on = network.wifi_enabled()
        self.wifi_toggle.setText("Turn Wi-Fi off" if on else "Turn Wi-Fi on")
        self.wifi_toggle.setEnabled(on is not None)
        self.nets.clear()
        for n in network.wifi_networks(rescan=rescan) if on else []:
            self.nets.addItem(f"{'✓ ' if n.in_use else '   '}{n.ssid}   {n.signal}%   {n.security}")

    def toggle_wifi(self) -> None:
        network.set_wifi(not network.wifi_enabled())
        self.refresh()


class SecurityPage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Security", "Firewall and boot security.")
        self.helper = HelperRunner(self.widget)
        fw = Card("Firewall (ufw)")
        self.fw_label = label("", wrap=True)
        self.fw_button = QPushButton()
        self.fw_button.clicked.connect(self.toggle)
        fw.body.addWidget(self.fw_label)
        fw.body.addWidget(self.fw_button)
        lay.addWidget(fw)

        sb = Card("Secure Boot")
        state = system.secure_boot_state()
        sb.body.addWidget(label({
            "enabled": "Secure Boot is enabled. Kernel modules must be signed.",
            "disabled": "Secure Boot is disabled in your firmware settings. SOS OS works with it enabled; "
                        "turning it on is done in your firmware (BIOS) setup.",
            "not-uefi": "This system booted in legacy BIOS mode; Secure Boot is not available.",
        }.get(state, "Secure Boot state could not be determined (install mokutil)."), wrap=True))
        lay.addWidget(sb)

        self.log = LogView()
        self.log.setMaximumHeight(140)
        self.helper.output.connect(self.log.append_text)
        self.helper.done.connect(self.done)
        lay.addWidget(self.log)
        lay.addStretch(1)
        self.refresh()

    def refresh(self) -> None:
        en = firewall.enabled()
        self.fw_label.setText({True: f"{status_dot(True)} Enabled: incoming connections are blocked by default.",
                               False: f"{status_dot(False)} Disabled: your computer accepts incoming connections.",
                               None: f"{status_dot(None)} ufw is not installed."}[en])
        self.fw_button.setText("Disable firewall" if en else "Enable firewall")
        self.fw_button.setEnabled(en is not None)

    def toggle(self) -> None:
        if firewall.enabled():
            if QMessageBox.question(self.widget, "Disable firewall?",
                                    "Disabling the firewall lets other devices connect to any service "
                                    "running on this computer. Continue?") != QMessageBox.StandardButton.Yes:
                return
            self.helper.start_helper("firewall", "disable")
        else:
            self.helper.start_helper("firewall", "enable")

    def done(self, code: int) -> None:
        self.log.append_text(explain_helper_exit(code) + "\n")
        self.refresh()


class UpdatesPage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Updates", "Signed Debian updates and optional tool sets.")
        up = Card("System updates")
        n = len(apt.upgradable())
        up.body.addWidget(label(f"{n} update(s) pending (per the last package list refresh)." if n
                                else "No pending updates (per the last package list refresh).", wrap=True))
        open_up = QPushButton("Open SOS Updater")
        open_up.setObjectName("Primary")
        open_up.clicked.connect(lambda: launch("sos-updater"))
        up.body.addWidget(open_up)
        lay.addWidget(up)

        ts = Card("Optional tool sets")
        try:
            sets = toolsets.load()
        except (OSError, ValueError) as exc:
            sets = []
            ts.body.addWidget(label(f"Could not load tool sets: {exc}", "Dim"))
        for t in sets:
            state = all(apt.is_installed(p.split(":")[0]) for p in t.packages[:3])
            ts.body.addWidget(label(f"{status_dot(state)} <b>{t.name}</b>: {t.description}", wrap=True))
        manage = QPushButton("Install tool sets in SOS Welcome")
        manage.clicked.connect(lambda: launch("sos-welcome", "--page", "toolsets"))
        ts.body.addWidget(manage)
        lay.addWidget(ts)
        lay.addStretch(1)


class PersonalPage:
    def __init__(self, win: ControlCenter):
        self.widget, lay = page("Personalisation", "Make this computer yours.")
        host = Card("Computer name")
        row = QHBoxLayout()
        self.host = QLineEdit(system.summary().hostname)
        save = QPushButton("Rename")
        save.clicked.connect(self.rename)
        row.addWidget(self.host, 1)
        row.addWidget(save)
        host.body.addLayout(row)
        self.host_msg = label("", "Dim")
        host.body.addWidget(self.host_msg)
        lay.addWidget(host)

        desk = Card("Desktop layout")
        desk.body.addWidget(label("Reset the panel, launcher and widgets to the SOS OS default layout. "
                                  "Your files are not touched.", "Dim", wrap=True))
        reset = QPushButton("Reset desktop layout")
        reset.clicked.connect(self.reset_layout)
        desk.body.addWidget(reset)
        more = QPushButton("More settings (KDE System Settings)")
        more.clicked.connect(lambda: launch("systemsettings"))
        desk.body.addWidget(more)
        lay.addWidget(desk)
        lay.addWidget(label(f"SOS OS {sos_version()}", "Dim"))
        lay.addStretch(1)

    def rename(self) -> None:
        name = self.host.text().strip()
        if not HOSTNAME_RE.match(name):
            self.host_msg.setText("Use 1–63 letters, digits or hyphens (not at the start or end).")
            return
        # systemd-hostnamed asks polkit for authorisation itself.
        r = run(["hostnamectl", "set-hostname", name], timeout=60)
        self.host_msg.setText("Renamed." if r.ok else f"Failed: {r.err.strip()}")

    def reset_layout(self) -> None:
        if QMessageBox.question(self.widget, "Reset layout?",
                                "Replace your current panels and widgets with the SOS OS defaults?"
                                ) == QMessageBox.StandardButton.Yes:
            r = plasma.apply_look_and_feel(reset_layout=True)
            self.widget.window().statusBar().showMessage("Layout reset" if r.ok else f"Failed: {r.err.strip()}", 5000)


class ControlCenter(SidebarWindow):
    def __init__(self) -> None:
        super().__init__("SOS Control Center")
        self.pages: list = []
        for name, icon, cls in (
            ("Appearance", "preferences-desktop-theme", AppearancePage),
            ("Performance", "speedometer", PerformancePage),
            ("Hardware", "computer", HardwarePage),
            ("Network", "network-wireless", NetworkPage),
            ("Security", "security-high", SecurityPage),
            ("Updates", "system-software-update", UpdatesPage),
            ("Personalisation", "preferences-desktop", PersonalPage),
        ):
            try:
                pg = cls(self)
                widget = pg.widget
            except Exception as exc:  # keep the app usable if one backend fails
                widget, lay = page(name)
                lay.addWidget(label(f"This page failed to load: {exc}", wrap=True))
                pg = None
            self.pages.append(pg)
            self.add_page(name, widget, icon)


def main() -> int:
    args = base_parser("SOS Control Center").parse_args()
    app = make_app("sos-settings", "SOS Control Center", "sos-settings")
    return run_window(app, ControlCenter, args.self_test)


if __name__ == "__main__":
    sys.exit(main())

