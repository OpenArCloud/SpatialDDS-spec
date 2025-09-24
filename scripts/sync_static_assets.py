#!/usr/bin/env python3
"""Copy IDL and manifest directories into the docs tree for publishing.

MkDocs only publishes files that live under ``docs/``. The canonical copies
of the SpatialDDS IDL definitions and manifest examples live at the repository
root so that other tooling (and the combined specification generator) can
reference them.  To make those files available on the published documentation
site we mirror the directories into ``docs/`` before building the site.

Run this script whenever the IDL or manifest files change, or before publishing
updated documentation.
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs"
DIRECTORIES = ("idl", "manifests")


def copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the directories that would be copied without modifying the docs tree.",
    )
    args = parser.parse_args()

    for directory in DIRECTORIES:
        src = PROJECT_ROOT / directory
        dst = DOCS_ROOT / directory
        if not src.exists():
            raise SystemExit(f"Expected source directory {src} to exist")
        if args.dry_run:
            print(f"Would copy {src} -> {dst}")
        else:
            copy_tree(src, dst)
            print(f"Copied {src} -> {dst}")


if __name__ == "__main__":
    main()
