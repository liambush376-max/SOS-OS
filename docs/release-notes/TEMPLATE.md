## SOS OS @VERSION@

> Pre-release builds are for testing. Don't install them on machines whose data you can't afford to lose.

### Highlights

- …

### Download and verify

| File | Purpose |
| --- | --- |
| `sos-os-@VERSION@-amd64.iso` | Bootable hybrid ISO (USB/DVD, UEFI and BIOS) |
| `sos-os-@VERSION@-amd64.iso.sha256` | SHA-256 checksum |
| `sos-os-@VERSION@-amd64.packages` | List of every package and version in the image |

```bash
sha256sum -c sos-os-@VERSION@-amd64.iso.sha256
```

### Installation

1. Write the ISO to a USB stick with Fedora Media Writer, balenaEtcher, Rufus (DD mode) or `dd`.
   **This erases the stick.**
2. Boot from it (UEFI or BIOS; Secure Boot supported).
3. Try the live desktop, then double-click **Install SOS OS**. The installer shows every disk change and
   asks for confirmation before it writes anything.

Full guide: [docs/INSTALL.md](https://github.com/liambush376-max/SOS-OS/blob/main/docs/INSTALL.md)

### Known issues

- …

### Hardware compatibility

| Hardware | Status | Notes |
| --- | --- | --- |
| QEMU/KVM (CI boot test) | | |
| VirtualBox | | |
| AMD GPU | | |
| Intel GPU | | |
| NVIDIA GPU (nouveau / proprietary) | | |
