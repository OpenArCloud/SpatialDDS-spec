#!/usr/bin/env python3
"""Web Binding — backend-blind conformance runner (step 6 skeleton).

Safe by construction: everything here is defined by the binding's own invariants
(the published schemas, the backend-blind client contract, skip-clean), not by
the gateway's shape. The gateway-specific checks (the cross-cutting checks and
the four §8 scenarios in README.md) are added as step 5 stands up an endpoint;
until then this runs a local self-check and SKIPs the network checks clean.

    python3 web-binding/conformance/run.py [--endpoint URL] [--token T]

No --endpoint -> SKIP (reason + remedy), exit 0, after the local self-check.
The suite is backend-blind: it takes only an endpoint and a token, and no code
path branches on whether a DDS bus or a web-native server is behind it.
"""
import argparse, glob, json, os, sys, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMAS_DIR = os.path.join(os.path.dirname(HERE), "schemas")
# Reuse the canonical-form helpers the round-trip gate already proved.
sys.path.insert(0, os.path.dirname(HERE))
from gate_roundtrip import canon, ecma262  # noqa: E402


def load_schemas(schemas_dir):
    """Load every published JSON Schema, keyed by its `title` (the type FQN).

    Defined by the binding's own output (web-binding/schemas/), not the gateway —
    conformance means "validates against the generated contract", so the suite's
    source of truth is the same schemas gate 1 pins.
    """
    schemas = {}
    for p in sorted(glob.glob(os.path.join(schemas_dir, "*.json"))):
        doc = json.load(open(p))
        title = doc.get("title") or os.path.basename(p)[:-5]
        schemas[title] = doc
    if not schemas:
        raise SystemExit(f"conformance: no schemas in {schemas_dir} — run gen.py first")
    return schemas


class Endpoint:
    """Backend-blind HTTP(S) client: base URL + optional bearer token, nothing
    that reveals or depends on what implements the endpoint. Network checks use
    this; it makes no call until one is invoked."""
    def __init__(self, base, token=None):
        self.base = base.rstrip("/")
        self.token = token

    def get(self, path):
        req = urllib.request.Request(self.base + path)
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        with urllib.request.urlopen(req) as r:   # noqa: S310 (https endpoint)
            return r.status, dict(r.headers), r.read()


def self_check(schemas):
    """Toolchain-free: the published schemas load and are well-formed JSON Schema
    objects. Proves the runner's foundation without any gateway."""
    bad = [t for t, d in schemas.items()
           if d.get("$schema") != "https://json-schema.org/draft/2020-12/schema"
           or "type" not in d and "oneOf" not in d]
    if bad:
        raise SystemExit(f"conformance self-check FAILED: malformed schemas: {bad[:5]}")
    # canonical-form helpers are importable and sane
    assert ecma262(0.1) == "0.1" and ecma262(1.0) == "1" and canon(True) == "true"
    print(f"conformance self-check OK ({len(schemas)} schemas load; "
          f"canonical-form helpers available).")


# Gateway-dependent checks (cross-cutting + the four §8 scenarios) are registered
# here as step 5 exposes the surface each needs. Empty until a gateway exists, by
# design — see README.md "Build order within step 6". Each will take (ep, schemas).
NETWORK_CHECKS = []   # list[(name, fn)]


def main():
    ap = argparse.ArgumentParser(description="Web Binding backend-blind conformance suite")
    ap.add_argument("--endpoint", help="base URL of a binding endpoint (bridged or standalone)")
    ap.add_argument("--token", help="bearer token for operator-scoped resources")
    a = ap.parse_args()

    schemas = load_schemas(SCHEMAS_DIR)
    self_check(schemas)

    if not a.endpoint:
        print("conformance: SKIP network checks — no --endpoint given.\n"
              "  Remedy: pass --endpoint <url> of a binding gateway (bridged or "
              "standalone). A gateway is stood up in step 5 (sidecar repo); the "
              "network checks are added against it (README.md build order).")
        return 0

    if not NETWORK_CHECKS:
        print("conformance: endpoint given, but no network checks are wired yet.\n"
              "  The gateway-dependent checks track step 5's surface and are added "
              "as it comes up (README.md). Nothing is asserted against the endpoint "
              "yet — this is pending, not a pass.")
        return 0

    ep = Endpoint(a.endpoint, a.token)
    failures = []
    for name, fn in NETWORK_CHECKS:
        try:
            fn(ep, schemas)
            print(f"  PASS  {name}")
        except Exception as e:
            failures.append(f"{name}: {e}")
            print(f"  FAIL  {name}: {e}")
    if failures:
        print(f"conformance FAILED ({len(failures)}/{len(NETWORK_CHECKS)})")
        return 1
    print(f"conformance OK ({len(NETWORK_CHECKS)} checks).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
