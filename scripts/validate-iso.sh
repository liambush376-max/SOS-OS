#!/bin/bash
# Structural validation of a built SOS OS ISO (no booting).
# Usage: scripts/validate-iso.sh out/sos-os-<version>-amd64.iso
# Needs: xorriso, squashfs-tools. Exits non-zero on the first failed check.
set -euo pipefail

ISO="${1:?usage: validate-iso.sh <iso>}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
fail=0
pass() { printf '  \033[32mPASS\033[0m %s\n' "$*"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$*"; fail=1; }
warn() { printf '  \033[33mWARN\033[0m %s\n' "$*"; }

echo "Validating $ISO"
[ -f "$ISO" ] || { echo "ISO not found"; exit 1; }

size=$(stat -c %s "$ISO")
mib=$((size / 1024 / 1024))
if [ "$size" -lt $((700 * 1024 * 1024)) ]; then bad "size ${mib} MiB is suspiciously small"; else pass "size ${mib} MiB"; fi
if [ "$size" -gt $((2 * 1024 * 1024 * 1024 - 1)) ]; then
    warn "ISO exceeds 2 GiB; the release workflow will split it into parts for GitHub Releases"
fi
if [ -f "$ISO.sha256" ]; then
    (cd "$(dirname "$ISO")" && sha256sum -c --quiet "$(basename "$ISO").sha256") && pass "sha256 matches" || bad "sha256 mismatch"
fi

# Hybrid MBR + GPT/EFI boot records
report="$(xorriso -indev "$ISO" -report_el_torito plain 2>/dev/null || true)"
grep -q "El Torito boot img.*BIOS" <<<"$report" && pass "El Torito BIOS boot image" || bad "no BIOS El Torito entry"
grep -q "El Torito boot img.*UEFI" <<<"$report" && pass "El Torito UEFI boot image" || bad "no UEFI El Torito entry"

listing="$WORK/files.txt"
xorriso -indev "$ISO" -find / -type f 2>/dev/null | tr -d "'" > "$listing"
for f in /live/filesystem.squashfs /boot/grub/grub.cfg /isolinux/isolinux.bin /EFI/boot/bootx64.efi; do
    # EFI paths are case-insensitive on FAT; match case-insensitively everywhere
    grep -qix "$f" "$listing" && pass "contains $f" || bad "missing $f"
done
grep -q '^/live/vmlinuz' "$listing" && pass "contains kernel" || bad "missing /live/vmlinuz*"
grep -q '^/live/initrd' "$listing" && pass "contains initrd" || bad "missing /live/initrd*"

# Bootloader configuration
# live-build splits the GRUB menu over several *.cfg files; check them all.
xorriso -osirrox on -indev "$ISO" -extract /boot/grub "$WORK/grub" >/dev/null 2>&1 || true
if [ -f "$WORK/grub/grub.cfg" ]; then
    grep -rq --include='*.cfg' 'boot=live' "$WORK/grub" && pass "GRUB entries boot with boot=live" || bad "GRUB config lacks boot=live"
    grep -rq --include='*.cfg' 'live-config.username=sos' "$WORK/grub" && pass "GRUB sets live user 'sos'" || bad "GRUB config lacks live-config.username=sos"
    grep -rq --include='*.cfg' 'SOS OS' "$WORK/grub" && pass "GRUB menu branded" || warn "GRUB menu not branded"
else
    bad "could not extract /boot/grub/grub.cfg"
fi

echo "Validating root filesystem contents"
if command -v python3 >/dev/null && python3 -c 'import pytest' 2>/dev/null; then
    xorriso -osirrox on -indev "$ISO" -extract /live/filesystem.squashfs "$WORK/fs.squashfs" >/dev/null 2>&1
    SOS_SQUASHFS="$WORK/fs.squashfs" SOS_PACKAGES="${ISO%.iso}.packages" \
        python3 -m pytest -q "$REPO/tests/iso" || fail=1
else
    warn "python3-pytest not installed: skipping filesystem tests"
fi

[ "$fail" -eq 0 ] && echo "ISO validation passed" || { echo "ISO validation FAILED"; exit 1; }
