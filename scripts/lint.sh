#!/bin/bash
# Run all static checks locally (same as .github/workflows/lint.yml).
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO"
rc=0

echo "== shellcheck"
mapfile -t shells < <(
    { find scripts iso/auto iso/config/hooks desktop/configuration/rootfs/usr/libexec packages/*/DEBIAN applications/*/bin -type f; } |
    while read -r f; do head -n1 "$f" | grep -qE '^#!.*\b(ba)?sh\b' && echo "$f"; done
)
if command -v shellcheck >/dev/null; then
    shellcheck -x -S warning "${shells[@]}" || rc=1
else
    echo "shellcheck not installed, skipping"
fi

echo "== ruff"
if command -v ruff >/dev/null; then
    ruff check applications tests desktop/configuration/rootfs/usr/bin/sos-quickstats applications/sos-common/libexec/sos-helper || rc=1
else
    echo "ruff not installed (pip install ruff), skipping"
fi

echo "== python syntax"
python3 -m py_compile applications/sos-common/libexec/sos-helper desktop/configuration/rootfs/usr/bin/sos-quickstats || rc=1
find applications tests -name '*.py' -print0 | xargs -0 python3 -m py_compile || rc=1

echo "== desktop files"
if command -v desktop-file-validate >/dev/null; then
    for d in applications/*/*.desktop installer/live/*.desktop; do desktop-file-validate "$d" || rc=1; done
else
    echo "desktop-file-validate not installed, skipping"
fi

exit $rc
