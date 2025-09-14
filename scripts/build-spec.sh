#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUTPUT="$ROOT_DIR/SpatialDDS-1.2-full.md"
MAIN="$ROOT_DIR/SpatialDDS-1.2.md"
SECTIONS_DIR="$ROOT_DIR/sections"

# Start with the main specification file
cat "$MAIN" > "$OUTPUT"

# Append numbered sections in order
find "$SECTIONS_DIR" -maxdepth 1 -name '[0-9][0-9]-*.md' | sort | while read -r file; do
  printf '\n' >> "$OUTPUT"
  cat "$file" >> "$OUTPUT"
done

# Append the remaining core sections
for base in conclusion future-directions glossary references; do
  printf '\n' >> "$OUTPUT"
  cat "$SECTIONS_DIR/$base.md" >> "$OUTPUT"
done

# Append appendices
find "$SECTIONS_DIR" -maxdepth 1 -name 'appendix-*.md' | sort | while read -r file; do
  printf '\n' >> "$OUTPUT"
  cat "$file" >> "$OUTPUT"
done
