# Changelog

All notable changes to SOS OS are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added
- Repository structure, GPL-3.0-or-later license and contribution docs.
- live-build configuration for a Debian 13 "trixie" amd64 hybrid ISO
  (UEFI and BIOS) with KDE Plasma 6, SDDM, Calamares and firmware.
- `sos-os-core` package: os-release branding, SOS Dark colour scheme,
  `org.sosos.desktop` look-and-feel with a floating panel layout, SOS Quick Stats
  panel widget, SDDM login theme, Plymouth boot splash, GRUB theme, KWin
  blur/animation defaults, ufw firewall enabled by default.
- Applications: SOS Control Center, SOS System Monitor, SOS Updater (with a
  user-level update notifier timer), SOS Welcome and SOS DevHub, plus the
  polkit-guarded `sos-helper`.
- GitHub Actions: lint, tests, ISO build with QEMU boot test, tag-driven
  release.

[Unreleased]: ../../compare/main...HEAD
