# Roadmap and release criteria

Every release is published as a **pre-release** until v1.0.0.

| Version | Theme | Exit criteria |
| --- | --- | --- |
| v0.1.0 | First bootable ISO | CI builds the ISO; `validate-iso.sh` and the QEMU boot test pass; boots in at least one real UEFI machine |
| v0.2.0 | Custom desktop design | SOS Plasma desktop theme (panel/launcher SVGs), window decoration with rounded corners, lock screen theme, screenshots in README |
| v0.3.0 | Core applications | All five apps verified on SOS; signed SOS APT repository so `sos-os-core` updates without a new ISO; translations framework |
| v0.4.0 | Installer integration | Calamares tested: erase, encrypt, alongside Windows, manual; post-install cleanup of live-only packages verified; OEM mode |
| v0.5.0 | Hardware compatibility | Tested matrix covering AMD, Intel and NVIDIA GPUs, Wi-Fi chipsets, laptops (suspend, brightness, battery), controllers; published in release notes |
| v0.9.0 | Beta | Feature freeze; no known data-loss bugs; upgrade path 0.9 → 1.0 documented and tested |
| v1.0.0 | Stable | Two weeks without release-blocking bugs; Secure Boot tested on 3+ machines; documentation complete; security review of helper and update path |

## v1.0.0 (stable)

A stable release requires all of the following:

* every item in the manual checklist in [TESTING.md](TESTING.md) passes,
* `docs/STATUS.md` has no "unverified" items among advertised features,
* no open issues labelled `release-blocker`,
* the ISO is reproducible from the tagged commit through CI.
