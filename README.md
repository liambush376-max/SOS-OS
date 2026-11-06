<p align="center">
  <img src="branding/logos/sos-logo.svg" width="128" alt="SOS OS logo">
</p>

<h1 align="center">SOS OS</h1>

<p align="center">
  A modern, dark, gaming- and developer-friendly Linux distribution built on
  <b>Debian 13 "trixie"</b> and <b>KDE Plasma 6</b>.
</p>

<p align="center">
  <a href="../../actions/workflows/build-iso.yml"><img alt="ISO build" src="../../actions/workflows/build-iso.yml/badge.svg"></a>
  <a href="../../actions/workflows/test.yml"><img alt="Tests" src="../../actions/workflows/test.yml/badge.svg"></a>
  <a href="../../actions/workflows/lint.yml"><img alt="Lint" src="../../actions/workflows/lint.yml/badge.svg"></a>
</p>

> **Status: pre-alpha (v0.1.0 in development).** Please don't install SOS OS on a
> machine whose data you care about yet. [docs/STATUS.md](docs/STATUS.md) lists
> what's implemented, what's been tested and what's still missing.

## What is SOS OS?

SOS OS is a Debian-based desktop operating system with its own visual identity
and its own system applications:

* **SOS Dark**: a dark Plasma colour scheme with electric-blue and purple
  accents, a floating translucent panel with blur, a custom launcher layout, a
  boot splash, a login screen and wallpapers.
* **SOS Control Center** (`sos-settings`): appearance, performance profiles,
  gaming mode, hardware information, network, firewall and updates.
* **SOS System Monitor** (`sos-monitor`): live CPU, GPU, RAM, disk, network
  and temperature graphs.
* **SOS Updater** (`sos-updater`): signed APT updates through a polkit-guarded
  helper, update notifications, and SOS release checks.
* **SOS Welcome** (`sos-welcome`): first-boot setup with theme selection,
  optional gaming and developer tool sets, and hardware checks.
* **SOS DevHub** (`sos-devhub`): clone GitHub repositories and open projects,
  with sign-in handled only by the official GitHub CLI.

SOS OS uses stock Debian packages from the signed Debian archive. It adds its
own `sos-os-core` package and configuration on top. It doesn't fork the kernel
or Plasma.

## Screenshots

There aren't any screenshots yet. They'll be added once the first ISO has been
boot-tested on real hardware.

## Installation

### 1. Download

Get the ISO and its `.sha256` file from
[GitHub Releases](../../releases). Development builds are available as
artifacts on the [ISO build workflow](../../actions/workflows/build-iso.yml)
runs for 7 days.

Verify the download:

```bash
sha256sum -c sos-os-0.1.0-amd64.iso.sha256
```

If a release ISO is bigger than 2 GiB, it's published in parts. Join the parts
before you verify:

```bash
cat sos-os-0.1.0-amd64.iso.part-* > sos-os-0.1.0-amd64.iso
```

### 2. Create a bootable USB stick

> ⚠️ Writing an image **erases everything** on the target USB stick. Check the
> device name twice.

* **Windows / macOS / Linux (graphical):** use
  [Fedora Media Writer](https://github.com/FedoraQt/MediaWriter) or
  [balenaEtcher](https://etcher.balena.io/) and pick the ISO. Rufus also works;
  choose **DD mode** when it asks.
* **Linux (command line):**

  ```bash
  lsblk -o NAME,SIZE,MODEL,TRAN   # find your USB stick, e.g. /dev/sdX
  sudo dd if=sos-os-0.1.0-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
  ```

### 3. Boot

Choose the USB stick in your firmware's boot menu. UEFI and legacy BIOS are
both supported. The live session logs in automatically as user `sos`. If a
password prompt ever shows up during the live session (for example, on the
lock screen), the password is `live`. That's the standard Debian live default,
and it only applies to the live session.

Secure Boot: the ISO uses Debian's signed shim and GRUB. SOS OS **never turns
Secure Boot off for you**. If your firmware rejects the image, see
[docs/INSTALL.md](docs/INSTALL.md#secure-boot).

### 4. Install

Double-click **Install SOS OS** on the live desktop. The Calamares installer
shows a summary before it changes any disk and asks for confirmation. Full-disk
encryption is an option on the partitioning page.

### Persistent live USB

See [docs/INSTALL.md](docs/INSTALL.md#persistent-live-usb).

## Virtual machines

```bash
# QEMU/KVM with UEFI firmware (Debian/Ubuntu: apt install qemu-system-x86 ovmf)
qemu-system-x86_64 -enable-kvm -m 4096 -smp 2 -cpu host \
  -bios /usr/share/ovmf/OVMF.fd \
  -device virtio-vga-gl -display gtk,gl=on \
  -cdrom sos-os-0.1.0-amd64.iso
```

VirtualBox: create a "Debian (64-bit)" VM with at least 4 GB RAM and 25 GB of
disk, turn on **EFI** under System → Motherboard, set the graphics controller to
**VMSVGA**, and attach the ISO.

## Building the ISO

Builds run in a privileged Debian 13 container, so any Linux host with Docker or
Podman can build an ISO:

```bash
./scripts/build-in-container.sh        # writes out/sos-os-<version>-amd64.iso
./scripts/validate-iso.sh out/sos-os-*-amd64.iso
./scripts/qemu-boot-test.sh out/sos-os-*-amd64.iso
```

You need about 25 GB of free disk space. A cold build takes 30–60 minutes. See
[docs/BUILDING.md](docs/BUILDING.md).

GitHub Actions builds the ISO on every push to `main`. You can also run it by
hand from **Actions → Build ISO → Run workflow**.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) and the maintainer guide in
[docs/MAINTAINERS.md](docs/MAINTAINERS.md).

## Reporting bugs

Open an issue with the **Bug report** template. For security problems, follow
[SECURITY.md](SECURITY.md) and **don't** open a public issue.

## License

SOS OS's own code, artwork and configuration are licensed under the
**GNU General Public License v3.0 or later** (see [LICENSE](LICENSE)). The
Debian packages shipped in the ISO keep their own licenses; see
`/usr/share/doc/*/copyright` on a running system and
[docs/LICENSING.md](docs/LICENSING.md).

SOS OS isn't affiliated with or endorsed by Debian or KDE.
