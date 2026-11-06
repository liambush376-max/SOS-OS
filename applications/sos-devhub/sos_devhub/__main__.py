"""SOS DevHub: clone repositories, open projects, and sign in to GitHub via
the official GitHub CLI (`gh auth login --web`). DevHub never asks for or
stores credentials itself."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PyQt6.QtCore import QProcess, QProcessEnvironment
from PyQt6.QtWidgets import (
    QComboBox, QFileDialog, QHBoxLayout, QLineEdit, QListWidget, QMainWindow, QPushButton,
    QVBoxLayout, QWidget,
)

from sos_common.proc import have, run
from sos_common.qt_widgets import Card, LogView, label

from . import repos

DEFAULT_ROOT = Path.home() / "Projects"


class DevHubWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SOS DevHub")
        self.resize(940, 700)
        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(24, 20, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(label("DevHub", "Title"))

        # GitHub account
        acct = Card("GitHub account")
        self.acct_label = label("", "Dim", wrap=True)
        row = QHBoxLayout()
        self.login_btn = QPushButton("Sign in with GitHub CLI (opens browser)")
        self.login_btn.clicked.connect(self.gh_login)
        refresh = QPushButton("Refresh status")
        refresh.clicked.connect(self.gh_status)
        row.addWidget(self.login_btn)
        row.addWidget(refresh)
        row.addStretch(1)
        acct.body.addWidget(self.acct_label)
        acct.body.addLayout(row)
        lay.addWidget(acct)

        # Clone
        clone = Card("Clone a repository")
        self.url = QLineEdit()
        self.url.setPlaceholderText("owner/repo, https://github.com/owner/repo or git@github.com:owner/repo.git")
        drow = QHBoxLayout()
        self.dest = QLineEdit(str(DEFAULT_ROOT))
        browse = QPushButton("Browse…")
        browse.clicked.connect(self.pick_dest)
        drow.addWidget(self.dest, 1)
        drow.addWidget(browse)
        self.clone_btn = QPushButton("Clone")
        self.clone_btn.setObjectName("Primary")
        self.clone_btn.clicked.connect(self.clone)
        clone.body.addWidget(self.url)
        clone.body.addLayout(drow)
        clone.body.addWidget(self.clone_btn)
        lay.addWidget(clone)

        # Projects
        proj = Card("Projects")
        self.list = QListWidget()
        self.list.setMinimumHeight(160)
        self.list.itemDoubleClicked.connect(lambda _i: self.open_editor())
        prow = QHBoxLayout()
        self.editor = QComboBox()
        for cmd, name in repos.available_editors():
            self.editor.addItem(name, cmd)
        if self.editor.count() == 0:
            self.editor.addItem("No editor installed (add the Developer tool set)", "")
        open_btn = QPushButton("Open in editor")
        open_btn.clicked.connect(self.open_editor)
        term_btn = QPushButton("Open terminal here")
        term_btn.clicked.connect(self.open_terminal)
        files_btn = QPushButton("Show in Dolphin")
        files_btn.clicked.connect(self.open_files)
        prow.addWidget(self.editor, 1)
        for b in (open_btn, term_btn, files_btn):
            prow.addWidget(b)
        proj.body.addWidget(self.list, 1)
        proj.body.addLayout(prow)
        lay.addWidget(proj, 1)

        self.log = LogView()
        self.log.setMaximumHeight(150)
        lay.addWidget(self.log)
        self.setCentralWidget(central)

        self.proc = QProcess(self)
        self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.proc.readyReadStandardOutput.connect(
            lambda: self.log.append_text(bytes(self.proc.readAllStandardOutput()).decode(errors="replace")))
        self.proc.finished.connect(self.clone_done)
        self.gh_status()
        self.load_projects()

    # --- GitHub CLI ------------------------------------------------------
    def gh_status(self) -> None:
        if not have("gh"):
            self.acct_label.setText("The GitHub CLI isn't installed. Install the Developer tool set from SOS Welcome. "
                                    "Public repositories can still be cloned without signing in.")
            self.login_btn.setEnabled(False)
            return
        r = run(["gh", "auth", "status", "--hostname", "github.com"], timeout=15)
        text = (r.out + r.err).strip()
        account = next((ln.split("account", 1)[1].split()[0] for ln in text.splitlines() if "Logged in to" in ln
                        and "account" in ln), "")
        self.acct_label.setText(f"Signed in as {account}." if r.ok and account else
                                "Not signed in. Signing in uses GitHub's own device/browser flow; "
                                "DevHub never sees your password or token.")
        self.login_btn.setEnabled(True)

    def gh_login(self) -> None:
        cmd = ["gh", "auth", "login", "--hostname", "github.com", "--web", "--git-protocol", "https"]
        if have("konsole"):
            subprocess.Popen(["konsole", "--hold", "-e", *cmd], start_new_session=True)  # noqa: S603
            self.log.append_text("Opened a terminal for `gh auth login`. Follow the steps there, then "
                                 "click Refresh status.\n")
        else:
            self.log.append_text("Run this in a terminal: " + " ".join(cmd) + "\n")

    # --- clone -----------------------------------------------------------
    def pick_dest(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Clone into", self.dest.text())
        if d:
            self.dest.setText(d)

    def clone(self) -> None:
        try:
            url = repos.normalise_url(self.url.text())
            name = repos.repo_dir_name(url)
        except ValueError as exc:
            self.log.append_text(f"{exc}\n")
            return
        root = Path(self.dest.text()).expanduser()
        target = root / name
        if target.exists():
            self.log.append_text(f"{target} already exists.\n")
            return
        root.mkdir(parents=True, exist_ok=True)
        self.clone_btn.setEnabled(False)
        self.log.append_text(f"$ git clone --progress {url} {target}\n")
        # GIT_TERMINAL_PROMPT=0: never prompt for credentials in a hidden pipe;
        # private repos authenticate through gh's credential helper.
        env = QProcessEnvironment.systemEnvironment()
        env.insert("GIT_TERMINAL_PROMPT", "0")
        self.proc.setProcessEnvironment(env)
        self.proc.start("git", ["clone", "--progress", url, str(target)])

    def clone_done(self, code: int, _status) -> None:
        self.clone_btn.setEnabled(True)
        self.log.append_text("Clone finished.\n" if code == 0 else
                             f"git exited with {code}. For private repositories, sign in first.\n")
        self.load_projects()

    # --- projects --------------------------------------------------------
    def load_projects(self) -> None:
        self.list.clear()
        self.paths = repos.projects(Path(self.dest.text()).expanduser())
        for p in self.paths:
            self.list.addItem(f"{p.name}    {p}")

    def selected(self) -> Path | None:
        i = self.list.currentRow()
        return self.paths[i] if 0 <= i < len(self.paths) else None

    def open_editor(self) -> None:
        p, cmd = self.selected(), self.editor.currentData()
        if p and cmd:
            subprocess.Popen([cmd, str(p)], start_new_session=True)  # noqa: S603

    def open_terminal(self) -> None:
        p = self.selected()
        if p and have("konsole"):
            subprocess.Popen(["konsole", "--workdir", str(p)], start_new_session=True)  # noqa: S603

    def open_files(self) -> None:
        p = self.selected()
        if p and have("dolphin"):
            subprocess.Popen(["dolphin", str(p)], start_new_session=True)  # noqa: S603


def main() -> int:
    from sos_common.qt_app import base_parser, make_app, run_window

    args = base_parser("SOS DevHub").parse_args()
    app = make_app("sos-devhub", "SOS DevHub", "sos-devhub")
    return run_window(app, DevHubWindow, args.self_test)


if __name__ == "__main__":
    sys.exit(main())
