# Building SOS OS

## Why Debian 13 "trixie"?

| | Debian 13 (chosen) | Ubuntu 24.04/26.04 LTS |
| --- | --- | --- |
| Image tooling | `live-build`, Debian's own native, maintained tool | `live-build` isn't Ubuntu's supported path; official images use internal tooling |
| Plasma | Plasma 6.3, stock and unpatched | Kubuntu ships Plasma, but Ubuntu's defaults favour GNOME |
| Packaging | No snaps; all `.deb`, signed archive | Firefox and others are snaps, which complicates offline ISOs |
| Redistribution | Clear DFSG policy, firmware split into `non-free-firmware` | Trademark policy restricts derivatives that reuse Ubuntu branding |
| Support | Security support until 2028, LTS to 2030 | 5 years |

## Requirements

* Linux host with Docker or Podman (a privileged container is needed for
  loop devices and mounts), **or** a Debian 13 machine/VM where you are root
* About 25 GB of free disk space and 4 GB of RAM
* Internet access to `deb.debian.org`

Windows and macOS users: build in a Debian VM, or push to GitHub and let
Actions build the ISO.

## Build

```bash
./scripts/build-in-container.sh
```

This runs `scripts/build-iso.sh` inside `debian:trixie`:

1. installs `live-build`, `librsvg2-bin`, `xorriso` and friends,
2. **preflights every package name** in `iso/config/package-lists/` against
   the trixie archive (fails fast on typos/renames),
3. builds `out/sos-os-core_<version>_all.deb` with `scripts/build-packages.sh`
   (renders all PNGs from the SVG sources),
4. copies live-build's bootloader templates and puts in the SOS splash,
5. runs `lb clean && lb config && lb build` in `iso/`,
6. writes `out/sos-os-<version>-amd64.iso`, `.sha256` and `.packages`.

Downloaded packages are cached in `iso/cache/`, so rebuilds are much faster.

On a Debian 13 host you can skip the container: `sudo ./scripts/build-iso.sh`.

## Validate and boot-test

```bash
sudo apt install xorriso squashfs-tools python3-pytest qemu-system-x86
./scripts/validate-iso.sh out/sos-os-0.1.0-amd64.iso
./scripts/qemu-boot-test.sh out/sos-os-0.1.0-amd64.iso
```

See [TESTING.md](TESTING.md) for what each test covers.

## Working on the apps without building an ISO

```bash
sudo apt install python3-pyqt6 python3-psutil   # Debian/Ubuntu
./scripts/run-app.sh sos-monitor
./scripts/run-app.sh sos-settings
```

Actions that need root (`pkexec sos-helper …`) only work on a system with
`sos-os-core` installed.

## Changing what's in the ISO

* Add or remove packages in `iso/config/package-lists/*.list.chroot`.
* System-wide defaults go in `desktop/configuration/rootfs/` (copied as-is
  into the `sos-os-core` package; files under `etc/` become conffiles).
* Steps that only make sense inside the image build go in
  `iso/config/hooks/live/`.

## CI build

`.github/workflows/build-iso.yml` does the same thing on `ubuntu-24.04`
runners: it frees roughly 30 GB of preinstalled toolchains, restores the
weekly-rotated live-build package cache, builds, validates, uploads the ISO as
an artifact (kept for 7 days, uncompressed) and then boots it in QEMU/KVM in a
second job.

Limits to keep in mind:

| Limit | Value | How SOS OS handles it |
| --- | --- | --- |
| Job time | 6 h | build job capped at 150 min; typical cold build ~45 min |
| Runner disk | ~14 GB free by default | cleanup step frees space first |
| Actions cache | 10 GB per repo | package cache only (~1.5 GB), rotated weekly |
| Artifact retention | 90 days max | 7 days for ISOs, 14 for logs |
| Release asset size | 2 GiB per file | ISO is split into 1900 MiB parts if needed (see `release.yml`) |

If split downloads become a burden, the practical alternatives are: a
self-hosted mirror or object storage bucket (for example Cloudflare R2, Backblaze
B2 or SourceForge) with the Release linking to it, or BitTorrent. Upload
credentials for those would be stored as GitHub Secrets in the `release`
environment.
