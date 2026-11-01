#!/usr/bin/env python3
"""Check the /owm/ page's replay asset: it is the published recording export,
and every claim the page draws traces to a record in it.

The Open World Model page (site_overlay/owm/) replays the crossing session from
one static file, site_overlay/owm/crossing-replay.json (schema owm-replay/2,
exported by SpatialDDS-demo's scenarios/crossing/export_replay.py). The page
carries no staged motion, so the file has to be exactly what the recording
produced, and nothing on the page may show a claim the file cannot back.

Three things are checked:

  1. Pin. The file's sha256 equals the asset SpatialDDS-demo published at the
     commit recorded below. Replacing the asset is a deliberate act: re-export
     it in the demo repo, copy it here, and move the pin in the same commit.

  2. Shape. The keys owm-replay/2 defines are present (schema, meta with its
     window, loop and honesty lines, map, tracks, gate, sight, claims, events).

  3. Traceability. Everything the page renders as a claim resolves to a record:
       - every revision of every segment (the strip's traces and ticks, the
         scene's annotations) is a recorded sample of that edge id at that
         time, with the same state and basis, and the same valid_from;
       - every segment ending (the strip's cap) is a RETIRED sample whose
         state_reason is the ending's reason, verbatim;
       - every narration line names its sources; a source on the relationship
         lane (a claim) is a sample in the asset, exact by key and stamp; a
         source on the entity lane is a gate sample in the asset, or a record
         the asset names by key (a track's `records`), whose sample the
         recording carries and SpatialDDS-demo's own test resolves. Those are
         observations feeding a narration line, never a claim the page draws,
         and the check counts them so the report says so;
       - every gate state the scene draws carries its record;
       - every claim name the page's script refers to exists in the asset.

Usage:
  check_owm_replay.py              # check; exit non-zero on any failure
  check_owm_replay.py --selftest   # plant known defects, confirm each fails
"""
import copy
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSET = os.path.join(ROOT, "site_overlay", "owm", "crossing-replay.json")
PAGE = os.path.join(ROOT, "site_overlay", "owm", "index.html")

# The published asset this page replays: SpatialDDS-demo, web/crossing/
# crossing-replay.json at 726d38e ("Crossing replay: owm-replay/2, exported
# from the committed session").
PIN_SHA256 = "50b17d5d298b30a31f26c3a39e44f797bba57fbee502d9ed3a5cd9f0b37655cc"
PIN_SOURCE = "OpenArCloud/SpatialDDS-demo@726d38e:web/crossing/crossing-replay.json"

REL_LANE = "spatialdds/crossing/world/oarc.relationship/v1"
ENT_LANE = "spatialdds/crossing/world/entity/v1"
TOL = 0.011   # asset times are rounded to 0.01 s


def stamp_s(st):
    return int(st["sec"]) + int(st["nanosec"]) / 1e9


