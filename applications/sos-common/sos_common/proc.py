"""Small subprocess helpers that never raise for a missing binary."""
from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass
class Result:
    code: int
    out: str
    err: str

    @property
    def ok(self) -> bool:
        return self.code == 0


def have(cmd: str) -> bool:
    return shutil.which(cmd) is not None


def run(argv: list[str], timeout: float = 15.0, env: dict | None = None) -> Result:
    """Run argv and capture output. Returns code 127 if the binary is missing
    and 124 on timeout, mirroring shell conventions."""
    if not have(argv[0]):
        return Result(127, "", f"{argv[0]}: not found")
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        return Result(124, "", f"{argv[0]}: timed out after {timeout}s")
    except OSError as exc:
        return Result(126, "", str(exc))
    return Result(p.returncode, p.stdout, p.stderr)
