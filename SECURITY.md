# Security policy

## Reporting a vulnerability

Please report vulnerabilities privately through **GitHub → Security → Report a
vulnerability** (private vulnerability reporting) on this repository. Don't
open a public issue.

We aim to acknowledge reports within 7 days.

Vulnerabilities in Debian packages (the kernel, Plasma, Firefox and so on)
should go to the [Debian security team](https://www.debian.org/security/). SOS
OS picks up their fixes from `security.debian.org`.

## Secure defaults in SOS OS

* All packages come from the signed Debian archive, and APT verifies the
  signatures. SOS OS doesn't disable signature checks.
* The `ufw` firewall is on, with incoming connections denied by default. No SSH
  server or other listening network service is installed by default.
* No credentials are hardcoded into the installed system. The live session uses
  the standard Debian live user (password `live`). That user exists only in the
  live session, and the installer creates your own account in its place.
* Privileged actions go through `/usr/libexec/sos-os/sos-helper`. It accepts a
  fixed allowlist of actions, and polkit requires administrator
  authentication.
* Secure Boot is supported through Debian's signed shim and GRUB, and SOS OS
  never turns it off. The optional NVIDIA tool set warns that its DKMS modules
  need a MOK key enrolled.
* Full-disk encryption (LUKS) is available in the installer.
* GitHub Actions workflows get least-privilege `permissions:`, and third-party
  actions are pinned to full commit SHAs.

## Supported versions

Until v1.0.0, only the latest pre-release receives fixes.
