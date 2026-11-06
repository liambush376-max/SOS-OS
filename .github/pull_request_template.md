## What does this change?

<!-- One or two sentences. Link the issue: Fixes #123 -->

## How was it tested?

- [ ] `./scripts/lint.sh`
- [ ] `python3 -m pytest tests`
- [ ] ISO built (CI or `./scripts/build-in-container.sh`)
- [ ] Booted in QEMU / VM (`./scripts/qemu-boot-test.sh` or manual)
- [ ] Tested on real hardware (describe below)

<!-- Be explicit about anything you could NOT test. -->

## Checklist

- [ ] No secrets, keys or tokens committed
- [ ] New artwork/fonts/binaries are redistributable and listed in `docs/LICENSING.md`
- [ ] `CHANGELOG.md` updated under *Unreleased*
- [ ] Disk-modifying code requires explicit user confirmation
