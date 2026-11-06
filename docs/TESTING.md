# Testing SOS OS

| Layer | Where | Command | Covers |
| --- | --- | --- | --- |
| Static checks | `lint.yml` | `./scripts/lint.sh` | shellcheck, ruff, Python syntax, `desktop-file-validate`, actionlint, XML/JSON |
| Unit & config | `test.yml` (Debian 13 container) | `python3 -m pytest tests --ignore=tests/iso` | repo layout, live-build package lists and options, config validity (colour scheme, SDDM, Plymouth, polkit, desktop files, systemd units, toolsets), backend parsers, helper allowlist, secret scan |
| App start-up | `test.yml` | `tests/test_app_startup.py` | each app builds its main window headless (`QT_QPA_PLATFORM=offscreen`, `--self-test`) |
| Package | `test.yml` | `./scripts/build-packages.sh out` | `sos-os-core` builds, contains key files; lintian (informational) |
| ISO structure | `build-iso.yml` | `./scripts/validate-iso.sh <iso>` | size, checksum, BIOS + UEFI El Torito, kernel/initrd/squashfs, GRUB config |
| ISO root filesystem | `build-iso.yml` | `tests/iso/` (run by validate-iso.sh) | SOS files present, os-release, merged-/usr layout, enabled services, firewall on, SDDM/Plymouth/Calamares branding, permissions, no world-writable files, no SSH server, no password hashes, required packages |
| Boot | `build-iso.yml` (`boot-test` job) | `./scripts/qemu-boot-test.sh <iso>` | live system boots in QEMU (KVM when available) and reaches `graphical.target` with the display manager active |

## How the boot test decides pass/fail

`sos-boot-report.service` (in `sos-os-core`) runs after `graphical.target`,
waits up to 3 minutes for `display-manager.service` to become active, then
prints exactly one line to the console:

```
SOS-OS-BOOT-OK version=0.1.0 target=graphical dm=active failed_units=0
```

or `SOS-OS-BOOT-FAIL …`. The test boots the ISO's kernel/initrd directly
with `console=ttyS0` so the line reaches QEMU's serial log, while the root
filesystem still comes from the ISO attached as a CD-ROM. A kernel panic,
"Unable to find a medium", QEMU exiting, or a timeout (15 min with KVM,
45 min without) all count as failures.

**Not covered by automated boot testing:** the GRUB/ISOLINUX menus themselves
(they're checked structurally only), whether the Plasma session renders
correctly (only that SDDM is running), Calamares installation, persistence,
and real hardware. Those need manual testing; see the checklist below.

## Manual test checklist (per release)

- [ ] UEFI boot with Secure Boot on (real hardware)
- [ ] Legacy BIOS boot
- [ ] Live desktop: panel, launcher, Quick Stats widget, notifications, quick settings
- [ ] Each SOS app opens; Control Center pages load
- [ ] Wi-Fi connect through Plasma applet
- [ ] Install with *Erase disk*; install with encryption; dual-boot alongside Windows
- [ ] First login shows SOS Welcome; Gaming and Developer tool sets install
- [ ] `sos-updater` refresh + upgrade
- [ ] Plymouth splash and LUKS prompt on installed system
- [ ] AMD, Intel and NVIDIA GPUs; Steam game via Proton
- [ ] Game controller detected (`steam-devices` udev rules)
- [ ] VirtualBox, VMware, QEMU guests
