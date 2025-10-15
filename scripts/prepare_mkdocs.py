#!/usr/bin/env python3
"""Generate MkDocs-friendly copies of the spec with includes expanded."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTIONS_SRC = ROOT / "sections"
DOCS_DST = ROOT / "mkdocs_docs"
STATIC_SRC = ROOT / "docs_static"

INCLUDE_RE = re.compile(r"{{include:([^}]+)}}")


def resolve_includes(text: str) -> str:
    """Inline {{include:path}} blocks with file contents."""

    def replacer(match: re.Match[str]) -> str:
        rel_path = match.group(1).strip()
        target = ROOT / rel_path
        if not target.exists():
            raise SystemExit(f"Included file not found: {rel_path}")
        return target.read_text(encoding="utf-8")

    return INCLUDE_RE.sub(replacer, text)


def write_processed(src: Path, dest: Path, *, rewrite_version: str | None = None) -> None:
    text = src.read_text(encoding="utf-8")
    text = resolve_includes(text)

    if rewrite_version:
        token = f"sections/v{rewrite_version}/"
        text = text.replace(token, f"v{rewrite_version}/")

    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    rel = dest.relative_to(ROOT)
    print(f"Wrote {rel}")


def clean_destination() -> None:
    if DOCS_DST.exists():
        shutil.rmtree(DOCS_DST)
    DOCS_DST.mkdir(parents=True)


def copy_static_assets() -> None:
    if not STATIC_SRC.exists():
        return

    for path in STATIC_SRC.rglob("*"):
        if path.is_dir():
            continue

        relative = path.relative_to(STATIC_SRC)
        dest = DOCS_DST / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        rel = dest.relative_to(ROOT)
        print(f"Copied {rel}")


def main() -> None:
    if not SECTIONS_SRC.exists():
        raise SystemExit("sections/ directory not found")

    clean_destination()

    index_src = SECTIONS_SRC / "index.md"
    if index_src.exists():
        write_processed(index_src, DOCS_DST / "index.md")

    versions: list[str] = []

    for entry in sorted(SECTIONS_SRC.iterdir()):
        if not entry.is_dir() or not entry.name.startswith("v"):
            continue
        version = entry.name.removeprefix("v")
        versions.append(version)

        for md_path in sorted(entry.glob("*.md")):
            relative = entry.name + "/" + md_path.name
            dest = DOCS_DST / relative
            write_processed(md_path, dest)

    if not versions:
        raise SystemExit("No versioned section directories found under sections/.")

    for version in versions:
        src = ROOT / f"SpatialDDS-{version}-full.md"
        if not src.exists():
            print(f"Skipping SpatialDDS-{version}-full.md (source missing)")
            continue
        dest = DOCS_DST / f"SpatialDDS-{version}-full.md"
        write_processed(src, dest, rewrite_version=version)

    copy_static_assets()


if __name__ == "__main__":
    main()
