#!/usr/bin/env python3
"""Finding 39 — the suite reports UNEXERCISED, not FAIL, for an empty registry,
and keeps its teeth.

0.2.0 made an empty registry the normal starting state (`python -m
spatialdds.serve --authority registry.example --publish` serves a conformant
surface with no data in it). Against that shape the suite used to report five
data-dependent checks as *failures* where its own UNEXERCISED vocabulary is the
right answer — "6 passed, 5 failed, 3 skipped". A check whose subject matter is
absent is unexercised, not failed (the rule the suite already applies to the
resolver, access classes, the QoS subset, and the §8.2 anchor-resolve flow).

This probe drives all 14 network checks against a *mocked* endpoint — no DDS, no
gateway, no network — in three scripted states, and asserts:

  EMPTY             an authority that holds nothing yet → 6 passed, 0 failed,
                    8 skipped. The acceptance record for a fresh deployment.
  CLAIMS-BUT-404    an endpoint that advertises a resource and 404s it → still
                    FAILS (schema_validity and latched_get assert 200 on every
                    advertised path). UNEXERCISED must not swallow a broken
                    serve: an absence stated is worth a pass, a false claim is
                    not.
  SERVED-MALFORMED  an advertised resource served (200) but missing a required
                    field → still FAILS (the content checks bite when there is
                    content to be wrong about).

Run it directly; exit 0 iff every expectation holds. It is a gate on the
finding-39 behaviour: the class is closed, not the instance.
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402  (the suite under test)
from run import (NETWORK_CHECKS, Skip, SCHEMAS_DIR, canon, load_schemas)  # noqa: E402

BASE = "https://registry.example"
WK = "/.well-known/spatialdds"


class MockEndpoint:
    """A faithful stand-in for run.Endpoint: the checks see only json()/raw().

    `routes` maps (method, path-without-query) -> (code, headers, body_bytes).
    A path not in the table is a 404 with an empty body, exactly as a gateway
    answers for a resource it does not have.
    """
    def __init__(self, routes, token="tok"):
        self.base = BASE
        self.connect = BASE
        self.token = token
        self.routes = routes

    @staticmethod
    def _path(target):
        t = target[len(BASE):] if target.startswith(BASE) else target
        return t.split("?", 1)[0]

    def raw(self, target, token=None, headers=None, method="GET", body=None):
        code, hdr, b = self.routes.get((method, self._path(target)),
                                       (404, {}, b""))
        return code, dict(hdr), b

    def json(self, target, token=None):
        code, _hdr, body = self.raw(target, token=token)
        if code != 200:
            raise AssertionError(f"GET {target} returned {code}, expected 200")
        return json.loads(body)

    def ws_target(self, target):  # never reached in these states
        return target.replace("https://", "wss://")


def _schemas_index_routes(schemas):
    """A self-describing /schemas surface: an index plus each schema served at
    its url, with digests the index can be checked against (check #1)."""
    routes = {}
    index = []
    for ty, schema in schemas.items():
        url = f"{BASE}{WK}/schemas/{ty}"
        body = json.dumps(schema).encode()
        digest = "sha256:" + hashlib.sha256(canon(schema).encode()).hexdigest()
        index.append({"type": ty, "url": url, "digest": digest})
        routes[("GET", f"{WK}/schemas/{ty}")] = (200, {}, body)
    routes[("GET", f"{WK}/schemas")] = (200, {}, json.dumps(index).encode())
    return routes


def empty_routes(schemas):
    routes = _schemas_index_routes(schemas)
    routes[("GET", f"{WK}/search")] = (
        200, {}, json.dumps({"results": [], "next_page_token": None}).encode())
    routes[("GET", f"{WK}/bootstrap")] = (404, {}, b"")
    routes[("GET", f"{WK}/resolver")] = (404, {}, b"")
    routes[("POST", "/")] = (404, {}, b"")  # no command lane; a clean refusal
    return routes


def _one_latched_manifest(topic_url, access="public-cacheable"):
    """A search response advertising exactly one latched GeoAnchor topic."""
    return {"results": [{
        "id": "spatialdds://registry.example/z/service/s",
        "profile": "spatial.manifest/1.8",
        "rtype": "service",
        "service": {
            "service_id": "s", "kind": "ANCHOR_REGISTRY",
            "topics": [{
                "name": "spatialdds/z/anchors/geo_anchor/v1",
                "type": "geo_anchor", "version": "v1", "url": topic_url,
                "access": access, "durability": "TRANSIENT_LOCAL",
            }],
        },
    }], "next_page_token": None}


def claims_but_404_routes(schemas):
    """Advertises a latched resource, then 404s its path — a false claim."""
    routes = _schemas_index_routes(schemas)
    topic_path = "/z/anchors/geo_anchor/v1"
    routes[("GET", f"{WK}/search")] = (
        200, {}, json.dumps(_one_latched_manifest(BASE + topic_path)).encode())
    # topic_path intentionally absent from routes -> 404
    return routes


def served_malformed_routes(schemas):
    """Advertises a latched resource and serves a 200 that omits a required
    field — the content is present and wrong."""
    routes = _schemas_index_routes(schemas)
    topic_path = "/z/anchors/geo_anchor/v1"
    routes[("GET", f"{WK}/search")] = (
        200, {}, json.dumps(_one_latched_manifest(BASE + topic_path)).encode())
    # A GeoAnchor with no fields at all: every required member is missing.
    routes[("GET", topic_path)] = (
        200, {"ETag": '"sha256:x"', "Cache-Control": "max-age=60"},
        json.dumps([{"anchor_id": "a"}]).encode())
    return routes


def _run(routes, schemas):
    """Run all 14 checks against a mock; return {name: ('PASS'|'FAIL'|'SKIP', info)}."""
    ep = MockEndpoint(routes)
    out = {}
    for name, fn in NETWORK_CHECKS:
        try:
            detail = fn(ep, schemas)
            out[name] = ("PASS", detail)
        except Skip as e:
            out[name] = ("SKIP", str(e))
        except Exception as e:
            out[name] = ("FAIL", f"{type(e).__name__}: {e}")
    return out


def _totals_line(results):
    """Reproduce run.main()'s totals line exactly, from a results map."""
    skipped = [n for n, (v, _) in results.items() if v == "SKIP"]
    failed = [n for n, (v, _) in results.items() if v == "FAIL"]
    npass = len(results) - len(skipped) - len(failed)
    line = f"{len(results)} checks: {npass} passed, {len(failed)} failed, {len(skipped)} skipped"
    if skipped:
        line += " (skipped: " + ", ".join(skipped) + ")"
    if failed:
        line += " (failed: " + ", ".join(failed) + ")"
    return line, npass, len(failed), len(skipped)


FIVE = [
    "every resource validates against its published schema",
    "canonical form on the wire",
    "latched state is GET with ETag, Cache-Control and 304",
    "§8.1 hello spatial in ten lines",
    "§8.4 third-party reader, published schemas only",
]


def main():
    schemas = load_schemas(SCHEMAS_DIR)
    bad = []

    # 1) EMPTY — the acceptance record for a fresh deployment.
    res = _run(empty_routes(schemas), schemas)
    line, npass, nfail, nskip = _totals_line(res)
    print("EMPTY REGISTRY:")
    print("  " + line)
    if (npass, nfail, nskip) != (6, 0, 8):
        bad.append(f"empty: expected 6/0/8, got {npass}/{nfail}/{nskip}")
    for n in FIVE:
        if res[n][0] != "SKIP":
            bad.append(f"empty: {n!r} should be SKIP, is {res[n][0]}")

    # 2) CLAIMS-BUT-404 — a false claim still fails (the teeth).
    res2 = _run(claims_but_404_routes(schemas), schemas)
    print("\nCLAIMS-BUT-NOT-SERVED (advertises a resource, 404s it):")
    print("  " + _totals_line(res2)[0])
    for n in ("every resource validates against its published schema",
              "latched state is GET with ETag, Cache-Control and 304"):
        if res2[n][0] != "FAIL":
            bad.append(f"claims-404: {n!r} must FAIL (teeth), is {res2[n][0]}")

    # 3) SERVED-MALFORMED — present and wrong still fails.
    res3 = _run(served_malformed_routes(schemas), schemas)
    print("\nSERVED-BUT-MALFORMED (200 missing required fields):")
    print("  " + _totals_line(res3)[0])
    if res3["§8.4 third-party reader, published schemas only"][0] != "FAIL":
        bad.append("served-malformed: third-party reader must FAIL, is "
                   f"{res3['§8.4 third-party reader, published schemas only'][0]}")

    print()
    if bad:
        print("empty_registry_probe FAILED:")
        for b in bad:
            print("  - " + b)
        return 1
    print("empty_registry_probe OK — empty registry certifies as 6 passed, 0 "
          "failed, 8 skipped; a false claim and malformed content still fail.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
