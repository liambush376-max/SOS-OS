# Project status

Last updated for **v0.1.0 (in development)**. This page says plainly what
exists, what has been verified and what is still missing. Keep it accurate.

## Legend

* **Implemented**: code and configuration exist in this repository.
* **Verified**: covered by a test that has passed (where it passed is noted).
* **Unverified**: implemented, but hasn't been run on a real system yet.

## Status by area

| Area | State | Notes |
| --- | --- | --- |
| Repository, docs, license, templates | Implemented | |
| live-build config (Debian 13, amd64, BIOS+UEFI hybrid ISO) | Implemented, **unverified** | No ISO has been built yet; the first CI run will tell |
| Package-name preflight | Implemented | Runs at the start of every build |
| `sos-os-core` package | Implemented, **unverified** | Built in CI `test.yml → package` |
| Branding: logo, wallpapers, icons (SVG) | Implemented | PNGs rendered during build |
| SOS Dark colour scheme, look-and-feel, KWin blur/animation defaults | Implemented, **unverified** | Uses stock Breeze widget style and window decorations |
| Floating translucent panel layout, custom launcher icon | Implemented, **unverified** | Plasma 6 layout script |
| SOS Quick Stats panel widget | Implemented, **unverified** | Plasma5Support executable engine |
| Notification centre / quick settings | Stock Plasma system tray | Not reimplemented, only configured |
| SDDM login theme (Qt 6) | Implemented, **unverified** | |
| Plymouth boot splash (with LUKS prompt) | Implemented, **unverified** | |
| GRUB theme (installed systems) | Implemented, **unverified** | Live ISO uses live-build menus with SOS splash |
| Rounded windows | Partial | Breeze's own corner radius; no custom KWin effect yet |
| SOS Control Center | Implemented, **unverified** on SOS | Backends: plasma-apply-*, powerprofilesctl, nmcli, hostnamectl, ufw via helper |
| SOS System Monitor | Implemented, **unverified** on SOS | psutil, sysfs (amdgpu, i915/xe), nvidia-smi |
| SOS Updater + notifier timer | Implemented, **unverified** on SOS | APT via polkit helper; release *check* only |
| SOS Welcome | Implemented, **unverified** on SOS | Theme, hardware checks, tool-set install |
| SOS DevHub | Implemented, **unverified** on SOS | git clone, `gh auth login --web` |
| Privileged helper + polkit policy | Implemented, unit-tested | Allowlist tests in `tests/test_helper.py` |
| Gaming tool set (Steam, GameMode, MangoHud, 32-bit Mesa) | Implemented, **unverified** | Steam licence must be accepted in the GUI |
| NVIDIA tool set | Implemented, **unverified** | DKMS + MOK flow comes from Debian |
| Developer tool set | Implemented, **unverified** | Kate instead of VS Code (VS Code isn't redistributable; VSCodium isn't in Debian) |
| Calamares installer with SOS branding | Implemented, **unverified** | Debian's module configuration, SOS branding |
| Full-disk encryption | Via Calamares | **unverified** |
| Persistence | Documented (live-boot) | **untested** |
| Firewall on by default | Implemented | Checked by ISO filesystem tests once an ISO exists |
| CI: lint, tests, ISO build, QEMU boot test, release | Implemented | Not run yet: needs the repository on GitHub |

## Verified so far

The unit, config and helper test suite was run locally on Windows (Python 3.13)
while writing this release. See the latest `Tests` workflow run for results on
Debian 13. **No ISO has been built or booted yet.**

## Known gaps (planned)

* **SOS package repository**: SOS components currently update only with a
  new ISO. A signed APT repository (with the key kept offline, not in CI) is
  planned for v0.3.0.
* **In-place release upgrades** (e.g. 0.x → 1.0): the updater only reports new
  releases for now.
* **Custom Plasma desktop theme (SVG)** and **window decoration** with full
  rounded corners: v0.2.0.
* **Screenshots** for the README: after the first successful boot.
* **Hardware compatibility matrix**: v0.5.0.
* **Translations**: none yet.
