#!/usr/bin/env python3
"""1.8.3 — a deployment's own lane is held to the schema the endpoint publishes
for it, and the suite keeps its teeth.

Through 1.8.2 the suite validated lanes against the binding's own schema set
only. An endpoint serving a deployment type (§3.3.2), with the schema N.2
requires it to publish, failed four checks the moment a tenant published valid
data on that lane — measured on spatialdds 0.8.1 serving the OWM 0.2
relationship prototype: "11 passed, 4 failed" ("endpoint publishes types the
binding does not define"; "no published schema for type 'oarc.relationship'",
three times). The suite was measuring its own closed-type assumption. It now
holds a namespaced topic type to the endpoint's published schema for it, and a
specification type to the binding's, as before.

This probe drives the real checks against a mocked endpoint and asserts:

  VALID            an extension lane whose instances meet the published schema
                   passes the self-describing and validity checks, and is counted.
  INSTANCE-BAD     an instance that violates its own published schema FAILS.
  DIGEST           an extension schema whose body does not digest to the index's
                   value FAILS the self-describing check.
  TITLE, BASENAME  a schema titled other than its type, or published at a name
                   other than N.2's, FAILS.
  NOT-A-SCHEMA     a published document that is not well-formed JSON Schema FAILS.
  NO-SCHEMA        an advertised extension topic with no index row FAILS.
  AMBIGUOUS        two extension rows that both fit one topic FAIL: the endpoint
                   has not said which contract applies.
  NO-SHADOW        an extension row named like a specification type does not
                   stand in for it: `geo_anchor` is still held to the binding's.

Run it directly; exit 0 iff every expectation holds.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run import (SCHEMAS_DIR, canon, check_schema_validity,  # noqa: E402
                 check_schemas_endpoint, load_schemas, schema_for)
from empty_registry_probe import BASE, WK, MockEndpoint  # noqa: E402

EXT_TYPE = "acme_owm.Claim"
EXT_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": f"spatialdds:webjson:{EXT_TYPE}", "title": EXT_TYPE,
    "type": "object", "additionalProperties": False,
    "required": ["id", "asserter"],
    "properties": {"id": {"type": "string"}, "asserter": {"type": "string"}},
}
LANE = "/z/world/acme.claim/v1"


def routes(binding, ext_rows, instances, topic_type="acme.claim"):
    """A self-describing surface: the binding's schemas, the given extension
    rows (type, published body, served-at basename, digest override), and one
    advertised extension lane serving `instances`."""
    r, index = {}, []
    for ty, schema in binding.items():
        url = f"{BASE}{WK}/schemas/{ty.replace('.', '_')}"
        index.append({"type": ty, "url": url,
                      "digest": "sha256:" + hashlib.sha256(canon(schema).encode()).hexdigest()})
        r[("GET", f"{WK}/schemas/{ty.replace('.', '_')}")] = (200, {}, json.dumps(schema).encode())
    for ty, doc, basename, digest in ext_rows:
        url = f"{BASE}{WK}/schemas/{basename}"
        index.append({"type": ty, "url": url, "digest": digest or
                      "sha256:" + hashlib.sha256(canon(doc).encode()).hexdigest()})
        r[("GET", f"{WK}/schemas/{basename}")] = (200, {}, json.dumps(doc).encode())
    r[("GET", f"{WK}/schemas")] = (200, {}, json.dumps(index).encode())
    r[("GET", f"{WK}/search")] = (200, {}, json.dumps({"results": [{
        "service": {"service_id": "s", "topics": [{
            "name": "spatialdds" + LANE, "type": topic_type, "version": "v1",
            "url": BASE + LANE, "access": "operator-scoped",
            "durability": "TRANSIENT_LOCAL"}]}}], "next_page_token": None}).encode())
    r[("GET", LANE)] = (200, {}, json.dumps(instances).encode())
    return r, index


def ext(doc=EXT_SCHEMA, ty=EXT_TYPE, basename=None, digest=None):
    return (ty, doc, basename or ty.replace(".", "_"), digest)


def outcome(fn, ep, binding):
    try:
        return "PASS", fn(ep, binding)
    except Exception as e:                       # noqa: BLE001 -- the verdict
        return "FAIL", str(e)


def main():
    binding = load_schemas(SCHEMAS_DIR)
    good = [{"id": "near-1", "asserter": "alice"}]
    bad = []

    def expect(label, fn, rows, instances, want, topic_type="acme.claim", contains=""):
        ep = MockEndpoint(routes(binding, rows, instances, topic_type)[0])
        got, detail = outcome(fn, ep, binding)
        print(f"{label:14} {fn.__name__:24} {got}  {str(detail)[:110]}")
        if got != want or (contains and contains not in str(detail)):
            bad.append(f"{label}: {fn.__name__} expected {want}"
                       + (f" mentioning {contains!r}" if contains else "")
                       + f", got {got}: {detail}")

    expect("VALID", check_schemas_endpoint, [ext()], good, "PASS", contains=EXT_TYPE)
    expect("VALID", check_schema_validity, [ext()], good, "PASS", contains="1 latched")
    expect("INSTANCE-BAD", check_schema_validity, [ext()],
           [{"id": "near-1", "asserter": 7}], "FAIL")
    expect("INSTANCE-BAD", check_schema_validity, [ext()],
           [{"id": "near-1", "asserter": "a", "extra": 1}], "FAIL")
    expect("DIGEST", check_schemas_endpoint, [ext(digest="sha256:" + "0" * 64)],
           good, "FAIL", contains="digest")
    expect("TITLE", check_schemas_endpoint,
           [ext(doc={**EXT_SCHEMA, "title": "acme_owm.Other"})], good, "FAIL",
           contains="title")
    expect("BASENAME", check_schemas_endpoint, [ext(basename="acme-owm-claim")],
           good, "FAIL", contains="N.2")
    expect("NOT-A-SCHEMA", check_schemas_endpoint,
           [ext(doc={**EXT_SCHEMA, "type": 5})], good, "FAIL",
           contains="well-formed")
    expect("NO-SCHEMA", check_schema_validity, [], good, "FAIL",
           contains="no published schema")
    expect("AMBIGUOUS", check_schema_validity,
           [ext(), ext(doc={**EXT_SCHEMA, "title": "other_ns.Claim",
                            "$id": "spatialdds:webjson:other_ns.Claim"},
                       ty="other_ns.Claim")], good, "FAIL",
           contains="more than one")

    # NO-SHADOW: an extension row named like GeoAnchor, and a geo_anchor topic.
    ga = "spatial.core.GeoAnchor"
    shadow = {**EXT_SCHEMA, "title": "evil.GeoAnchor",
              "$id": "spatialdds:webjson:evil.GeoAnchor"}
    r, index = routes(binding, [ext(doc=shadow, ty="evil.GeoAnchor")], good)
    ep = MockEndpoint(r)
    held = schema_for(binding, {"type": "geo_anchor"}, index, ep)
    ok = held is binding[ga]
    print(f"{'NO-SHADOW':14} {'schema_for':24} {'PASS' if ok else 'FAIL'}  "
          f"geo_anchor held to {'the binding' if ok else held and held.get('title')}")
    if not ok:
        bad.append("no-shadow: geo_anchor must be held to the binding's GeoAnchor")

    if bad:
        print("\nextension-lane probe FAILED:")
        for b in bad:
            print("  -", b)
        return 1
    print("\nextension-lane probe OK: an extension lane is held to its published "
          "schema, and every way that schema or its data can be wrong still fails.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
