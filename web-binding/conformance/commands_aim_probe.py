#!/usr/bin/env python3
"""Item 8 — the command check aims by advertisement, not by position, and the
advertise-but-refuse drift fails.

`check_commands_post` used to POST to `discover(ep)[0]` — the first advertised
topic by position. Measured against the reference N.6 surface (spatialdds-web
a55b6eb; the `--demo` gateway advertises `accepts_commands` on `geo_anchor`,
which is not first in the manifest), it reported `POST -> 405 (no command lane
advertised)` and passed, while a working handler sat on another lane. The check
aimed by position, not by the property under test, so an endpoint that
advertised a lane and then refused it would have passed identically.

The fix selects lanes by the `accepts_commands` advertisement and exercises the
N.6 accept path against each. This probe drives the fixed check against a mocked
endpoint — no gateway — in four states and asserts:

  ADVERTISED + ACCEPTS    an advertised lane that returns 202 accepted → PASS.
  ADVERTISED + REFUSES    an advertised lane that returns 405 → FAIL. The
                          injection: advertisement and behaviour must agree.
  ADVERTISED + WRONG      a 202 that does not name outcome "accepted" → FAIL.
  NONE ADVERTISED         no lane advertises a command surface; a POST is
                          refused 405 and the branch is conformant → PASS.

Run it directly; exit 0 iff every expectation holds. Gate on the aim-by-property
behaviour: the class is closed, not the instance.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run  # noqa: E402
from run import check_commands_post, COMMAND_ADVERTISEMENT, Skip, SCHEMAS_DIR, load_schemas  # noqa: E402

BASE = "https://registry.example"
WK = "/.well-known/spatialdds"
LANE = "/z/anchors/geo_anchor/v1"
QUIET = "/z/anchors/announce/v1"

# A real-enough GeoAnchor record to POST back as a command body.
RECORD = {"anchor_id": "a1", "map_id": "m", "method": "Surveyed"}


class MockEndpoint:
    """Routes (method, path) -> (code, headers, body_bytes); 404 otherwise."""
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


def _manifest(advertise_command_lane):
    topics = [
        {"name": "spatialdds/z/anchors/announce/v1", "type": "announce",
         "version": "v1", "url": BASE + QUIET, "access": "public-cacheable",
         "durability": "TRANSIENT_LOCAL"},
        {"name": "spatialdds/z/anchors/geo_anchor/v1", "type": "geo_anchor",
         "version": "v1", "url": BASE + LANE, "access": "public-cacheable",
         "durability": "TRANSIENT_LOCAL"},
    ]
    if advertise_command_lane:
        topics[1][COMMAND_ADVERTISEMENT] = True
    return {"results": [{"id": "spatialdds://registry.example/z/service/s",
                         "profile": "spatial.manifest/1.8", "rtype": "service",
                         "service": {"service_id": "s", "kind": "ANCHOR_REGISTRY",
                                     "topics": topics}}],
            "next_page_token": None}


def _routes(advertise, post_code, outcome):
    r = {
        ("GET", f"{WK}/search"): (200, {}, json.dumps(_manifest(advertise)).encode()),
        ("GET", LANE): (200, {}, json.dumps([RECORD]).encode()),
        ("GET", QUIET): (200, {}, json.dumps([{"service_id": "s"}]).encode()),
    }
    if post_code is not None:
        body = json.dumps({"outcome": outcome}).encode() if outcome is not None else b""
        r[("POST", LANE)] = (post_code, {}, body)
    # a POST to the quiet lane (used by the no-advertised branch) refuses 405
    r[("POST", QUIET)] = (405, {}, json.dumps({"title": "not a command lane"}).encode())
    return r


def _verdict(routes, schemas):
    ep = MockEndpoint(routes)
    try:
        return "PASS", check_commands_post(ep, schemas)
    except Skip as e:
        return "SKIP", str(e)
    except Exception as e:
        return "FAIL", f"{type(e).__name__}: {e}"


def main():
    schemas = load_schemas(SCHEMAS_DIR)
    bad = []

    v, info = _verdict(_routes(True, 202, "accepted"), schemas)
    print(f"ADVERTISED + ACCEPTS   : {v}  {info}")
    if v != "PASS":
        bad.append(f"advertised+accepts should PASS, got {v}")

    v, info = _verdict(_routes(True, 405, None), schemas)
    print(f"ADVERTISED + REFUSES   : {v}  {info}")
    if v != "FAIL":
        bad.append(f"advertised+405 should FAIL (injection), got {v}")

    v, info = _verdict(_routes(True, 202, "queued"), schemas)
    print(f"ADVERTISED + WRONG OUT : {v}  {info}")
    if v != "FAIL":
        bad.append(f"advertised+202-wrong-outcome should FAIL, got {v}")

    v, info = _verdict(_routes(False, None, None), schemas)
    print(f"NONE ADVERTISED        : {v}  {info}")
    if v != "PASS":
        bad.append(f"none-advertised should PASS (refuse branch), got {v}")

    print()
    if bad:
        print("commands_aim_probe FAILED:")
        for b in bad:
            print("  - " + b)
        return 1
    print("commands_aim_probe OK — the check aims by advertisement; an "
          "advertised lane that refuses fails, and no-command-lane stays "
          "conformant.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
