"""NetworkManager queries and radio toggles via nmcli.

Connecting to password-protected networks is deliberately left to Plasma's
network applet / KCM, which store secrets in KWallet; SOS apps never handle
Wi-Fi passwords.
"""
from __future__ import annotations

from dataclasses import dataclass

from .proc import run


def split_terse(line: str) -> list[str]:
    """Split an `nmcli -t` line on unescaped ':' and unescape '\\:'."""
    fields, cur, esc = [], [], False
    for ch in line:
        if esc:
            cur.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            fields.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    fields.append("".join(cur))
    return fields


@dataclass
class Device:
    name: str
    type: str
    state: str
    connection: str


@dataclass
class WifiNetwork:
    in_use: bool
    ssid: str
    signal: int
    security: str


def parse_devices(text: str) -> list[Device]:
    out = []
    for line in text.splitlines():
        f = split_terse(line)
        if len(f) >= 4 and f[1] not in ("loopback",):
            out.append(Device(f[0], f[1], f[2], f[3]))
    return out


def parse_wifi(text: str) -> list[WifiNetwork]:
    nets: dict[str, WifiNetwork] = {}
    for line in text.splitlines():
        f = split_terse(line)
        if len(f) < 4 or not f[1].strip() or f[1] == "--":  # hidden networks
            continue
        try:
            sig = int(f[2])
        except ValueError:
            sig = 0
        net = WifiNetwork(f[0].strip() == "*", f[1], sig, f[3] or "open")
        prev = nets.get(net.ssid)
        if prev is None or net.in_use or (not prev.in_use and net.signal > prev.signal):
            nets[net.ssid] = net
    return sorted(nets.values(), key=lambda n: (not n.in_use, -n.signal))


def devices() -> list[Device]:
    r = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device"])
    return parse_devices(r.out) if r.ok else []


def wifi_networks(rescan: bool = False) -> list[WifiNetwork]:
    r = run(["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list",
             "--rescan", "yes" if rescan else "auto"], timeout=20)
    return parse_wifi(r.out) if r.ok else []


def wifi_enabled() -> bool | None:
    r = run(["nmcli", "radio", "wifi"])
    if not r.ok:
        return None
    return r.out.strip() == "enabled"


def set_wifi(enabled: bool) -> bool:
    return run(["nmcli", "radio", "wifi", "on" if enabled else "off"]).ok
