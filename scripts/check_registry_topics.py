#!/usr/bin/env python3
"""Registry-topic cross-check gate.

The §3.3.2 registry declared the Open World Model entity topic as
`spatialdds/<scene>/model/entity/v0` while every deployed artifact spoke
`spatialdds/<scene>/world/entity/v1`, and nothing caught the drift because
`check_registry.py` validates that each row names a resolvable IDL type but never
looks at the topic *string*. This gate closes that gap with the check the spec's
own material allows: it cross-checks every `spatialdds/.../v<N>` topic string the
registry declares against every such string elsewhere in the spec.

Two invariants, both derived from the registry as the authority:

  A. Version consistency per topic family. For each (stream, type) pair that
     appears anywhere in the spec, there is exactly one version. A registry row
     at `.../world/entity/v1` and an example at `.../world/entity/v0` is the
     drift this catches.

  B. Single-stream registered types. A type segment that the §3.3.2 registry
     pins to exactly one stream and one IDL type (e.g. `entity` -> `world` ->
     `spatial::owm::Entity`) must not appear under any other stream in the spec.
     A stray `.../model/entity/...` is the drift this catches. Type segments the
     registry backs with more than one row/stream (e.g. `event` under both
     `events` and `mapping`, `query` under `discovery` and `vps`) are exempt,
     because the multiplicity is itself registered.

Usage:
  check_registry_topics.py <ver>              # check; exit non-zero on drift
  check_registry_topics.py <ver> --selftest   # plant a known drift, confirm it fails
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

TOPIC = re.compile(r"spatialdds/[A-Za-z0-9_<>\-]+(?:/[A-Za-z0-9_<>\-]+)*/v[0-9]+")
PLACEHOLDER = re.compile(r"^<[^>]+>$")
IDLTYPE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:::[A-Za-z_][A-Za-z0-9_]*)+")


def parse(topic):
    """(stream, type_segment, version) for a topic, placeholders normalized to '*'."""
    p = topic.split("/")
    if len(p) < 4 or p[0] != "spatialdds":
        return None
    stream, typ, ver = p[-3], p[-2], p[-1]
    norm = lambda s: "*" if PLACEHOLDER.match(s) else s
    return (norm(stream), typ, ver)


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def registry_rows(profiles_md):
    """Every §3.3.2 registry table row, as its raw line.

    A registry row is a Markdown table line (`| ... |`) that carries both a
    `spatialdds/.../v<N>` topic string and a `module::Type` IDL reference — the
    QoS table (§3.3.3) rows carry neither, and the §3.3.0 examples are JSON, not
    table rows, so this isolates the registry without fragile region-slicing.
    """
    out = []
    for line in read(profiles_md).splitlines():
        if line.lstrip().startswith("|") and TOPIC.search(line) and IDLTYPE.search(line):
            out.append(line)
    return out


def collect(ver, extra_topics=()):
    sections = os.path.join(ROOT, "sections", f"v{ver}")
    profiles = os.path.join(sections, "02-idl-profiles.md")

    # Registry rows: per table row, its topic strings and IDL types.
    reg_streams = {}   # type_seg -> set(streams)   (from registry topic strings)
    reg_types = {}     # type_seg -> set(idl_types) (IDL types in rows bearing that seg's topic)
    for line in registry_rows(profiles):
        topics = TOPIC.findall(line)
        idl_types = set(IDLTYPE.findall(line))
        for t in topics:
            pr = parse(t)
            if not pr:
                continue
            stream, typ, _ver = pr
            reg_streams.setdefault(typ, set()).add(stream)
            reg_types.setdefault(typ, set()).update(idl_types)

    # Every topic string anywhere in the spec (registry included), + any planted ones.
    spec = {}          # (stream, type_seg) -> set((version, source))
    def add(topic, source):
        pr = parse(topic)
        if pr:
            stream, typ, ver = pr
            spec.setdefault((stream, typ), set()).add((ver, source))
    for fn in sorted(os.listdir(sections)):
        if fn.endswith(".md"):
            for t in TOPIC.findall(read(os.path.join(sections, fn))):
                add(t, fn)
    for t in extra_topics:
        add(t, "<planted>")

    return reg_streams, reg_types, spec


def check(ver, extra_topics=()):
    reg_streams, reg_types, spec = collect(ver, extra_topics)
    failures = []

    # Invariant A: one version per (stream, type) family.
    for (stream, typ), entries in sorted(spec.items()):
        versions = {v for (v, _s) in entries}
        if len(versions) > 1:
            where = sorted({s for (_v, s) in entries} | set())
            failures.append(
                f"topic family {stream}/{typ} appears at multiple versions "
                f"{sorted(versions)} (sources: {where}) — a registry/example version drift")

    # Invariant B: a registry type-segment pinned to one stream + one IDL type
    # must not appear under any other stream in the spec.
    seg_streams_in_spec = {}
    for (stream, typ) in spec:
        seg_streams_in_spec.setdefault(typ, set()).add(stream)
    for typ, streams in sorted(reg_streams.items()):
        if len(streams) == 1 and len(reg_types.get(typ, ())) == 1:
            pinned = next(iter(streams))
            stray = seg_streams_in_spec.get(typ, set()) - {pinned}
            if stray:
                idl = next(iter(reg_types[typ]))
                failures.append(
                    f"type segment '{typ}' is registered under stream '{pinned}' only "
                    f"({idl}), but the spec also uses it under {sorted(stray)} — topic drift")

    return failures


def main(argv):
    ver = next((a for a in argv[1:] if not a.startswith("--")), "1.8")
    if "--selftest" in argv:
        # Plant the exact historical drift: the OWM entity topic under the old
        # model/ stream at v0, contradicting the registry's world/entity/v1.
        planted = check(ver, extra_topics=["spatialdds/<scene>/model/entity/v0"])
        if not planted:
            print("check_registry_topics --selftest FAILED: the planted "
                  "spatialdds/<scene>/model/entity/v0 drift was NOT detected — the "
                  "gate is not failable."); return 1
        print("check_registry_topics --selftest OK: the planted model/entity/v0 "
              "drift is detected (gate is failable):")
        for f in planted:
            print("  - " + f)
        return 0

    failures = check(ver)
    if failures:
        print(f"check_registry_topics FAILED for v{ver} ({len(failures)}):")
        for f in failures:
            print("  - " + f)
        return 1
    print(f"Registry-topic cross-check OK for v{ver} (every §3.3.2 topic agrees "
          f"with the spec's examples on stream and version).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
