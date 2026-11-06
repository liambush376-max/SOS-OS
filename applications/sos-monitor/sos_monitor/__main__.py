"""SOS System Monitor: live CPU, GPU, RAM, disk, network and temperatures."""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QMainWindow, QProgressBar, QVBoxLayout, QWidget

from sos_common.qt_app import base_parser, make_app, run_window
from sos_common.qt_widgets import Card, Sparkline, label
from sos_common.system import human_bytes

from .sampler import Sampler


class MetricCard(Card):
    def __init__(self, title: str, maximum: float = 100.0, auto_scale: bool = False):
        super().__init__(title)
        self.value = label("—", "BigNumber")
        self.detail = label("", "Dim", wrap=True)
        self.graph = Sparkline(maximum=maximum)
        self.graph.auto_scale = auto_scale
        self.body.addWidget(self.value)
        self.body.addWidget(self.graph, 1)
        self.body.addWidget(self.detail)


class MonitorWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SOS System Monitor")
        self.resize(1180, 760)
        self.sampler = Sampler()

        central = QWidget()
        outer = QVBoxLayout(central)
        outer.setContentsMargins(20, 18, 20, 18)
        outer.addWidget(label("System Monitor", "Title"))
        outer.addWidget(label("Live readings, refreshed every second.", "Subtitle"))

        grid = QGridLayout()
        grid.setSpacing(14)
        self.cpu = MetricCard("CPU")
        self.gpu = MetricCard("GPU")
        self.ram = MetricCard("Memory")
        self.disk = MetricCard("Disk activity", auto_scale=True)
        self.net = MetricCard("Network", auto_scale=True)
        self.temp = MetricCard("Temperatures", maximum=110)
        for i, card in enumerate((self.cpu, self.gpu, self.ram, self.disk, self.net, self.temp)):
            grid.addWidget(card, i // 3, i % 3)
        outer.addLayout(grid, 1)

        self.cores_card = Card("CPU cores")
        self.cores_row = QHBoxLayout()
        self.cores_card.body.addLayout(self.cores_row)
        self.core_bars: list[QProgressBar] = []
        outer.addWidget(self.cores_card)

        self.setCentralWidget(central)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(1000)
        self.refresh()

    def refresh(self) -> None:
        s = self.sampler.sample()

        self.cpu.value.setText(f"{s.cpu_total:.0f}%")
        self.cpu.graph.push(s.cpu_total)
        freq = f"{s.cpu_freq_mhz / 1000:.2f} GHz · " if s.cpu_freq_mhz else ""
        self.cpu.detail.setText(f"{freq}load {s.load[0]:.2f} {s.load[1]:.2f} {s.load[2]:.2f}")

        if s.gpus:
            g = s.gpus[0]
            if g.busy_percent is not None:
                self.gpu.value.setText(f"{g.busy_percent:.0f}%")
                self.gpu.graph.push(g.busy_percent)
            else:
                self.gpu.value.setText("n/a")
            parts = [g.name]
            if g.metric == "frequency":
                parts.append("(clock vs. max; Intel exposes no utilisation counter)")
            if g.temp_c is not None:
                parts.append(f"{g.temp_c:.0f} °C")
            if g.vram_total:
                parts.append(f"VRAM {human_bytes(g.vram_used or 0)} / {human_bytes(g.vram_total)}")
            self.gpu.detail.setText(" · ".join(parts))
        else:
            self.gpu.value.setText("n/a")
            self.gpu.detail.setText("No GPU statistics available (VM or unsupported driver).")

        ram_pct = 100.0 * s.ram_used / s.ram_total if s.ram_total else 0
        self.ram.value.setText(f"{ram_pct:.0f}%")
        self.ram.graph.push(ram_pct)
        swap = f" · swap {human_bytes(s.swap_used)} / {human_bytes(s.swap_total)}" if s.swap_total else ""
        self.ram.detail.setText(f"{human_bytes(s.ram_used)} / {human_bytes(s.ram_total)}{swap}")

        io = s.disk_read_bps + s.disk_write_bps
        self.disk.value.setText(f"{human_bytes(io)}/s")
        self.disk.graph.push(io)
        self.disk.detail.setText(f"read {human_bytes(s.disk_read_bps)}/s · write {human_bytes(s.disk_write_bps)}/s")

        net = s.net_rx_bps + s.net_tx_bps
        self.net.value.setText(f"{human_bytes(net)}/s")
        self.net.graph.push(net)
        self.net.detail.setText(f"↓ {human_bytes(s.net_rx_bps)}/s · ↑ {human_bytes(s.net_tx_bps)}/s")

        temps = dict(s.temps)
        for g in s.gpus:
            if g.temp_c is not None:
                temps[g.name] = g.temp_c
        if temps:
            hottest_name, hottest = max(temps.items(), key=lambda kv: kv[1])
            self.temp.value.setText(f"{hottest:.0f} °C")
            self.temp.graph.push(hottest)
            top = sorted(temps.items(), key=lambda kv: -kv[1])[:4]
            self.temp.detail.setText(" · ".join(f"{k}: {v:.0f}°" for k, v in top))
        else:
            self.temp.value.setText("n/a")
            self.temp.detail.setText("No sensors found. Run `sensors-detect` (lm-sensors) on real hardware.")

        while len(self.core_bars) < len(s.cpu_per_core):
            bar = QProgressBar()
            bar.setOrientation(Qt.Orientation.Vertical)
            bar.setTextVisible(False)
            bar.setFixedWidth(14)
            bar.setMinimumHeight(60)
            self.core_bars.append(bar)
            self.cores_row.addWidget(bar)
        for bar, v in zip(self.core_bars, s.cpu_per_core, strict=False):
            bar.setValue(int(v))


def main() -> int:
    args = base_parser("SOS System Monitor").parse_args()
    app = make_app("sos-monitor", "SOS System Monitor", "sos-monitor")
    return run_window(app, MonitorWindow, args.self_test)


if __name__ == "__main__":
    sys.exit(main())
