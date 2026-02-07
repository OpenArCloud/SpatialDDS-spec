#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IDL_DIR="$ROOT_DIR/idl/v1.5"
OUT_DIR="${TMPDIR:-/tmp}/spatialdds_idlc_out/v1.5"

if ! command -v idlc >/dev/null 2>&1; then
  echo "idlc not found in PATH. Install Cyclone DDS idlc and retry." >&2
  exit 127
fi

mkdir -p "$OUT_DIR"

errors=0
for file in "$IDL_DIR"/*.idl; do
  echo "[idlc] $(basename "$file")"
  if ! idlc -I "$IDL_DIR" -o "$OUT_DIR" "$file"; then
    errors=1
  fi
done

if [[ $errors -ne 0 ]]; then
  echo "IDL validation failed for v1.5." >&2
  exit 1
fi

echo "IDL validation succeeded for v1.5."
