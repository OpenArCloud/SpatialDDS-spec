#!/usr/bin/env python3
"""SpatialDDS registered-types registry gate.

Motivated by findings batch 2 (A.3). Two directions:

  FATAL — Reference integrity. Every §3.3.2 registry row that names an IDL
    type (``module::Struct``) MUST resolve to a struct in idl/v<ver>, and every
    QoS profile a row names (``QoS `PROFILE` ``) MUST appear in the §3.3.3 QoS
    table. This catches a registry row pointing at a type or profile that does
    not exist.

  ADVISORY — Coverage. Every topic-bearing struct (heuristic: declares a
    ``schema_version`` field) SHOULD be referenced by a registry row. Embedded
    helper types that legitimately carry ``schema_version`` without being
    standalone topics are allow-listed. Misses are reported but do not fail the
    build, because the heuristic cannot perfectly distinguish a topic from an
    embedded record.

Usage: check_registry.py [version]   (default: 1.7)
Exit status is nonzero only on a FATAL failure.
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
    for dirpath, _, files in os.walk(idl_dir):
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
    """Return (type_refs, qos_refs, qos_profiles, slugs).

    type_refs: set of 'module::Struct' referenced by registry rows.
    qos_refs:  set of QoS profile names referenced by registry rows.
    qos_profiles: set of profile names defined in the §3.3.3 QoS table.
    slugs: set of first-column registry `type` slugs (e.g. 'spatial_event').
    """
    type_refs = set()
    qos_refs = set()
    qos_profiles = set()
    slugs = set()
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
                slugs.add(m.group(1))
            for m in TYPE_REF_RE.finditer(line):
                type_refs.add(m.group(1))
            for m in QOS_REF_RE.finditer(line):
                qos_refs.add(m.group(1))
        if in_qos and s.startswith("| `"):
            m = re.match(r'\|\s*`([A-Z_][A-Z0-9_]*)`', s)
            if m:
                qos_profiles.add(m.group(1))
    return type_refs, qos_refs, qos_profiles, slugs


def _snake(name):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()


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
    type_refs, qos_refs, qos_profiles, slugs = collect_registry_and_qos(profiles_md)

    fatal = []
    for ref in sorted(type_refs):
        if not fqn_resolves(ref, fqns):
            fatal.append(f"registry row names IDL type `{ref}` with no matching "
                         f"struct in idl/v{version}")
    for prof in sorted(qos_refs):
        if prof not in qos_profiles:
            fatal.append(f"registry row names QoS profile `{prof}` absent from "
                         f"the §3.3.3 QoS Profiles table")

    # Advisory coverage: topic-bearing structs (schema_version heuristic) that no
    # registry row references by name.
    referenced_simple = {r.split("::")[-1] for r in type_refs}
    advisory = []
    for s in sorted(schema_structs):
        if s in EMBEDDED_ALLOWLIST:
            continue
        if s in referenced_simple or _snake(s) in slugs:
            continue
        advisory.append(s)

    if advisory:
        print(f"Registry coverage (advisory) for v{version}: "
              f"{len(advisory)} schema_version-bearing struct(s) not named by a "
              f"registry row (may be pre-existing or intentionally embedded):")
        for s in advisory:
            print(f"  ~ {s}")
        print()

    if fatal:
        print(f"Registry gate FAILED for v{version} ({len(fatal)} issue(s)):\n")
        for f in fatal:
            print(f"  - {f}")
        return 1
    print(f"Registry gate OK for v{version} "
          f"({len(type_refs)} typed row ref(s) resolve; "
          f"{len(qos_refs)} QoS ref(s) present).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
