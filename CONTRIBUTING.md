# Contributing to SOS OS

Thanks for helping build SOS OS! This guide covers the workflow every change
goes through.

## Ground rules

* **Never commit secrets**: passwords, API tokens, SSH private keys or signing
  keys. If you commit one by accident, tell a maintainer straight away so the
  secret can be rotated. Rewriting history isn't enough.
* **Don't claim more than you tested.** If you couldn't boot-test a change, say
  so in the PR.
* **Respect upstream licenses.** Only add artwork, fonts or binaries whose
  license allows redistribution, and record them in `docs/LICENSING.md`.

## Workflow

1. Open (or pick up) an issue, and assign it to the right milestone
   (`v0.1.0`, `v0.2.0`, …).
2. Create a branch from `main`:
   `feature/<short-name>`, `fix/<short-name>` or `docs/<short-name>`.
3. Make focused commits in the imperative mood ("Add GPU sensor to monitor").
4. Run the local checks:

   ```bash
   ./scripts/lint.sh
   python3 -m pytest tests -q
   ```

5. Open a pull request with the PR template filled in. CI (lint, tests, ISO
   build) has to pass, and one maintainer has to approve.
6. Maintainers squash-merge into `main`.

## Repository layout

| Path | Purpose |
| --- | --- |
| `iso/` | live-build configuration (package lists, hooks, `auto/` scripts) |
| `packages/sos-os-core/` | Debian packaging metadata for the `sos-os-core` package |
| `applications/` | SOS applications (Python 3 + PyQt6) and the shared `sos_common` library |
| `desktop/` | Plasma look-and-feel, colour scheme, panel widget, SDDM, Plymouth and GRUB themes, system config |
| `branding/` | Original SVG logos, wallpapers and icons (PNG files are generated during the build) |
| `installer/` | Calamares branding and configuration overrides |
| `scripts/` | Build, validation, lint and QEMU test scripts |
| `tests/` | pytest suites and ISO tests |
| `docs/` | User and maintainer documentation |

## Coding style

* **Python:** Python 3.11+, checked with `ruff`. Only use libraries Debian
  ships (`python3-pyqt6`, `python3-psutil`), with no pip dependencies at
  runtime. Keep the system logic (backends) in `sos_common` and separate from
  the Qt widgets so it can be unit-tested.
* **Shell:** `#!/bin/bash` with `set -euo pipefail`, clean under `shellcheck`.
* **QML:** Qt 6 / Plasma 6 APIs only.
* **Privileged operations** go only through `/usr/libexec/sos-os/sos-helper`,
  which accepts a fixed allowlist of actions and is authorised through polkit.
  Never run a GUI as root.

## Commit sign-off

Add a `Signed-off-by:` line (`git commit -s`) to certify the
[Developer Certificate of Origin](https://developercertificate.org/).
