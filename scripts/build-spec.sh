#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-1.3}"
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

# Derive the section order from the table of contents in the main file.
SECTION_FILES=()
while IFS= read -r line; do
  SECTION_FILES+=("$line")
done < <(
  python3 - "$MAIN" "$VERSION" <<'PY'
import sys, pathlib, re

main_path = pathlib.Path(sys.argv[1])
version = sys.argv[2]
pattern = re.compile(rf"\(sections/v{re.escape(version)}/([^\)]+\.md)\)")

seen = set()
for match in pattern.finditer(main_path.read_text()):
    rel_path = match.group(1)
    if rel_path not in seen:
        seen.add(rel_path)
        print(rel_path)
PY
)

if [[ "${#SECTION_FILES[@]}" -eq 0 ]]; then
  echo "No sections referenced in the table of contents for version $VERSION" >&2
  exit 1
fi

for rel in "${SECTION_FILES[@]}"; do
  file="$SECTIONS_DIR/$rel"
  if [[ ! -f "$file" ]]; then
    echo "Referenced section '$file' not found" >&2
    exit 1
  fi
  printf '\n' >> "$OUTPUT"
  inject "$file" >> "$OUTPUT"
done

if [[ -x "$ROOT_DIR/scripts/prepare_mkdocs.py" ]]; then
  "$ROOT_DIR/scripts/prepare_mkdocs.py" >/dev/null || echo "Warning: failed to refresh MkDocs copies" >&2
fi

# Consistency gate for the active spec version only (frozen prior versions
# carry known-benign literal/canonical divergence and are immutable). Fails the
# build if an in-prose IDL copy drifts from its canonical source or a stale/
# retired profile identifier remains. See scripts/check_spec_consistency.py.
ACTIVE_VERSION="1.7"
if [[ "$VERSION" == "$ACTIVE_VERSION" && -x "$ROOT_DIR/scripts/check_spec_consistency.py" ]]; then
  "$ROOT_DIR/scripts/check_spec_consistency.py" "$VERSION"
fi

# Registry gate: every §3.3.2 registry row that names an IDL type / QoS profile
# must resolve. See scripts/check_registry.py.
if [[ "$VERSION" == "$ACTIVE_VERSION" && -x "$ROOT_DIR/scripts/check_registry.py" ]]; then
  "$ROOT_DIR/scripts/check_registry.py" "$VERSION"
fi

# Topic-construction gate (optional): constructs a CycloneDDS Topic for every
# generated Python type — catches binding-incompatible sequence bounds. Skips
# cleanly when idlc -l py / cyclonedds-python are unavailable.
if [[ "$VERSION" == "$ACTIVE_VERSION" && -x "$ROOT_DIR/scripts/check_topic_construct.py" ]]; then
  "$ROOT_DIR/scripts/check_topic_construct.py" "$VERSION"
fi
