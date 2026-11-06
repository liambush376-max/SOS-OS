#!/bin/bash
# Boot the ISO in QEMU (headless) and wait until the live system reports that
# graphical.target is reached and the display manager is running.
#
# Usage: scripts/qemu-boot-test.sh <iso> [timeout-seconds]
#
# The kernel and initrd are extracted from the ISO and booted directly so a
# serial console can be added to the command line; the root filesystem still
# comes from the ISO (attached as a CD-ROM) exactly as on real hardware.
# sos-boot-report.service prints SOS-OS-BOOT-OK / SOS-OS-BOOT-FAIL to the
# console. Firmware boot paths (GRUB/ISOLINUX) are checked separately by
# validate-iso.sh.
set -euo pipefail

ISO="${1:?usage: qemu-boot-test.sh <iso> [timeout]}"
WORK="$(mktemp -d)"
LOG="${SOS_BOOT_LOG:-$PWD/out/qemu-serial.log}"
mkdir -p "$(dirname "$LOG")"
: > "$LOG"

if [ -w /dev/kvm ]; then
    ACCEL=(-enable-kvm -cpu host)
    TIMEOUT="${2:-900}"
    echo "Using KVM acceleration"
else
    ACCEL=(-cpu max)
    TIMEOUT="${2:-2700}"
    echo "KVM not available: using TCG emulation (slow)"
fi

cleanup() {
    [ -n "${QPID:-}" ] && kill "$QPID" 2>/dev/null || true
    chmod -R u+w "$WORK" 2>/dev/null || true
    rm -rf "$WORK"
}
trap cleanup EXIT

kernel="$(xorriso -indev "$ISO" -find /live -name 'vmlinuz*' 2>/dev/null | tr -d "'" | head -n1)"
initrd="$(xorriso -indev "$ISO" -find /live -name 'initrd.img*' 2>/dev/null | tr -d "'" | head -n1)"
[ -n "$kernel" ] && [ -n "$initrd" ] || { echo "kernel/initrd not found in ISO"; exit 1; }
xorriso -osirrox on -indev "$ISO" -extract "$kernel" "$WORK/vmlinuz" -extract "$initrd" "$WORK/initrd" >/dev/null 2>&1

APPEND="boot=live components live-config.username=sos live-config.hostname=sos-os \
console=tty0 console=ttyS0,115200n8 systemd.show_status=1 plymouth.enable=0"

qemu-system-x86_64 "${ACCEL[@]}" -m 4096 -smp 2 \
    -machine q35 -vga std -display none \
    -cdrom "$ISO" -kernel "$WORK/vmlinuz" -initrd "$WORK/initrd" -append "$APPEND" \
    -netdev user,id=n0 -device virtio-net-pci,netdev=n0 \
    -serial "file:$LOG" -no-reboot &
QPID=$!

echo "QEMU pid $QPID, waiting up to ${TIMEOUT}s for SOS-OS-BOOT marker (log: $LOG)"
start=$(date +%s)
while :; do
    if grep -q 'SOS-OS-BOOT-OK' "$LOG"; then
        grep 'SOS-OS-BOOT-OK' "$LOG" | head -n1
        echo "BOOT TEST PASSED in $(( $(date +%s) - start ))s"
        exit 0
    fi
    if grep -q 'SOS-OS-BOOT-FAIL' "$LOG"; then
        grep 'SOS-OS-BOOT-FAIL' "$LOG" | head -n1
        echo "BOOT TEST FAILED: reached graphical.target but the display manager is not active"
        exit 1
    fi
    if grep -qE 'Kernel panic|end Kernel panic|Unable to find a medium containing a live file system' "$LOG"; then
        tail -n 40 "$LOG"
        echo "BOOT TEST FAILED: fatal boot error"
        exit 1
    fi
    if ! kill -0 "$QPID" 2>/dev/null; then
        tail -n 40 "$LOG"
        echo "BOOT TEST FAILED: QEMU exited early"
        exit 1
    fi
    if [ $(( $(date +%s) - start )) -ge "$TIMEOUT" ]; then
        tail -n 60 "$LOG"
        echo "BOOT TEST FAILED: timeout after ${TIMEOUT}s"
        exit 1
    fi
    sleep 5
done
