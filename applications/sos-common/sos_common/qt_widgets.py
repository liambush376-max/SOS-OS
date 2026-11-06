"""Reusable SOS widgets: cards, sparkline graphs, sidebar shell, log view and
a QProcess runner for the polkit helper."""
from __future__ import annotations

from collections import deque

from PyQt6.QtCore import QProcess, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QMainWindow, QPlainTextEdit,
    QScrollArea, QStackedWidget, QVBoxLayout, QWidget,
)

from .qt_app import ACCENT, ACCENT2, FG_DIM

HELPER = "/usr/libexec/sos-os/sos-helper"


class Card(QFrame):
    def __init__(self, title: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 16, 18, 16)
        self.body.setSpacing(8)
        if title:
            t = QLabel(title)
            t.setObjectName("CardTitle")
            self.body.addWidget(t)


def label(text: str = "", obj: str = "", wrap: bool = False) -> QLabel:
    lab = QLabel(text)
    if obj:
        lab.setObjectName(obj)
    lab.setWordWrap(wrap)
    lab.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return lab


def page(title: str, subtitle: str = "") -> tuple[QScrollArea, QVBoxLayout]:
    """A scrollable page with a header; returns (widget, content layout)."""
    inner = QWidget()
    lay = QVBoxLayout(inner)
    lay.setContentsMargins(28, 24, 28, 24)
    lay.setSpacing(14)
    lay.addWidget(label(title, "Title"))
    if subtitle:
        lay.addWidget(label(subtitle, "Subtitle", wrap=True))
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setWidget(inner)
    return scroll, lay


class Sparkline(QWidget):
    """Rolling line graph (0..maximum) with a blue→purple gradient fill."""

    def __init__(self, points: int = 60, maximum: float = 100.0, parent: QWidget | None = None):
        super().__init__(parent)
        self.values: deque[float] = deque([0.0] * points, maxlen=points)
        self.maximum = maximum
        self.auto_scale = False
        self.setMinimumHeight(70)

    def push(self, value: float) -> None:
        self.values.append(max(0.0, float(value)))
        if self.auto_scale:
            self.maximum = max(1.0, max(self.values) * 1.2)
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802 (Qt API)
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 4, -1, -1)
        p.setPen(QPen(QColor(255, 255, 255, 18), 1))
        for i in range(1, 4):
            y = r.top() + r.height() * i / 4
            p.drawLine(int(r.left()), int(y), int(r.right()), int(y))
        n = len(self.values)
        if n < 2:
            return
        step = r.width() / (n - 1)
        path = QPainterPath()
        for i, v in enumerate(self.values):
            x = r.left() + i * step
            y = r.bottom() - r.height() * min(1.0, v / self.maximum if self.maximum else 0)
            path.moveTo(x, y) if i == 0 else path.lineTo(x, y)
        fill = QPainterPath(path)
        fill.lineTo(r.right(), r.bottom())
        fill.lineTo(r.left(), r.bottom())
        fill.closeSubpath()
        grad = QLinearGradient(0, r.top(), 0, r.bottom())
        c1, c2 = QColor(ACCENT), QColor(ACCENT2)
        c1.setAlpha(110)
        c2.setAlpha(10)
        grad.setColorAt(0, c1)
        grad.setColorAt(1, c2)
        p.fillPath(fill, grad)
        line = QLinearGradient(r.left(), 0, r.right(), 0)
        line.setColorAt(0, QColor(ACCENT))
        line.setColorAt(1, QColor(ACCENT2))
        p.setPen(QPen(line, 2))
        p.drawPath(path)


class SidebarWindow(QMainWindow):
    """Main window with a navigation list on the left and stacked pages."""

    def __init__(self, title: str):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(1080, 720)
        central = QWidget()
        row = QHBoxLayout(central)
        row.setContentsMargins(12, 12, 12, 12)
        row.setSpacing(12)
        self.nav = QListWidget()
        self.nav.setObjectName("Nav")
        self.nav.setFixedWidth(220)
        self.stack = QStackedWidget()
        row.addWidget(self.nav)
        row.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self.nav.currentRowChanged.connect(self.stack.setCurrentIndex)

    def add_page(self, name: str, widget: QWidget, icon: str = "") -> None:
        from PyQt6.QtGui import QIcon

        item = QListWidgetItem(QIcon.fromTheme(icon), name) if icon else QListWidgetItem(name)
        self.nav.addItem(item)
        self.stack.addWidget(widget)
        if self.nav.count() == 1:
            self.nav.setCurrentRow(0)


class LogView(QPlainTextEdit):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("Log")
        self.setReadOnly(True)
        self.setMaximumBlockCount(5000)
        self.setMinimumHeight(160)

    def append_text(self, text: str) -> None:
        self.moveCursor(self.textCursor().MoveOperation.End)
        self.insertPlainText(text)
        self.ensureCursorVisible()


class HelperRunner(QProcess):
    """Runs `pkexec sos-helper <args>` and streams output. polkit shows its
    own authentication dialog; SOS apps never see the password."""

    output = pyqtSignal(str)
    done = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.readyReadStandardOutput.connect(self._read)
        self.finished.connect(lambda code, _status: self.done.emit(code))
        self.errorOccurred.connect(self._error)

    def start_helper(self, *args: str) -> None:
        self.output.emit(f"$ pkexec sos-helper {' '.join(args)}\n")
        self.start("pkexec", [HELPER, *args])

    def _read(self) -> None:
        self.output.emit(bytes(self.readAllStandardOutput()).decode(errors="replace"))

    def _error(self, err) -> None:
        if err == QProcess.ProcessError.FailedToStart:
            self.output.emit("Could not start pkexec. Is polkit installed?\n")
            self.done.emit(127)


def explain_helper_exit(code: int) -> str:
    return {
        0: "Finished successfully.",
        126: "Authentication was cancelled or refused.",
        127: "Authentication failed or the helper is missing.",
        2: "The helper rejected the request.",
        3: "The licence must be accepted first.",
    }.get(code, f"Failed (exit code {code}). See the log above.")


def status_dot(ok: bool | None) -> str:
    color = {True: "#38D696", False: "#FF5470", None: FG_DIM}[ok]
    return f'<span style="color:{color}">●</span>'
