#!/usr/bin/env python3
"""SpatialDDS registered-types registry gate.

Motivated by findings batch 2 (A.3). Two directions:

  FATAL — Reference integrity. Every §3.3.2 registry row MUST name a
    resolvable IDL type (``module::Struct``) — a typeless row is a spec defect —
    and that type MUST resolve to a struct in idl/v<ver>. Every QoS profile a
    row names (``QoS `PROFILE` ``) MUST appear in the §3.3.3 QoS table. Example
    (Appendix E) types are resolvable targets but are not required to have rows.

  FATAL — Coverage. Every topic-bearing struct (heuristic: declares a
    ``schema_version`` field) MUST be named by a registry row, matched
    underscore- and case-insensitively (``NavSatStatus`` ↔ ``navsat_status``).
    Embedded helper types that legitimately carry ``schema_version`` without
    being standalone topics are allow-listed; Appendix E informative examples
    (neural, agent) are excluded.

Usage: check_registry.py [version]   (default: 1.7)
Exit status is nonzero on any FATAL failure.
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Structs that carry schema_version but are embedded in a topic-bearing struct
# rather than published as a topic in their own right. Not registry defects.
EMBEDDED_ALLOWLIST = {
    "StreamMeta",   # embedded as <SensorMeta>.base
}

SCHEMA_VER_RE = re.compile(r'\bstring\s+schema_version\b')
# In a registry Notes cell: `sensing::vision::Detection2DSet`; QoS `DET_RT`
TYPE_REF_RE = re.compile(r'`([A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)+)`')
QOS_REF_RE = re.compile(r'QoS\s+`([A-Z_][A-Z0-9_]*)`')
# Scope-opener keywords and brace tokens, scanned positionally.
TOKEN_RE = re.compile(
    r'\b(module|struct|union|enum)\s+([A-Za-z_][A-Za-z0-9_]*)|([{}])')


def _strip_comments(text):
    text = re.sub(r'//[^\n]*', '', text)
    text = re.sub(r'/\*.*?\*/', '', text, flags=re.S)
    return text


def collect_idl(idl_dir):
    """Return (fqn_structs, schema_version_structs).

    fqn_structs: set of fully-qualified struct names (e.g.
      'spatial::sensing::vision::Detection2DSet') plus bare names for
      suffix matching.
    schema_version_structs: set of simple struct names that declare a
      schema_version field.
    """
    fqns = set()
    schema_structs = set()
    for dirpath, dirnames, files in os.walk(idl_dir):
        # Appendix E informative examples (neural, agent) are excluded from
        # COVERAGE (schema_structs) — they are not registry candidates — but
        # their FQNs are still collected so a registry row MAY resolve to them.
        is_example = os.path.basename(dirpath) == "examples"
        for fn in sorted(files):
            if not fn.endswith(".idl"):
                continue
            text = _strip_comments(
                open(os.path.join(dirpath, fn), encoding="utf-8").read())
            stack = []          # list of (kind, name) for open scopes
            pending = None      # (kind, name) awaiting its '{'
            for m in TOKEN_RE.finditer(text):
                if m.group(1):                      # opener keyword + name
                    kind, name = m.group(1), m.group(2)
                    pending = (kind, name)
                    if kind == "struct":
                        mods = [n for (k, n) in stack if k == "module"]
                        fqns.add("::".join(mods + [name]))
                        fqns.add(name)
                elif m.group(3) == "{":
                    stack.append(pending if pending else ("scope", None))
                    pending = None
                elif m.group(3) == "}":
                    if stack:
                        stack.pop()
                    pending = None
            # Second pass: attribute schema_version to its enclosing struct.
            # Coverage excludes examples, so skip their schema_version scan.
            if is_example:
                continue
            stack = []
            pending = None
            for m in re.finditer(
                    r'\b(module|struct|union|enum)\s+([A-Za-z_][A-Za-z0-9_]*)'
                    r'|([{}])|(\bstring\s+schema_version\b)', text):
                if m.group(1):
                    pending = (m.group(1), m.group(2))
                elif m.group(3) == "{":
                    stack.append(pending if pending else ("scope", None))
                    pending = None
                elif m.group(3) == "}":
                    if stack:
                        stack.pop()
                    pending = None
                elif m.group(4):
                    for (k, n) in reversed(stack):
                        if k == "struct":
                            schema_structs.add(n)
                            break
    return fqns, schema_structs


def read_section(sections_dir, name):
    path = os.path.join(sections_dir, name)
    return open(path, encoding="utf-8").read() if os.path.exists(path) else ""


def collect_registry_and_qos(profiles_md):
    """Return (rows, qos_profiles).

    rows: list of (slug, [type_refs_in_row], [qos_refs_in_row]) — one per
      §3.3.2 registry data row, in document order.
    qos_profiles: set of profile names defined in the §3.3.3 QoS table.
    """
    rows = []
    qos_profiles = set()
    in_registry = False
    in_qos = False
    for line in profiles_md.split("\n"):
        s = line.strip()
        if s.startswith("#### ") and "Typed Topics Registry" in s:
            in_registry, in_qos = True, False
            continue
        if s.startswith("#### ") and "QoS Profiles" in s:
            in_registry, in_qos = False, True
            continue
        if s.startswith("#### ") or s.startswith("### "):
            in_registry = in_qos = False
        if in_registry and s.startswith("| `"):
            m = re.match(r'\|\s*`([a-z][a-z0-9_]*)`', s)
            if m:
                trefs = [x.group(1) for x in TYPE_REF_RE.finditer(line)]
                qrefs = [x.group(1) for x in QOS_REF_RE.finditer(line)]
                rows.append((m.group(1), trefs, qrefs))
        if in_qos and s.startswith("| `"):
            m = re.match(r'\|\s*`([A-Z_][A-Z0-9_]*)`', s)
            if m:
                qos_profiles.add(m.group(1))
    return rows, qos_profiles


def _norm(name):
    """Lowercase, strip non-alphanumerics — so 'NavSatStatus', 'nav_sat_status'
    and 'navsat_status' all compare equal."""
    return re.sub(r'[^a-z0-9]', '', name.lower())


def fqn_resolves(ref, fqns):
    """A ref like 'sensing::vision::Detection2DSet' resolves if some known FQN
    ends with '::'+ref or equals 'spatial::'+ref or equals ref."""
    if ref in fqns:
        return True
    tail = "::" + ref
    for f in fqns:
        if f.endswith(tail) or f == "spatial::" + ref:
            return True
    return False


def main():
    version = sys.argv[1] if len(sys.argv) > 1 else "1.7"
    sections_dir = os.path.join(ROOT, "sections", f"v{version}")
    idl_dir = os.path.join(ROOT, "idl", f"v{version}")
    for d in (sections_dir, idl_dir):
        if not os.path.isdir(d):
            print(f"error: missing directory {d}", file=sys.stderr)
            return 2

    fqns, schema_structs = collect_idl(idl_dir)
    profiles_md = read_section(sections_dir, "02-idl-profiles.md")
    rows, qos_profiles = collect_registry_and_qos(profiles_md)

    all_type_refs = set()
    all_slugs = set()
    fatal = []
    # Rule 1 (reverse): every registry row MUST name a resolvable IDL type; a
    # typeless row is a spec defect. Referenced QoS profiles must exist too.
    for slug, trefs, qrefs in rows:
        all_slugs.add(slug)
        all_type_refs.update(trefs)
        if not trefs:
            fatal.append(f"registry row `{slug}` names no IDL type "
                         f"(every row MUST name a resolvable `module::Struct`)")
        for ref in trefs:
            if not fqn_resolves(ref, fqns):
                fatal.append(f"registry row `{slug}` names IDL type `{ref}` with "
                             f"no matching struct in idl/v{version}")
        for prof in qrefs:
            if prof not in qos_profiles:
                fatal.append(f"registry row `{slug}` names QoS profile `{prof}` "
                             f"absent from the §3.3.3 QoS Profiles table")

    # Rule 2 (coverage): every topic-bearing struct (schema_version heuristic)
    # must be named by a registry row, matched underscore- and case-insensitively
    # (so 'NavSatStatus' ↔ 'navsat_status'). Embedded helper types are
    # allow-listed; Appendix E examples are excluded upstream.
    ref_norms = {_norm(r.split("::")[-1]) for r in all_type_refs}
    slug_norms = {_norm(s) for s in all_slugs}
    for s in sorted(schema_structs):
        if s in EMBEDDED_ALLOWLIST:
            continue
        n = _norm(s)
        if n in ref_norms or n in slug_norms:
            continue
        fatal.append(f"topic-bearing struct `{s}` (declares schema_version) has "
                     f"no registry row in §3.3.2")

    if fatal:
        print(f"Registry gate FAILED for v{version} ({len(fatal)} issue(s)):\n")
        for f in fatal:
            print(f"  - {f}")
        return 1
    print(f"Registry gate OK for v{version} "
          f"({len(rows)} rows; all name a resolvable IDL type and QoS profile).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