def check(doc, raw_bytes, page_text):
    fails = []

    # 1. pin
    digest = hashlib.sha256(raw_bytes).hexdigest()
    if digest != PIN_SHA256:
        fails.append(f"asset sha256 {digest[:16]}… is not the pinned {PIN_SHA256[:16]}… "
                     f"({PIN_SOURCE}); re-export and move the pin deliberately")

    # 2. shape
    if doc.get("schema") != "owm-replay/2":
        fails.append(f"schema is {doc.get('schema')!r}, expected 'owm-replay/2'")
    for k in ("meta", "map", "tracks", "gate", "sight", "claims", "events"):
        if k not in doc:
            fails.append(f"missing top-level key {k!r}")
    if fails and any("missing top-level" in f or "schema is" in f for f in fails):
        return fails
    meta = doc["meta"]
    for k in ("recording", "sha256", "commit", "captured_utc", "driven_by", "window",
              "loop_s", "track_dt", "honesty"):
        if k not in meta:
            fails.append(f"meta lacks {k!r}")
    for k in ("world", "claims"):
        if k not in meta.get("honesty", {}):
            fails.append(f"meta.honesty lacks {k!r} (the page prints it)")
    t0 = meta["window"]["stamp_start"]
    rel = lambda st: stamp_s(st) - t0

    # 3. traceability: claims
    names = set()
    rel_records = set()          # (key, stamp-seconds rounded) on the relationship lane
    for c in doc["claims"]:
        nm = c.get("name")
        names.add(nm)
        for k in ("asserter", "subject", "predicate", "object", "lane", "segments", "records"):
            if k not in c:
                fails.append(f"claim {nm}: lacks {k!r}")
        recs = c.get("records", [])
        ids = {r["record"]["id"] for r in recs}
        if len(ids) != 1:
            fails.append(f"claim {nm}: records span {len(ids)} edge ids, expected one")
        for r in recs:
            rec = r["record"]
            rel_records.add((rec["id"], round(stamp_s(rec["stamp"]), 3)))
            if abs(rel(rec["stamp"]) - r["t"]) > TOL:
                fails.append(f"claim {nm}: sample at t {r['t']} carries stamp "
                             f"t {rel(rec['stamp']):.3f}")
        for s in c.get("segments", []):
            for rv in s["revisions"]:
                hit = [r for r in recs if abs(r["t"] - rv["t"]) <= TOL]
                if not hit:
                    fails.append(f"claim {nm}: revision at t {rv['t']} has no recorded sample")
                    continue
                rec = hit[0]["record"]
                if rec["state"] != rv["state"] or rec["basis"] != rv["basis"]:
                    fails.append(f"claim {nm}: revision at t {rv['t']} is {rv['state']}/"
                                 f"{rv['basis']}, the record says {rec['state']}/{rec['basis']}")
                rec_vf = rel(rec["valid_from"]) if rec.get("has_valid_from") else None
                if (rv["valid_from"] is None) != (rec_vf is None) or \
                        (rec_vf is not None and abs(rec_vf - rv["valid_from"]) > TOL):
                    fails.append(f"claim {nm}: revision at t {rv['t']} valid_from "
                                 f"{rv['valid_from']} vs record {rec_vf}")
            if s["to"] is not None:
                end = [r for r in recs if abs(r["t"] - s["to"]) <= TOL]
                if not end:
                    fails.append(f"claim {nm}: ending at t {s['to']} has no recorded sample")
                else:
                    rec = end[0]["record"]
                    if rec["state"] != "RETIRED":
                        fails.append(f"claim {nm}: ending at t {s['to']} is a {rec['state']} "
                                     f"sample, not RETIRED")
                    if rec["state_reason"] != s["reason"]:
                        fails.append(f"claim {nm}: ending reason {s['reason']!r} is not the "
                                     f"record's {rec['state_reason']!r}")

    # gate states, and the entity-lane records they are
    ent_records = set()
    named_entities = {k for tr in doc["tracks"] for k in tr.get("records", [])}
    named_entities |= {g["record"]["entity_id"] for g in doc["gate"] if g.get("record")}
    for g in doc["gate"]:
        rec = g.get("record")
        if not rec:
            fails.append(f"gate state {g.get('state')} at t {g.get('t')} carries no record")
            continue
        ent_records.add((rec["entity_id"], round(stamp_s(rec["stamp"]), 3)))
        if rec.get("state") is None:
            fails.append(f"gate record at t {g['t']} has no state")

    # narration sources
    by_name = []
    for e in doc["events"]:
        if not e.get("sources"):
            fails.append(f"narration at t {e['t']} names no source: {e['text'][:50]!r}")
        for s in e.get("sources", []):
            if "truth" in s:
                continue
            r = s.get("record")
            if not r:
                fails.append(f"narration at t {e['t']}: a source that is neither record nor truth")
                continue
            key = (r["key"], round(stamp_s(r["stamp"]), 3))
            if r["lane"] == REL_LANE:
                if key not in rel_records:
                    fails.append(f"narration at t {e['t']}: claim source {r['key']} @ {key[1]} is not "
                                 f"a sample in the asset")
            elif r["lane"] == ENT_LANE:
                if key in ent_records:
                    pass
                elif r["key"] in named_entities:
                    by_name.append((e["t"], r["key"]))
                else:
                    fails.append(f"narration at t {e['t']}: entity source {r['key']} is neither a "
                                 f"sample in the asset nor a record it names")
            else:
                fails.append(f"narration at t {e['t']}: source lane {r['lane']} is not one the asset carries")

    # the page refers to claims by name; each must exist
    used = set(re.findall(r'\bC\d+\b', page_text))
    for nm in sorted(used - names):
        fails.append(f"the page refers to claim {nm}, which the asset does not carry")

    check.by_name = by_name
    return fails


