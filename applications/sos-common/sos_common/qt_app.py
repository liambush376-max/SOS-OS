"""Qt application bootstrap, SOS styling and --self-test support."""
from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtWidgets import QApplication, QWidget

ACCENT = "#2F7BFF"
ACCENT2 = "#9B3DFF"
BG = "#0D0F20"
SURFACE = "#15182F"
FG = "#E6E9FF"
FG_DIM = "#8C92BA"
DANGER = "#FF5470"
OK = "#38D696"

STYLESHEET = f"""
QWidget {{ color: {FG}; font-size: 10.5pt; }}
QMainWindow, QDialog {{ background: {BG}; }}
QFrame#Card {{
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
}}
QLabel#Title {{ font-size: 20pt; font-weight: 600; }}
QLabel#Subtitle, QLabel#Dim {{ color: {FG_DIM}; }}
QLabel#CardTitle {{ font-size: 11pt; font-weight: 600; color: {FG}; }}
QLabel#BigNumber {{ font-size: 22pt; font-weight: 300; }}
QListWidget#Nav {{
    background: rgba(255, 255, 255, 0.03); border: none; border-radius: 14px; padding: 8px;
    font-size: 11pt;
}}
QListWidget#Nav::item {{ padding: 10px 14px; border-radius: 10px; margin: 2px 0; }}
QListWidget#Nav::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
    color: white;
}}
QListWidget#Nav::item:hover:!selected {{ background: rgba(255, 255, 255, 0.06); }}
QPushButton {{
    background: rgba(255, 255, 255, 0.07); border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px; padding: 8px 16px;
}}
QPushButton:hover {{ background: rgba(255, 255, 255, 0.12); }}
QPushButton:disabled {{ color: {FG_DIM}; background: rgba(255, 255, 255, 0.03); }}
QPushButton#Primary {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
    border: none; color: white; font-weight: 600;
}}
QPushButton#Primary:disabled {{ background: rgba(47, 123, 255, 0.35); }}
QLineEdit, QComboBox, QPlainTextEdit, QListWidget, QTreeWidget, QTableWidget, QSpinBox {{
    background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 10px; padding: 6px; selection-background-color: {ACCENT};
}}
QLineEdit:focus, QComboBox:focus {{ border-color: {ACCENT}; }}
QPlainTextEdit#Log {{ font-family: "JetBrains Mono", monospace; font-size: 9pt; }}
QHeaderView::section {{ background: transparent; color: {FG_DIM}; border: none; padding: 6px; }}
QProgressBar {{
    background: rgba(255, 255, 255, 0.06); border: none; border-radius: 5px; height: 10px; text-align: center;
}}
QProgressBar::chunk {{
    border-radius: 5px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {ACCENT}, stop:1 {ACCENT2});
}}
QCheckBox::indicator, QRadioButton::indicator {{ width: 18px; height: 18px; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QSlider::groove:horizontal {{ height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; }}
QSlider::handle:horizontal {{ width: 16px; margin: -6px 0; border-radius: 8px; background: {ACCENT}; }}
QTabBar::tab {{ padding: 8px 16px; border-radius: 8px; margin-right: 4px; background: transparent; }}
QTabBar::tab:selected {{ background: rgba(47,123,255,0.25); }}
QTabWidget::pane {{ border: none; }}
"""


def make_app(app_id: str, display_name: str, icon: str) -> QApplication:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName(app_id)
    app.setApplicationDisplayName(display_name)
    app.setDesktopFileName(app_id)
    app.setWindowIcon(QIcon.fromTheme(icon))
    app.setStyle("Fusion")
    pal = QPalette()
    for role, color in (
        (QPalette.ColorRole.Window, BG), (QPalette.ColorRole.Base, SURFACE),
        (QPalette.ColorRole.AlternateBase, "#1A1D38"), (QPalette.ColorRole.Text, FG),
        (QPalette.ColorRole.WindowText, FG), (QPalette.ColorRole.Button, SURFACE),
        (QPalette.ColorRole.ButtonText, FG), (QPalette.ColorRole.Highlight, ACCENT),
        (QPalette.ColorRole.HighlightedText, "#FFFFFF"), (QPalette.ColorRole.ToolTipBase, SURFACE),
        (QPalette.ColorRole.ToolTipText, FG), (QPalette.ColorRole.PlaceholderText, FG_DIM),
        (QPalette.ColorRole.Link, "#569CFF"),
    ):
        pal.setColor(role, QColor(color))
    app.setPalette(pal)
    app.setStyleSheet(STYLESHEET)
    return app


def base_parser(description: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--self-test", action="store_true",
                   help="construct the main window, run the event loop briefly and exit 0 (used by CI)")
    return p


def run_window(app: QApplication, factory: Callable[[], QWidget], self_test: bool) -> int:
    window = factory()
    window.show()
    if self_test:
        def finish() -> None:
            print(f"SELFTEST-OK {app.applicationName()} {window.windowTitle()!r}")
            app.quit()
        QTimer.singleShot(1500, finish)
    return app.exec()
