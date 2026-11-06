# Maintainer guide

## One-time GitHub setup

1. **Branch protection** on `main`: require pull requests, one approval, and
   the `Lint`, `Tests` checks to pass. Disallow force pushes.
2. **Environment `release`** (Settings → Environments): add required
   reviewers. `release.yml` pauses for approval before publishing anything.
3. **Private vulnerability reporting** (Settings → Security): enable.
4. **Actions permissions** (Settings → Actions → General): set "Workflow
   permissions" to *Read repository contents*. Workflows request `contents:
   write` only in the release job.
5. **Milestones**: create `v0.1.0`, `v0.2.0`, `v0.3.0`, `v0.4.0`, `v0.5.0`,
   `v0.9.0`, `v1.0.0` (see [ROADMAP.md](ROADMAP.md)). With the GitHub CLI:

   ```bash
   for m in v0.1.0 v0.2.0 v0.3.0 v0.4.0 v0.5.0 v0.9.0 v1.0.0; do
     gh api repos/{owner}/{repo}/milestones -f title="$m"
   done
   ```

No repository secrets are needed today. Add one only when a step really
requires a credential (for example uploading to external mirror storage), and
scope it to the `release` environment.

## Cutting a release

1. Make sure `main` is green, including the **QEMU boot test**.
2. Do the manual checklist in [TESTING.md](TESTING.md) for anything the
   release claims to support.
3. Bump `VERSION`, move *Unreleased* entries in `CHANGELOG.md` under the new
   version, and write `docs/release-notes/v<version>.md` (copy `TEMPLATE.md`).
   Fill in **known issues** and the **hardware compatibility** table honestly.
4. Merge, then tag from `main`:

   ```bash
   git tag -s v0.1.0 -m "SOS OS 0.1.0"
   git push origin v0.1.0
   ```

5. Approve the `release` environment deployment when the build and boot test
   have passed.

Versions `< 1.0.0` and anything with a `-suffix` are always published as
**pre-releases**. A stable release means tagging `v1.0.0` or later with no
suffix, and only once the [v1.0.0 criteria](ROADMAP.md#v100-stable) are met.

## Updating pinned actions

Workflows pin third-party actions to full commit SHAs. Dependabot opens PRs
for new versions. Check the action's release notes before merging. To look up
a SHA by hand:

```bash
git ls-remote https://github.com/actions/checkout refs/tags/v7.0.1
```

## Debugging a failed ISO build

* The **summary** of the failed run shows the last 80 lines of `build.log`.
* The **build-log** artifact has the full live-build log.
* "packages not found in Debian trixie" comes from the preflight step. A
  package was renamed or removed; fix `iso/config/package-lists/`.
* Reproduce locally with `./scripts/build-in-container.sh`. Delete `iso/cache`
  if you suspect a corrupt cache.