def load():
    raw = open(ASSET, "rb").read()
    return json.loads(raw), raw, open(PAGE, encoding="utf-8").read()


def main(argv):
    doc, raw, page = load()
    if "--selftest" in argv:
        plants = []
        # a changed byte: the pin catches it
        plants.append(("one changed byte in the asset", doc, raw.replace(b'"C1"', b'"C9"', 1), page))
        # a revision the recording never wrote
        d = copy.deepcopy(doc)
        d["claims"][0]["segments"][0]["revisions"].append(
            {"t": 30.0, "state": "UPDATED", "basis": "OBSERVED", "valid_from": None})
        plants.append(("a revision with no recorded sample", d, raw, page))
        # an ending reason that is not the record's
        d = copy.deepcopy(doc)
        d["claims"][2]["segments"][0]["reason"] = "withdrawn"
        plants.append(("an ending whose reason is not the record's", d, raw, page))
        # a narration source that resolves to nothing
        d = copy.deepcopy(doc)
        d["events"][0]["sources"][0]["record"]["key"] = "rel:svc:crossing:nobody:0"
        plants.append(("a narration source that is not a record", d, raw, page))
        # an entity-lane source the asset does not even name
        d = copy.deepcopy(doc)
        for e in d["events"]:
            for src in e["sources"]:
                if "record" in src and src["record"]["lane"] == ENT_LANE:
                    src["record"]["key"] = "ent:nobody:ghost"
                    break
            else:
                continue
            break
        plants.append(("an entity source the asset does not name", d, raw, page))
        # the page naming a claim the asset lacks
        plants.append(("the page naming a claim the asset lacks", doc, raw, page + "\n/* C42 */"))
        ok = True
        for label, d, r, p in plants:
            fails = check(d, r, p)
            print(f"  plant: {label}: {'caught' if fails else 'NOT CAUGHT'}"
                  + (f" ({fails[0][:90]})" if fails else ""))
            ok = ok and bool(fails)
        if not ok:
            print("check_owm_replay --selftest FAILED: a planted defect was not caught.")
            return 1
        clean = check(doc, raw, page)
        if clean:
            print("check_owm_replay --selftest FAILED: the unplanted asset does not pass:")
            for f in clean:
                print("  - " + f)
            return 1
        print(f"check_owm_replay --selftest OK: {len(plants)} plants caught, the real asset passes.")
        return 0

    fails = check(doc, raw, page)
    if fails:
        print(f"check_owm_replay FAILED ({len(fails)}):")
        for f in fails:
            print("  - " + f)
        return 1
    n_rev = sum(len(s["revisions"]) for c in doc["claims"] for s in c["segments"])
    n_src = sum(1 for e in doc["events"] for s in e["sources"] if "record" in s)
    print(f"OWM replay check OK: asset is {PIN_SOURCE} (sha256 pinned); "
          f"{len(doc['claims'])} claims, {n_rev} revisions and every ending trace to recorded "
          f"samples; {len(doc['events'])} narration lines, {n_src} record sources resolve "
          f"({n_src - len(check.by_name)} as samples in the asset, {len(check.by_name)} as an "
          f"observation the asset names and the recording carries"
          + (": " + ", ".join(f"{k} at t {t}" for t, k in check.by_name) if check.by_name else "") + ").")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
