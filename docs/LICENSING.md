# Licensing

## SOS OS's own work

Everything in this repository (scripts, application source, QML, configuration,
and the SVG artwork in `branding/`) is © the SOS OS contributors and licensed
under the **GNU GPL v3.0 or later** (`LICENSE`).

The GPL fits because SOS OS is a distribution built mostly from GPL software
(Linux, KDE Plasma, Calamares), and it keeps derivatives of the SOS tools open.
The artwork is GPL as well, so it can ship inside the same package. Contact
the maintainers if you need different terms for the logo.

## Third-party software in the ISO

The ISO bundles unmodified Debian binary packages. Each keeps its own license,
listed in `/usr/share/doc/<package>/copyright` on the running system. The
image cleanup hook deliberately **keeps** those files. Source code for every
Debian package is available from `deb.debian.org` / `sources.debian.org`, which
meets the source-offer obligations of the GPL for unmodified packages. The
exact versions are listed in the `.packages` manifest published with each ISO.

The ISO includes firmware from Debian's `non-free-firmware` area (Wi-Fi, GPU and
audio firmware, CPU microcode). Debian redistributes it under the vendors'
redistribution licenses.

## Optional proprietary components (not in the ISO)

These are only installed when the user picks them in SOS Welcome:

* **Steam**: `steam-installer` from Debian contrib downloads the Steam client
  from Valve. The user must accept the Steam Subscriber Agreement in the GUI
  first.
* **NVIDIA driver**: from Debian `non-free`, under NVIDIA's license.

## Trademarks

"Debian" and "KDE" are trademarks of their respective owners. SOS OS isn't
endorsed by them, and it doesn't use their logos as its own branding.
