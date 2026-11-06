#!/bin/bash
# Run an SOS application straight from the source tree (development).
# Usage: scripts/run-app.sh sos-monitor [--self-test]
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
app="${1:?usage: run-app.sh <sos-settings|sos-monitor|sos-updater|sos-welcome|sos-devhub> [args]}"
shift
PYTHONPATH="$(printf '%s:' "$REPO"/applications/*/ | sed 's/:$//')"
export PYTHONPATH
exec python3 -m "${app//-/_}" "$@"
