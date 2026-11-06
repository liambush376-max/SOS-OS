# iso/: live-build configuration

This directory is a [live-build](https://live-team.pages.debian.net/live-manual/)
configuration tree. Don't run `lb` here directly. Use
`scripts/build-iso.sh` (inside a Debian 13 container), which:

1. builds `sos-os-core_<version>_all.deb` and drops it into
   `config/packages.chroot/`,
2. renders the branding PNGs and copies the bootloader templates into
   `config/bootloaders/` with the SOS splash,
3. runs `lb clean`, `lb config` and `lb build`.

| Path | Purpose |
| --- | --- |
| `auto/config` | All `lb config` options (distribution, mirrors, boot options, ISO metadata) |
| `config/package-lists/*.list.chroot` | Packages installed into the live system |
| `config/hooks/live/*.hook.chroot` | Scripts run inside the chroot at the end of the chroot stage |

Generated paths (`config/packages.chroot`, `config/bootloaders`, `cache/`,
`chroot/`, `binary/`) are git-ignored.
