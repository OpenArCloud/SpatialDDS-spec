#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-1.2}"
OUTPUT="$ROOT_DIR/SpatialDDS-$VERSION-full.md"
MAIN="$ROOT_DIR/SpatialDDS-$VERSION.md"
SECTIONS_DIR="$ROOT_DIR/sections/v$VERSION"

if [[ ! -f "$MAIN" ]]; then
  echo "Main specification file '$MAIN' not found" >&2
  exit 1
fi

if [[ ! -d "$SECTIONS_DIR" ]]; then
  echo "Sections directory '$SECTIONS_DIR' not found" >&2
  exit 1
fi

inject() {
  local file="$1"
  python3 - "$file" "$ROOT_DIR" <<'PY'
import sys, pathlib, re
file_path = pathlib.Path(sys.argv[1])
root = pathlib.Path(sys.argv[2])
text = file_path.read_text()

def repl(match):
    path = root / match.group(1)
    return path.read_text()

print(re.sub(r'{{include:([^}]+)}}', repl, text), end='')
PY
}

# Start with the main specification file
inject "$MAIN" > "$OUTPUT"

# Append numbered sections in order
find "$SECTIONS_DIR" -maxdepth 1 -name '[0-9][0-9]-*.md' | sort | while read -r file; do
  printf '\n' >> "$OUTPUT"
  inject "$file" >> "$OUTPUT"

done

# Append the remaining core sections
for base in conclusion future-directions glossary references; do
  printf '\n' >> "$OUTPUT"
  inject "$SECTIONS_DIR/$base.md" >> "$OUTPUT"

done

# Append appendices
find "$SECTIONS_DIR" -maxdepth 1 -name 'appendix-*.md' | sort | while read -r file; do
  printf '\n' >> "$OUTPUT"
  inject "$file" >> "$OUTPUT"

done
