#!/bin/bash
# Assemble and build sos-os-core_<version>_all.deb from the repository tree.
# Usage: scripts/build-packages.sh <output-dir>
# Needs: dpkg-deb, rsvg-convert (librsvg2-bin), python3.
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$REPO/out}"
VERSION="$(tr -d '[:space:]' < "$REPO/VERSION")"
STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
ROOT="$STAGE/sos-os-core"

mkdir -p "$OUT" "$ROOT"

# --- Debian control files --------------------------------------------------
cp -a "$REPO/packages/sos-os-core/DEBIAN" "$ROOT/DEBIAN"
sed -i "s/@VERSION@/$VERSION/" "$ROOT/DEBIAN/control"
chmod 0755 "$ROOT/DEBIAN/preinst" "$ROOT/DEBIAN/postinst" "$ROOT/DEBIAN/postrm"

# --- System configuration (etc/, usr/) --------------------------------------
cp -a "$REPO/desktop/configuration/rootfs/." "$ROOT/"
sed -i "s/@VERSION@/$VERSION/g" "$ROOT/usr/lib/os-release" "$ROOT/etc/sos-release"

# --- Applications -----------------------------------------------------------
PY="$ROOT/usr/lib/sos-os/python"
mkdir -p "$PY" "$ROOT/usr/bin" "$ROOT/usr/share/applications" \
         "$ROOT/usr/libexec/sos-os" "$ROOT/usr/share/sos-os" \
         "$ROOT/usr/share/polkit-1/actions" "$ROOT/usr/lib/systemd/user" \
         "$ROOT/etc/xdg/autostart"
