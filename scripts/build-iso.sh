#!/bin/bash
# Build the SOS OS live ISO. Must run as root on Debian 13 (trixie), normally
# inside a privileged container started by scripts/build-in-container.sh or
# the GitHub Actions workflow.
#
# Output: out/sos-os-<version>-amd64.iso (+ .sha256, .packages)
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="$REPO/out"
ISO_DIR="$REPO/iso"
SOS_VERSION="$(tr -d '[:space:]' < "$REPO/VERSION")"
export SOS_VERSION

log() { printf '\n\033[1;35m==> %s\033[0m\n' "$*"; }
die() { printf '\033[1;31mERROR: %s\033[0m\n' "$*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "build-iso.sh must run as root (use scripts/build-in-container.sh)"
. /etc/os-release
[ "${VERSION_CODENAME:-}" = "trixie" ] || die "build host must be Debian 13 trixie, found '${PRETTY_NAME:-unknown}'"
[[ "$SOS_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.]+)?$ ]] || die "VERSION '$SOS_VERSION' is not semver"

log "SOS OS $SOS_VERSION: preparing build host"
# The container image only enables 'main'; the ISO also needs contrib and
# non-free-firmware, so enable them here for the package preflight.
if [ -f /etc/apt/sources.list.d/debian.sources ]; then
    sed -i 's/^Components: main$/Components: main contrib non-free-firmware/' \
        /etc/apt/sources.list.d/debian.sources
fi
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq --no-install-recommends \
    live-build debootstrap dpkg-dev librsvg2-bin xorriso squashfs-tools \
    mtools dosfstools isolinux syslinux-common grub-efi-amd64-bin grub-pc-bin \
    ca-certificates python3 >/dev/null

log "Preflight: checking that every listed package exists in trixie"
missing=()
while read -r pkg; do
    apt-cache show "$pkg" >/dev/null 2>&1 || missing+=("$pkg")
done < <(grep -hv '^\s*#' "$ISO_DIR"/config/package-lists/*.list.chroot | awk 'NF {print $1}' | sort -u)
if [ "${#missing[@]}" -gt 0 ]; then
    die "packages not found in Debian trixie: ${missing[*]}"
fi

log "Building sos-os-core package"
mkdir -p "$OUT"
"$REPO/scripts/build-packages.sh" "$OUT"
rm -rf "$ISO_DIR/config/packages.chroot"
mkdir -p "$ISO_DIR/config/packages.chroot"
cp "$OUT"/sos-os-core_"$SOS_VERSION"_all.deb "$ISO_DIR/config/packages.chroot/"

log "Preparing branded bootloader templates"
rm -rf "$ISO_DIR/config/bootloaders"
mkdir -p "$ISO_DIR/config/bootloaders"
for bl in grub-pc isolinux; do
    cp -a "/usr/share/live/build/bootloaders/$bl" "$ISO_DIR/config/bootloaders/"
done
rsvg-convert -w 800 -h 600 "$REPO/branding/wallpapers/sos-boot.svg" \
    -o "$ISO_DIR/config/bootloaders/grub-pc/splash.png"
rsvg-convert -w 640 -h 480 "$REPO/branding/wallpapers/sos-boot.svg" \
    -o "$ISO_DIR/config/bootloaders/isolinux/splash.png"
# Menu titles: "Debian GNU/Linux Live" -> "SOS OS Live"
{ grep -rlZ 'Live system' "$ISO_DIR/config/bootloaders" || true; } \
    | xargs -0 -r sed -i 's/Live system/SOS OS Live/g'

log "Running live-build"
cd "$ISO_DIR"
lb clean
lb config
lb build

iso_src="$(ls -1 "$ISO_DIR"/sos-os-"$SOS_VERSION"*.iso 2>/dev/null | head -n1 || true)"
[ -n "$iso_src" ] && [ -f "$iso_src" ] || die "live-build finished without producing an ISO; see iso/build.log"

iso_out="$OUT/sos-os-$SOS_VERSION-amd64.iso"
mv "$iso_src" "$iso_out"
pkg_list="$(ls -1 "$ISO_DIR"/sos-os-"$SOS_VERSION"*.packages 2>/dev/null | head -n1 || true)"
[ -n "$pkg_list" ] && cp "$pkg_list" "$OUT/sos-os-$SOS_VERSION-amd64.packages"
cp "$ISO_DIR/build.log" "$OUT/build.log" 2>/dev/null || true

cd "$OUT"
sha256sum "$(basename "$iso_out")" > "$(basename "$iso_out").sha256"

if [ -n "${HOST_UID:-}" ]; then
    chown -R "$HOST_UID:${HOST_GID:-$HOST_UID}" "$OUT" "$ISO_DIR/cache" 2>/dev/null || true
fi

log "Done: $iso_out ($(du -h "$iso_out" | cut -f1))"
cat "$iso_out.sha256"
