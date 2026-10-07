#!/usr/bin/env python3
"""Gate 3: published member names are the IDL's, not the code generator's.

This generator reads the Python that `idlc` renders rather than an IDL AST, so
it sees `idlc`'s identifiers. Where an IDL member collides with a Python
keyword `idlc` prefixes an underscore, and for a time those renames were
published: `_global` and `_from` reached eleven schemas and four serializer
tables, among them the discovery types that §3.3.0's search binding returns.

MAPPING.md requires members under their **verbatim IDL names**, and §3.3.4's
coverage examples and §8.2.3's manifest example both write `"global": false`.
So the published contract contradicted the rule and the prose at once.

**Why this has to be asserted rather than relied upon.** The mismatch was
silent in both directions. `additionalProperties` is `true` by design -- it is
the APPENDABLE evolution rule restated for the web -- so a conforming
producer's `global` was accepted and ignored as an unknown field, while
`required` reported `_global` missing. A tolerant reader cannot be the detector
for a renamed field: tolerance is exactly what hides it. Something has to look.

The rule, stated so it can fail: a published property name may begin with an
underscore only if an IDL member of that name does. No IDL member does, because
IDL identifiers cannot begin with one, so in practice any leading underscore is
a generator artefact. The gate reads the IDL anyway rather than asserting the
simpler "no underscores", so that it keeps working if the specification ever
declares such a member and says so.

Reported by the binding's second implementation,
OpenArCloud/spatialdds-web, WEB-BINDING-FINDINGS.md finding 10.

Usage:  python3 web-binding/gate_names.py
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS = os.path.join(ROOT, "web-binding", "schemas")
TABLES = os.path.join(ROOT, "web-binding", "serializer_tables.json")
IDL_GLOBS = [os.path.join(ROOT, "idl", "v1.8", "*.idl"),
             os.path.join(ROOT, "idl", "v1.8", "provisional", "*.idl")]

# A member declaration: a type expression, then the member name, then `;`.
# Deliberately loose. It is used only to collect names that begin with an
# underscore, and over-collecting would make the gate more permissive in a way
# that is visible here rather than less permissive in a way that is not.
MEMBER = re.compile(r"^\s*(?:@\w+(?:\([^)]*\))?\s*)*[\w:<>,\s]+?\s+(_\w+)\s*(?:\[[^\]]*\])*\s*;",
                    re.M)


def idl_underscore_members() -> set[str]:
    names: set[str] = set()
    for pattern in IDL_GLOBS:
        for path in sorted(glob.glob(pattern)):
            names |= set(MEMBER.findall(open(path).read()))
    return names


def schema_property_names() -> dict[str, set[str]]:
    """Every property name each schema declares, its `$defs` included."""
    out: dict[str, set[str]] = {}
    for path in sorted(glob.glob(os.path.join(SCHEMAS, "*.json"))):
        doc = json.load(open(path))
        names: set[str] = set()

        def walk(node):
            if isinstance(node, dict):
                props = node.get("properties")
                if isinstance(props, dict):
                    names.update(props)
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(doc)
        out[os.path.basename(path)] = names
    return out


def table_field_names() -> dict[str, set[str]]:
    if not os.path.exists(TABLES):
        return {}
    tables = json.load(open(TABLES))
    out: dict[str, set[str]] = {}
    for fqn, spec in tables.items():
        if spec.get("kind") == "struct":
            out[fqn] = {n for n, _ in spec["fields"]}
        elif spec.get("kind") == "union":
            out[fqn] = {c[1] for c in spec["cases"] if c[1]}
    return out


def main() -> int:
    allowed = idl_underscore_members()
    schemas = schema_property_names()
    tables = table_field_names()
    if not schemas:
        print(f"gate_names: no schemas in {SCHEMAS} — run gen.py first")
        return 1

    bad_schema = {f: sorted(n for n in names
                            if n.startswith("_") and n not in allowed)
                  for f, names in schemas.items()}
    bad_schema = {f: n for f, n in bad_schema.items() if n}
    bad_tables = {f: sorted(n for n in names
                            if n.startswith("_") and n not in allowed)
                  for f, names in tables.items()}
    bad_tables = {f: n for f, n in bad_tables.items() if n}

    n_props = sum(len(v) for v in schemas.values())
    print(f"gate_names: {len(schemas)} schemas, {n_props} property name(s); "
          f"{len(tables)} table entries")
    print(f"  IDL members beginning with an underscore: "
          f"{sorted(allowed) if allowed else 'none'}")

    if bad_schema or bad_tables:
        print("gate_names FAILED: published names that no IDL member has")
        for f, names in sorted(bad_schema.items()):
            print(f"  schema {f}: {names}")
        for f, names in sorted(bad_tables.items()):
            print(f"  table  {f}: {names}")
        print("  These are the code generator's identifiers, not the "
              "specification's. MAPPING.md requires verbatim IDL names; see "
              "gen.py's unmangle().")
        return 1

    print("gate_names OK (every published name is a name the IDL declares).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
