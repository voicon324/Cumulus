#!/usr/bin/env bash
# Cumulus repository-local installer.
# Source: https://github.com/voicon324/Cumulus
set -euo pipefail

REPO="${CUMULUS_REPO:-voicon324/Cumulus}"
REF="${CUMULUS_REF:-main}"
TARGET_DIR="${CUMULUS_TARGET:-$PWD}"
TMP_DIR="$(mktemp -d)"
cleanup() { rm -rf "$TMP_DIR"; }
trap cleanup EXIT

need() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "ERROR: '$1' is required but was not found." >&2
    exit 1
  }
}

need curl
need tar
need python3

ARCHIVE_URL="https://github.com/${REPO}/archive/${REF}.tar.gz"
printf 'Cumulus: downloading %s@%s
' "$REPO" "$REF"
curl -fsSL "$ARCHIVE_URL" -o "$TMP_DIR/cumulus.tgz"
tar -xzf "$TMP_DIR/cumulus.tgz" -C "$TMP_DIR"

SOURCE_DIR="$(find "$TMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
if [[ -z "$SOURCE_DIR" || ! -f "$SOURCE_DIR/scripts/install-repo.sh" ]]; then
  echo "ERROR: downloaded package is missing scripts/install-repo.sh" >&2
  exit 1
fi

exec bash "$SOURCE_DIR/scripts/install-repo.sh" --repo "$TARGET_DIR" "$@"
