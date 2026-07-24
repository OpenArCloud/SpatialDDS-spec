#!/usr/bin/env python3
"""SpatialDDS spec consistency gate.

Two permanent build checks, run per spec version:

  1. IDL fence drift (universal): every literal ```idl block in
     sections/v<ver>/ that declares a `const string MODULE_ID` MUST match the
     canonical idl/v<ver>/*.idl file that owns that MODULE_ID, byte-for-byte
     (whitespace-trimmed at the ends). Hand-maintained copies of a canonical
     IDL file are how stale type lists and old version strings survive into a
     new-version doc; this fails the build if such a copy drifts. `{{include:}}`
     fences and deliberate excerpt snippets (no MODULE_ID) are exempt.

  2. Identifier hygiene (unified-minor versions, >= 1.7): no dual
     `name@MAJOR.MINOR` profile identifiers, and no stale `spatial.<x>/1.<k>`
     identifiers with k < the active minor. This is the C.15 version grep kept
     as a permanent gate.

Usage: check_spec_consistency.py [version]   (default: 1.7)
Exit status is nonzero if any check fails.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FENCE_OPEN = "`" * 3 + "idl"
FENCE_CLOSE = "`" * 3

# Versions from this minor onward use the single-identifier, unified-minor
# policy (§3.1 pre-adoption instability). Earlier versions legitimately use the
# dual @-form and mixed per-profile minors, so the identifier checks are skipped
# for them.
UNIFIED_MINOR_FROM = (1, 7)

MODULE_ID_RE = re.compile(r'const\s+string\s+MODULE_ID\s*=\s*"([^"]+)"')
DUAL_ID_RE = re.compile(r'\bspatial\.[A-Za-z0-9_.]+@[0-9]+\.[0-9]+')
SLASH_ID_RE = re.compile(r'\bspatial\.[A-Za-z0-9_.]+/1\.([0-9]+)')


def iter_idl_fences(md_text):
    """Yield (line_no, body) for each ```idl ... ``` block (1-indexed opener)."""
    lines = md_text.split("\n")
    i = 0
    while i < len(lines):
        if lines[i].strip() == FENCE_OPEN:
            body = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != FENCE_CLOSE:
                body.append(lines[j])
                j += 1
            yield i + 1, "\n".join(body)
            i = j
        i += 1


def load_canonical(idl_dir):
    """Map MODULE_ID string -> (filename, trimmed content)."""
    by_module = {}
    for dirpath, _, files in os.walk(idl_dir):
        for fn in sorted(files):
            if not fn.endswith(".idl"):
                continue
            path = os.path.join(dirpath, fn)
            text = open(path, encoding="utf-8").read()
            m = MODULE_ID_RE.search(text)
            if m:
                rel = os.path.relpath(path, ROOT)
                by_module[m.group(1)] = (rel, text.strip())
    return by_module


def check_fence_drift(sections_dir, idl_dir):
    failures = []
    canonical = load_canonical(idl_dir)
    for fn in sorted(os.listdir(sections_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(sections_dir, fn)
        text = open(path, encoding="utf-8").read()
        for line_no, body in iter_idl_fences(text):
            stripped = body.strip()
            if stripped.startswith("{{include:"):
                continue  # build expands includes; nothing to drift
            m = MODULE_ID_RE.search(body)
            if not m:
                continue  # excerpt / abridged snippet, not a full-module copy
            module_id = m.group(1)
            loc = f"sections/{os.path.basename(sections_dir)}/{fn}:{line_no}"
            if module_id not in canonical:
                failures.append(
                    f"{loc}: literal IDL block declares MODULE_ID "
                    f'"{module_id}" with no canonical file under {os.path.relpath(idl_dir, ROOT)}'
                )
                continue
            can_rel, can_body = canonical[module_id]
            if stripped != can_body:
                failures.append(
                    f"{loc}: literal IDL block for {module_id} has DRIFTED from "
                    f"canonical {can_rel}. Re-sync the block or convert it to "
                    f"{{{{include:{can_rel}}}}}."
                )
    return failures


def check_identifiers(sections_dir, minor):
    failures = []
    for fn in sorted(os.listdir(sections_dir)):
        if not fn.endswith(".md"):
            continue
        path = os.path.join(sections_dir, fn)
        for i, line in enumerate(open(path, encoding="utf-8"), 1):
            if "{{include:" in line:
                continue
            loc = f"sections/{os.path.basename(sections_dir)}/{fn}:{i}"
            for m in DUAL_ID_RE.finditer(line):
                failures.append(
                    f"{loc}: retired dual identifier form '{m.group(0)}' "
                    f"(use spatial.<profile>/MAJOR.MINOR)"
                )
            for m in SLASH_ID_RE.finditer(line):
                if int(m.group(1)) < minor:
                    failures.append(
                        f"{loc}: stale identifier '{m.group(0)}' "
                        f"(active minor is 1.{minor})"
                    )
    return failures


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.7"
    try:
        major, minor = (int(x) for x in version.split("."))
    except ValueError:
        print(f"error: bad version '{version}' (expected e.g. 1.7)", file=sys.stderr)
        return 2

    sections_dir = os.path.join(ROOT, "sections", f"v{version}")
    idl_dir = os.path.join(ROOT, "idl", f"v{version}")
    for d in (sections_dir, idl_dir):
        if not os.path.isdir(d):
            print(f"error: missing directory {d}", file=sys.stderr)
            return 2

    failures = check_fence_drift(sections_dir, idl_dir)
    if (major, minor) >= UNIFIED_MINOR_FROM:
        failures += check_identifiers(sections_dir, minor)

    if failures:
        print(f"Spec consistency FAILED for v{version} ({len(failures)} issue(s)):\n")
        for f in failures:
            print(f"  - {f}")
        return 1
    print(f"Spec consistency OK for v{version} (IDL fences match canonical; identifiers clean).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
