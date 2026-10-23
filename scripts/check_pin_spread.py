#!/usr/bin/env python3
"""check_pin_spread.py -- report how far each downstream consumer's declared
SpatialDDS-spec pin lags behind spec `main` HEAD.

Reporting instrument only: it reads each consumer's recorded spec pin (the
SpatialDDS-spec commit it was generated/vendored against) and computes the
commit distance from that pin to spec `main` HEAD using the local spec checkout.

Run with no args:  python3 scripts/check_pin_spread.py
"""

import re
import subprocess
import sys
from pathlib import Path

# Local spec checkout whose `main` HEAD is the reference point.
SPEC_REPO = Path("/Users/fiberhog/AGENT_DEV/OARC/SpatialDDS-spec")
# Parent dir holding the consumer repos as siblings.
OARC = Path("/Users/fiberhog/AGENT_DEV/OARC")

# Per-consumer rule: (repo dir, file relative to repo, regex capturing the SHA).
# Each regex has one group: the declared spec pin (7-40 hex chars).
CONSUMERS = [
    (
        "SpatialDDS-demo",
        "ar_demo/SPEC_COMPLIANCE.md",
        r"spec commit `([0-9a-f]{7,40})`",
    ),
    (
        "spatialdds-ros",
        "spatialdds_idl18/PROVENANCE.md",
        r"IDL source.*?at `([0-9a-f]{7,40})`",
    ),
    (
        "spatialdds-scenescape",
        "idl/PROVENANCE",
        r"(?m)^\s*commit\s*=\s*([0-9a-f]{7,40})",
    ),
    (
        "openvps",
        "maplocalizer/server/vendor/spatialdds_idl18/__init__.py",
        r"Provenance:\s*SpatialDDS-spec\s+([0-9a-f]{7,40})",
    ),
    (
        "spatialdds-web",
        "webjson/PROVENANCE",
        r"(?m)^\s*artifacts_commit\s*=\s*([0-9a-f]{7,40})",
    ),
]


def read_pin(repo, rel, pattern):
    """Return (pin, source_label, line_no) or (None, error_label, None)."""
    path = OARC / repo / rel
    if not path.exists():
        return None, f"MISSING FILE: {path}", None
    text = path.read_text(encoding="utf-8", errors="replace")
    m = re.search(pattern, text)
    if not m:
        return None, f"NO MATCH in {path}", None
    pin = m.group(1)
    line_no = text.count("\n", 0, m.start(1)) + 1
    return pin, f"{repo}/{rel}:{line_no}", line_no


def distance_behind(pin):
    """Commits on spec main HEAD not reachable from pin, or an 'unknown' note."""
    # Confirm the pin exists in the spec repo.
    r = subprocess.run(
        ["git", "-C", str(SPEC_REPO), "cat-file", "-e", f"{pin}^{{commit}}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return "unknown (pin not in spec repo)"
    r = subprocess.run(
        ["git", "-C", str(SPEC_REPO), "rev-list", "--count", f"{pin}..HEAD"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        err = (r.stderr or r.stdout).strip().replace("\n", " ")
        return f"unknown ({err or 'rev-list failed'})"
    count = r.stdout.strip()
    # If pin is not an ancestor of HEAD, also report divergence for clarity.
    anc = subprocess.run(
        ["git", "-C", str(SPEC_REPO), "merge-base", "--is-ancestor", pin, "HEAD"],
        capture_output=True, text=True,
    )
    if anc.returncode != 0:
        return f"{count} (NOTE: pin not an ancestor of HEAD)"
    return count


def main():
    head = subprocess.run(
        ["git", "-C", str(SPEC_REPO), "rev-parse", "--short", "HEAD"],
        capture_output=True, text=True,
    ).stdout.strip()

    rows = []
    for repo, rel, pattern in CONSUMERS:
        pin, source, _ = read_pin(repo, rel, pattern)
        if pin is None:
            rows.append((repo, "unknown", source, source))
            continue
        dist = distance_behind(pin)
        rows.append((repo, pin[:12], dist, source))

    headers = ("consumer", "declared pin", "distance behind spec main", "source (file:line)")
    cols = list(zip(headers, *rows)) if rows else [(h,) for h in headers]
    widths = [max(len(str(c)) for c in col) for col in cols]

    def fmt(r):
        return "  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r))

    print(f"SpatialDDS-spec main HEAD: {head}  ({SPEC_REPO})\n")
    print(fmt(headers))
    print("  ".join("-" * w for w in widths))
    for r in rows:
        print(fmt(r))


if __name__ == "__main__":
    sys.exit(main())
