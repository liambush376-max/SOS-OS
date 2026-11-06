#!/bin/bash
# Build the ISO inside a privileged Debian 13 container (Docker or Podman).
# Usage: scripts/build-in-container.sh [extra args for build-iso.sh]
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${SOS_BUILD_IMAGE:-docker.io/library/debian:trixie}"

if command -v docker >/dev/null 2>&1; then
    ENGINE=docker
elif command -v podman >/dev/null 2>&1; then
    ENGINE=podman
else
    echo "ERROR: install Docker or Podman to build SOS OS" >&2
    exit 1
fi

# live-build needs loop devices, mounts and device nodes, hence --privileged.
exec "$ENGINE" run --rm --privileged \
    -e HOST_UID="$(id -u)" -e HOST_GID="$(id -g)" \
    -v "$REPO:/src" -w /src \
    "$IMAGE" /src/scripts/build-iso.sh "$@"