for app in "$REPO"/applications/*/; do
    for pkgdir in "$app"sos_*/; do
        [ -d "$pkgdir" ] && cp -a "$pkgdir" "$PY/"
    done
    [ -d "$app/bin" ] && install -m 0755 "$app"bin/* "$ROOT/usr/bin/"
    for d in "$app"*.desktop; do
        [ -f "$d" ] || continue
        case "$d" in
            *-autostart.desktop) install -m 0644 "$d" "$ROOT/etc/xdg/autostart/$(basename "${d%-autostart.desktop}").desktop" ;;
            *) install -m 0644 "$d" "$ROOT/usr/share/applications/" ;;
        esac
    done
    [ -d "$app/systemd" ] && install -m 0644 "$app"systemd/* "$ROOT/usr/lib/systemd/user/"
done
find "$PY" -name '__pycache__' -prune -exec rm -rf {} +
echo "$VERSION" > "$PY/sos_common/VERSION"

COMMON="$REPO/applications/sos-common"
install -m 0755 "$COMMON/libexec/sos-helper" "$ROOT/usr/libexec/sos-os/sos-helper"
install -m 0644 "$COMMON/data/org.sosos.helper.policy" "$ROOT/usr/share/polkit-1/actions/"
install -m 0644 "$COMMON/data/toolsets.json" "$ROOT/usr/share/sos-os/toolsets.json"
install -D -m 0644 "$REPO/installer/live/install-sos-os.desktop" "$ROOT/usr/share/sos-os/live/install-sos-os.desktop"

# --- Branding: icons, logo, wallpapers --------------------------------------
ICONS="$ROOT/usr/share/icons/hicolor"
install -D -m 0644 "$REPO/branding/logos/sos-logo.svg" "$ICONS/scalable/apps/sos-os.svg"
install -D -m 0644 "$REPO/branding/logos/sos-logo.svg" "$ICONS/scalable/apps/start-here-sos.svg"
for icon in "$REPO"/branding/icons/*.svg; do
    install -m 0644 "$icon" "$ICONS/scalable/apps/"
done
for size in 48 128 256; do
    mkdir -p "$ICONS/${size}x${size}/apps"
    rsvg-convert -w "$size" -h "$size" "$REPO/branding/logos/sos-logo.svg" -o "$ICONS/${size}x${size}/apps/sos-os.png"
done
install -D -m 0644 "$REPO/branding/logos/sos-logo.svg" "$ROOT/usr/share/sos-os/branding/sos-logo.svg"
rsvg-convert -w 512 -h 512 "$REPO/branding/logos/sos-logo.svg" -o "$ROOT/usr/share/sos-os/branding/sos-logo.png"

python3 - "$REPO/branding/wallpapers" "$ROOT/usr/share/wallpapers" <<'PYEOF'
import json, pathlib, subprocess, sys
src, dst = map(pathlib.Path, sys.argv[1:3])
meta = json.loads((src / "wallpapers.json").read_text())
for wp in meta["wallpapers"]:
    pkg = dst / wp["id"]
    img = pkg / "contents" / "images"
    img.mkdir(parents=True, exist_ok=True)
    for w, h in ((3840, 2160), (1920, 1080), (2560, 1600)):
        subprocess.run(["rsvg-convert", "-w", str(w), "-h", str(h),
                        str(src / wp["file"]), "-o", str(img / f"{w}x{h}.png")], check=True)
    (pkg / "metadata.json").write_text(json.dumps({
        "KPlugin": {"Id": wp["id"], "Name": wp["name"], "License": "GPL-3.0-or-later",
                    "Authors": [{"Name": "SOS OS Project"}]}
    }, indent=2) + "\n")
PYEOF

# --- Desktop: colour scheme, look-and-feel, widget, login/boot themes -------
install -D -m 0644 "$REPO/desktop/themes/color-schemes/SOSDark.colors" "$ROOT/usr/share/color-schemes/SOSDark.colors"
mkdir -p "$ROOT/usr/share/plasma/look-and-feel" "$ROOT/usr/share/plasma/plasmoids"
cp -a "$REPO/desktop/themes/look-and-feel/org.sosos.desktop" "$ROOT/usr/share/plasma/look-and-feel/"
cp -a "$REPO/desktop/widgets/org.sosos.quickstats" "$ROOT/usr/share/plasma/plasmoids/"
mkdir -p "$ROOT/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/previews" \
         "$ROOT/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/splash/images"
rsvg-convert -w 1600 -h 900 "$REPO/branding/wallpapers/sos-aurora.svg" \
    -o "$ROOT/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/previews/fullscreenpreview.png"
rsvg-convert -w 400 -h 225 "$REPO/branding/wallpapers/sos-aurora.svg" \
    -o "$ROOT/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/previews/preview.png"

mkdir -p "$ROOT/usr/share/sddm/themes" "$ROOT/usr/share/plymouth/themes" "$ROOT/usr/share/grub/themes"
cp -a "$REPO/desktop/sddm/sos" "$ROOT/usr/share/sddm/themes/"
rsvg-convert -w 1920 -h 1080 "$REPO/branding/wallpapers/sos-aurora.svg" -o "$ROOT/usr/share/sddm/themes/sos/background.png"
rsvg-convert -w 128 -h 128 "$REPO/branding/logos/sos-logo.svg" -o "$ROOT/usr/share/sddm/themes/sos/logo.png"

cp -a "$REPO/desktop/plymouth/sos" "$ROOT/usr/share/plymouth/themes/"
rsvg-convert -w 160 -h 160 "$REPO/branding/logos/sos-logo.svg" -o "$ROOT/usr/share/plymouth/themes/sos/logo.png"
rsvg-convert -w 12 -h 12 "$REPO/branding/icons/sos-dot.svg" -o "$ROOT/usr/share/plymouth/themes/sos/dot.png"

cp -a "$REPO/desktop/grub/sos" "$ROOT/usr/share/grub/themes/"
rsvg-convert -w 1920 -h 1080 "$REPO/branding/wallpapers/sos-boot.svg" -o "$ROOT/usr/share/grub/themes/sos/background.png"

# KDE splash screen uses the logo too
rsvg-convert -w 160 -h 160 "$REPO/branding/logos/sos-logo.svg" \
    -o "$ROOT/usr/share/plasma/look-and-feel/org.sosos.desktop/contents/splash/images/logo.png"

# --- Installer branding -----------------------------------------------------
mkdir -p "$ROOT/etc/calamares/branding"
cp -a "$REPO/installer/calamares/branding/sos" "$ROOT/etc/calamares/branding/"
rsvg-convert -w 128 -h 128 "$REPO/branding/logos/sos-logo.svg" -o "$ROOT/etc/calamares/branding/sos/logo.png"
rsvg-convert -w 800 -h 440 "$REPO/branding/wallpapers/sos-aurora.svg" -o "$ROOT/etc/calamares/branding/sos/welcome.png"
# Module configs stay Debian's (calamares-settings-debian owns them); the
# live hook only switches settings.conf to "branding: sos".

# --- Permissions & conffiles ------------------------------------------------
find "$ROOT" -path "$ROOT/DEBIAN" -prune -o -type d -exec chmod 0755 {} +
find "$ROOT" -path "$ROOT/DEBIAN" -prune -o -type f ! -perm -u+x -exec chmod 0644 {} +
chmod 0755 "$ROOT"/usr/bin/* "$ROOT"/usr/libexec/sos-os/*
( cd "$ROOT" && find etc -type f | sed 's|^|/|' | sort ) > "$ROOT/DEBIAN/conffiles"

INSTALLED_KB="$(du -sk --exclude=DEBIAN "$ROOT" | cut -f1)"
sed -i "s/@INSTALLED_SIZE@/$INSTALLED_KB/" "$ROOT/DEBIAN/control"

dpkg-deb --root-owner-group --build "$ROOT" "$OUT/sos-os-core_${VERSION}_all.deb"
echo "Built $OUT/sos-os-core_${VERSION}_all.deb"
