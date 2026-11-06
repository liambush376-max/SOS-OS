# Installing SOS OS

## System requirements

| | Minimum | Recommended |
| --- | --- | --- |
| CPU | x86-64 (64-bit) | 4+ cores |
| RAM | 4 GB | 8 GB+ (16 GB for gaming) |
| Disk | 25 GB | 64 GB+ SSD |
| Firmware | UEFI or legacy BIOS | UEFI |
| Graphics | Anything with a kernel DRM driver | AMD or Intel (Mesa), or NVIDIA with the proprietary tool set |

## 1. Verify the download

```bash
sha256sum -c sos-os-<version>-amd64.iso.sha256
```

## 2. Write a USB stick

> ⚠️ This **erases** the USB stick.

* **Fedora Media Writer** or **balenaEtcher** (Windows, macOS, Linux): choose
  "custom image" and select the ISO.
* **Rufus** (Windows): when asked, choose **"Write in DD Image mode"**.
* **Linux terminal:**

  ```bash
  lsblk -o NAME,SIZE,MODEL,TRAN          # identify the stick, e.g. sdb (TRAN = usb)
  sudo dd if=sos-os-<version>-amd64.iso of=/dev/sdX bs=4M status=progress conv=fsync
  ```

  Double-check `/dev/sdX`. `dd` overwrites whatever device you give it.

## 3. Boot the live system

Open your firmware's boot menu (often F12, F11, F8 or Esc) and choose the USB
stick. Pick **SOS OS Live** from the menu. The desktop starts automatically as
user `sos`. The password, if anything asks for one, is `live`. That's the
Debian live default, and it doesn't exist on an installed system.

### Secure Boot

SOS OS boots through Debian's Microsoft-signed `shim` and signed GRUB and
kernel, so it should boot with Secure Boot **enabled** on most PCs. If your
firmware refuses it:

1. Check that you're using the original ISO (verify the checksum).
2. Some firmware only trusts Microsoft's "Windows" CA. On those machines
   you'd have to enable the "third-party UEFI CA" option in firmware setup.
   SOS OS never changes firmware settings for you.

The optional NVIDIA tool set builds a DKMS kernel module. With Secure Boot on,
Debian asks you to create a Machine Owner Key and enrol it at the next boot
(MOK manager, a blue screen). Follow the prompts there; don't disable Secure
Boot.

## 4. Install to an internal drive

Double-click **Install SOS OS** on the desktop. The Calamares installer:

1. asks for language, location and keyboard,
2. shows the **partitioning** page. *Erase disk*, *Replace a partition*,
   *Install alongside* or *Manual*. Tick **Encrypt system** for LUKS full-disk
   encryption (you'll type the passphrase at every boot),
3. creates your user account,
4. shows a **summary of every change** to your disks. Nothing is written
   until you confirm by clicking **Install**.

> Back up your data first. Partitioning can always go wrong, whether it's a
> power cut, a failing disk or picking the wrong drive.

Restart and remove the USB stick when the installer says it's done. SOS Welcome
opens on first login.

## Persistent live USB

Persistence keeps files and settings on the USB stick between boots. Debian's
`live-boot` supports it through a second partition labelled `persistence`:

1. Write the ISO to the stick as above.
2. With a partition editor (KDE Partition Manager or GParted), create a new
   **ext4** partition in the free space after the image and label it
   `persistence`. ⚠️ Pick the USB stick, not your internal disk.
3. Mount it and create the configuration file:

   ```bash
   echo "/ union" | sudo tee /media/$USER/persistence/persistence.conf
   ```

4. At the boot menu, press `e` (GRUB) or `Tab` (ISOLINUX) and add
   ` persistence` to the end of the kernel line.

Persistence hasn't been tested with SOS OS yet (see [STATUS.md](STATUS.md)).

## Virtual machines

**QEMU/KVM:**

```bash
qemu-img create -f qcow2 sos.qcow2 40G
qemu-system-x86_64 -enable-kvm -m 4096 -smp 4 -cpu host \
  -bios /usr/share/ovmf/OVMF.fd \
  -device virtio-vga-gl -display gtk,gl=on \
  -drive file=sos.qcow2,if=virtio -cdrom sos-os-<version>-amd64.iso
```

**virt-manager / GNOME Boxes:** choose "Debian 13" as the OS type.

**VirtualBox 7:** Type *Linux*, Version *Debian (64-bit)*, 4 GB+ RAM, enable EFI,
graphics controller **VMSVGA** with 128 MB video memory.

**VMware Workstation/Player:** guest OS *Debian 12.x 64-bit* or later.
`open-vm-tools-desktop` is preinstalled.
