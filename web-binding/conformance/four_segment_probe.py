#!/usr/bin/env python3
"""Four-segment (short) topics: the suite discovers by url, never by segment count.

§3.3.2 registers four-segment topic names (`spatialdds/<stream>/<type>/<version>`,
no `<domain>`) — the discovery announce/depart lanes among them. Appendix N.3
serves such a topic in the well-known namespace at
`{base}/.well-known/spatialdds/<stream>/<type>/<version>`. A gateway that splits
topic names and requires five segments drops them: measured against the reference
gateway, an OpenVPS session served 0 resources and the suite honestly reported
`15 checks: 6 passed, 0 failed, 9 skipped` — UNEXERCISED everywhere, all
downstream of the gateway's drop; a five-segment control of the identical
payloads gave `14/0/1`. That drop is the gateway's (its own queue).

This probe shows the SUITE's verdict is honest either way: it follows the `url`
a manifest advertises and never splits the topic name, so a four-segment topic
served at its well-known path is exercised exactly like a five-segment one, and a
topic the endpoint does not serve is UNEXERCISED rather than silently dropped.

  FOUR-SEGMENT, SERVED   `spatialdds/discovery/announce/v1` advertised with its
                         well-known-namespace url and served → validated, counted.
  FIVE-SEGMENT CONTROL   `spatialdds/<domain>/discovery/announce/v1` at a
                         domain-scoped url → identical verdict and count.
  FOUR-SEGMENT, ABSENT   the endpoint serves nothing (the gateway dropped it) →
                         UNEXERCISED, not a false pass.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from run import (check_schema_validity, _synth_instance, Skip,  # noqa: E402
                 SCHEMAS_DIR, load_schemas)

BASE = "https://registry.example"
WK = "/.well-known/spatialdds"
ANNOUNCE_FQN = "spatial.disco.Announce"
# The four-segment topic's well-known path (N.3), and a five-segment control.
FOUR_PATH = f"{WK}/discovery/announce/v1"
FIVE_PATH = "/openvps/discovery/announce/v1"


class MockEndpoint:
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
        code, hdr, b = self.routes.get((method, self._path(target)), (404, {}, b""))
        return code, dict(hdr), b

    def json(self, target, token=None):
        code, _hdr, body = self.raw(target, token=token)
        if code != 200:
            raise AssertionError(f"GET {target} returned {code}")
        return json.loads(body)


def _manifest(topics):
    return {"results": [{"id": "spatialdds://registry.example/z/service/s",
                         "profile": "spatial.manifest/1.8", "rtype": "service",
                         "service": {"service_id": "s", "kind": "ANCHOR_REGISTRY",
                                     "topics": topics}}],
            "next_page_token": None}


def _routes(topics, announce_body, serve_path):
    index = [{"type": ANNOUNCE_FQN, "url": BASE + f"{WK}/schemas/x",
              "digest": "sha256:x"}]
    r = {
        ("GET", f"{WK}/search"): (200, {}, json.dumps(_manifest(topics)).encode()),
        ("GET", f"{WK}/schemas"): (200, {}, json.dumps(index).encode()),
    }
    if serve_path is not None:
        r[("GET", serve_path)] = (200, {}, json.dumps([announce_body]).encode())
    return r


def _topic(name, path):
    return {"name": name, "type": "announce", "version": "v1", "url": BASE + path,
            "access": "public-cacheable", "durability": "TRANSIENT_LOCAL"}


def _verdict(routes, schemas):
    ep = MockEndpoint(routes)
    try:
        return "PASS", check_schema_validity(ep, schemas)
    except Skip as e:
        return "SKIP", str(e)
    except Exception as e:
        return "FAIL", f"{type(e).__name__}: {e}"


def main():
    schemas = load_schemas(SCHEMAS_DIR)
    ann = _synth_instance(schemas[ANNOUNCE_FQN], schemas[ANNOUNCE_FQN].get("$defs", {}))
    bad = []

    # FOUR-SEGMENT, served at the well-known namespace path.
    four = _topic("spatialdds/discovery/announce/v1", FOUR_PATH)
    v4, d4 = _verdict(_routes([four], ann, FOUR_PATH), schemas)
    print(f"FOUR-SEGMENT, SERVED : {v4}  {d4}")
    if v4 != "PASS" or "1 latched instance" not in d4:
        bad.append(f"four-segment served should PASS with 1 instance, got {v4}: {d4}")

    # FIVE-SEGMENT control, identical payload at a domain-scoped path.
    five = _topic("spatialdds/openvps/discovery/announce/v1", FIVE_PATH)
    v5, d5 = _verdict(_routes([five], ann, FIVE_PATH), schemas)
    print(f"FIVE-SEGMENT CONTROL : {v5}  {d5}")
    if v5 != "PASS" or "1 latched instance" not in d5:
        bad.append(f"five-segment control should PASS with 1 instance, got {v5}: {d5}")

    # Segment count is not a variable: same verdict, same count.
    if (v4, "1 latched instance" in d4) != (v5, "1 latched instance" in d5):
        bad.append("four- and five-segment verdicts differ — segment count leaked in")

    # FOUR-SEGMENT, absent: the endpoint serves nothing (gateway dropped it).
    va, da = _verdict(_routes([], ann, None), schemas)
    print(f"FOUR-SEGMENT, ABSENT : {va}  {da[:70]}...")
    if va != "SKIP":
        bad.append(f"absent four-segment topic should be UNEXERCISED (SKIP), got {va}")

    print()
    if bad:
        print("four_segment_probe FAILED:")
        for b in bad:
            print("  - " + b)
        return 1
    print("four_segment_probe OK — the suite follows the advertised url and never "
          "splits the topic name; a four-segment topic served at its well-known "
          "path is exercised exactly like a five-segment one, and an unserved one "
          "is UNEXERCISED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
