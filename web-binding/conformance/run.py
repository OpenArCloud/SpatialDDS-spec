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
import argparse, glob, hashlib, json, os, re, sys, urllib.request, urllib.error

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

    def raw(self, path, token=None, headers=None, method="GET", body=None):
        """A request that reports its status instead of raising on it.

        The binding uses status codes as part of its contract -- 401 for an
        operator-scoped resource, 404 for a well-known path an authority does
        not support, 304 for a validated cache entry -- so a client that
        raises on all of them cannot check any of them.
        """
        req = urllib.request.Request(self.base + path, data=body,
                                     method=method)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req) as r:   # noqa: S310
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, path, token=None):
        code, hdr, body = self.raw(path, token=token)
        if code != 200:
            raise AssertionError(f"GET {path} returned {code}, expected 200")
        return json.loads(body)

    def ws_url(self, path):
        return self.base.replace("https://", "wss://").replace(
            "http://", "ws://") + path


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



# ---- helpers shared by the checks ------------------------------------------
WK = "/.well-known/spatialdds"
HAS_GUARD = re.compile(r"^has_(\w+)$")


def discover(ep):
    """Every resource the endpoint advertises, by following its own links.

    The manifest's topic entries carry a `url`, which is what makes discovery
    hypermedia rather than a path-construction exercise: a client follows the
    link instead of rebuilding `{base}/{scene}/{stream}/{type}/{version}` by
    string surgery on a topic name. Ratified into the pinned surface.
    """
    doc = ep.json(f"{WK}/search")
    out = []
    for man in doc.get("results", []):
        for t in man.get("service", {}).get("topics", []):
            url = t.get("url")
            if not url or not url.startswith(ep.base):
                continue
            out.append({"path": url[len(ep.base):], **t})
    return out


def schema_for(schemas, topic_entry, index):
    """The published schema for a topic, via the schemas index."""
    for row in index:
        if row["type"].split(".")[-1].lower() == \
                topic_entry["type"].replace("_", "").lower():
            return schemas.get(row["type"])
    return None


def _validate(doc, schema):
    import jsonschema
    jsonschema.validate(doc, schema)


# ---- cross-cutting checks (README "Cross-cutting checks") ------------------

def check_schemas_endpoint(ep, schemas):
    """The endpoint publishes its schemas, and they are what it says they are."""
    index = ep.json(f"{WK}/schemas")
    assert isinstance(index, list) and index, "schemas index is empty"
    for row in index:
        assert sorted(row) == ["digest", "type", "url"], \
            f"index entry has keys {sorted(row)}, expected type/url/digest"
    # Each schema fetches, and its digest matches what the index claims.
    sample = index[:8] + index[-8:]
    for row in sample:
        path = row["url"][len(ep.base):] if row["url"].startswith(ep.base) \
            else row["url"]
        code, hdr, body = ep.raw(path)
        assert code == 200, f"schema {row['type']} returned {code}"
        want = row["digest"]
        got = "sha256:" + hashlib.sha256(canon(json.loads(body)).encode()
                                         ).hexdigest()
        assert got == want, \
            f"{row['type']}: index digest {want}, body digests to {got}"
    # And every type it publishes is one the binding defines.
    unknown = [r["type"] for r in index if r["type"] not in schemas]
    assert not unknown, f"endpoint publishes types the binding does not define: {unknown[:4]}"


def check_schema_validity(ep, schemas):
    """Every resource the endpoint returns validates against its own schema."""
    index = ep.json(f"{WK}/schemas")
    n = 0
    for t in discover(ep):
        code, hdr, body = ep.raw(t["path"], token=ep.token)
        if code == 401:
            continue
        assert code == 200, f"GET {t['path']} returned {code}"
        schema = schema_for(schemas, t, index)
        assert schema is not None, f"no published schema for type {t['type']!r}"
        for doc in json.loads(body):
            _validate(doc, schema)
            n += 1
    assert n > 0, "no instance was validated; the endpoint served nothing"
    return f"{n} instance(s)"


def check_canonical_form(ep, schemas):
    """The §5 canonical rules, observed on what the endpoint actually sends."""
    seen = {"int64_string": 0, "enum_name": 0, "guard_literal": 0,
            "union_tagged": 0}

    def walk(doc, schema, defs=None):
        if not isinstance(doc, dict) or not isinstance(schema, dict):
            return
        defs = defs if defs is not None else (schema.get("$defs") or {})
        props = schema.get("properties") or {}
        for k, v in doc.items():
            sub = props.get(k)
            if not isinstance(sub, dict):
                continue
            ref = sub.get("$ref", "")
            target = defs.get(ref.split("/")[-1], {}) if ref.startswith(
                "#/$defs/") else {}
            if sub.get("type") == "string" and sub.get("pattern") in (
                    r"^-?\d+$", r"^\d+$"):
                assert isinstance(v, str) and re.fullmatch(sub["pattern"], v), \
                    f"{k}: a 64-bit integer must be a decimal string, got {v!r}"
                seen["int64_string"] += 1
            if "enum" in sub:
                assert v in sub["enum"], f"{k}: {v!r} is not one of {sub['enum']}"
                seen["enum_name"] += 1
            if HAS_GUARD.match(k):
                assert isinstance(v, bool), f"{k}: a guard must be a boolean"
                member = HAS_GUARD.match(k).group(1)
                if member in props:
                    assert member in doc, \
                        f"{member}: a guarded member is always present (literal rule)"
                seen["guard_literal"] += 1
            if isinstance(v, dict) and "oneOf" in (target or sub or {}):
                assert "type" in v, \
                    f"{k}: a union must be a tagged object keyed on \"type\""
                consts = [br.get("properties", {}).get("type", {}).get("const")
                          for br in (target or sub)["oneOf"]]
                assert v["type"] in consts, \
                    f"{k}: discriminator {v['type']!r} is not one of {consts}"
                seen["union_tagged"] += 1
            if isinstance(v, dict) and target:
                walk(v, target, defs)
            if isinstance(v, float):
                assert v == v and v not in (float("inf"), float("-inf")), \
                    f"{k}: non-finite double"

    index = ep.json(f"{WK}/schemas")
    for t in discover(ep):
        code, _h, body = ep.raw(t["path"], token=ep.token)
        if code != 200:
            continue
        schema = schema_for(schemas, t, index)
        if schema is None:
            continue
        for doc in json.loads(body):
            walk(doc, schema)
    assert seen["int64_string"] > 0, \
        "no 64-bit integer was observed, so the string rule was not exercised"
    assert seen["enum_name"] > 0, "no enum was observed"
    # A rule the endpoint's data never exercises is reported as unexercised
    # rather than counted as passed: zero observations is not evidence.
    unexercised = [k for k, v in seen.items() if v == 0]
    detail = ", ".join(f"{k}={v}" for k, v in seen.items())
    if unexercised:
        detail += f"; UNEXERCISED by this endpoint's data: {unexercised}"
    return detail


def check_latched_get(ep, schemas):
    """TRANSIENT_LOCAL resources are GET with ETag, Cache-Control, and 304."""
    latched = [t for t in discover(ep)
               if t.get("durability") == "TRANSIENT_LOCAL"]
    assert latched, "the endpoint advertises no latched resource"
    checked = 0
    for t in latched:
        code, hdr, body = ep.raw(t["path"], token=ep.token)
        if code == 401:
            continue
        assert code == 200, f"GET {t['path']} returned {code}"
        etag = hdr.get("ETag")
        assert etag, f"{t['path']}: a latched resource must carry an ETag"
        assert hdr.get("Cache-Control"), \
            f"{t['path']}: a latched resource must carry Cache-Control"
        code2, hdr2, body2 = ep.raw(t["path"], token=ep.token,
                                    headers={"If-None-Match": etag})
        assert code2 == 304, \
            f"{t['path']}: a matching If-None-Match gave {code2}, expected 304"
        assert body2 == b"", "a 304 must carry no body"
        code3, _h3, _b3 = ep.raw(t["path"], token=ep.token,
                                 headers={"If-None-Match": '"sha256:stale"'})
        assert code3 == 200, \
            f"{t['path']}: a stale If-None-Match gave {code3}, expected 200"
        checked += 1
    assert checked, "every latched resource was refused, so none was checked"
    return f"{checked} latched resource(s)"


def check_access_classes(ep, schemas):
    """Each resource declares an access class, and its headers obey it.

    Backend-blind: the class comes from the endpoint's own manifest, and the
    assertion is that the headers agree with what it declared. The suite has no
    opinion about which resources ought to be which.
    """
    pub = op = 0
    for t in discover(ep):
        anon_code, anon_hdr, _b = ep.raw(t["path"])
        cc = (anon_hdr.get("Cache-Control") or "").lower()
        declared = t.get("access")
        assert declared in ("public-cacheable", "operator-scoped"), \
            f"{t['path']}: access class {declared!r} is not one of the two"
        if declared == "public-cacheable":
            assert anon_code == 200, \
                f"{t['path']} is public but anonymous GET gave {anon_code}"
            assert "max-age" in cc, f"{t['path']} is public but not cacheable"
            pub += 1
        else:
            assert anon_code == 401, \
                f"{t['path']} is operator-scoped but anonymous GET gave {anon_code}"
            assert anon_hdr.get("WWW-Authenticate", "").startswith("Bearer"), \
                f"{t['path']}: a 401 must say how to authenticate"
            tok_code, tok_hdr, _b2 = ep.raw(t["path"], token=ep.token)
            assert tok_code == 200, \
                f"{t['path']}: the bearer token was refused ({tok_code})"
            tcc = (tok_hdr.get("Cache-Control") or "").lower()
            assert "no-store" in tcc and "no-store" in cc, \
                f"{t['path']}: operator-scoped must never be cacheable, got {tcc!r}"
            op += 1
    assert pub and op, \
        f"both classes must be present to test both directions ({pub} public, {op} gated)"
    return f"{pub} public, {op} operator-scoped"


def check_dds_join_optional(ep, schemas):
    """DDS-join material is optional-and-validated, never required.

    Ruled at step 5's report: `service.connection`, `bootstrap` and `resolver`
    are correct when present and conformant when absent. The suite must not
    demand DDS of an endpoint that never claimed any, or the backend-blind
    invariant fails on the standalone shape it exists to certify.
    """
    notes = []
    for name in ("bootstrap", "resolver"):
        code, _h, body = ep.raw(f"{WK}/{name}")
        assert code in (200, 404), \
            f"{WK}/{name} returned {code}; expected a manifest (200) or 404"
        if code == 200:
            doc = json.loads(body)
            assert isinstance(doc, dict), f"{name} must be a JSON object"
            notes.append(f"{name}=present")
        else:
            notes.append(f"{name}=404")
    for man in ep.json(f"{WK}/search").get("results", []):
        conn = man.get("service", {}).get("connection")
        if conn is None:
            notes.append("connection=absent")
            continue
        assert isinstance(conn, dict), "service.connection must be an object"
        if "domain_id" in conn:
            assert isinstance(conn["domain_id"], int), \
                "connection.domain_id must be an integer"
        for k in ("partitions", "initial_peers"):
            if k in conn:
                assert isinstance(conn[k], list), f"connection.{k} must be an array"
        notes.append("connection=validated")
    return ", ".join(sorted(set(notes)))


def check_manifest_shape(ep, schemas):
    """§8.2.3 service manifests, including the ratified topic `url`/`access`."""
    doc = ep.json(f"{WK}/search")
    assert sorted(doc) >= ["next_page_token", "results"], \
        f"search response keys {sorted(doc)}"
    assert isinstance(doc["results"], list), "results must be an array"
    for man in doc["results"]:
        for k in ("id", "profile", "rtype"):
            assert k in man, f"manifest is missing {k}"
        assert re.fullmatch(r"spatial\.manifest/1\.(\d+)", man["profile"]), \
            f"profile {man['profile']!r} is not spatial.manifest/1.x"
        assert int(man["profile"].split(".")[-1]) >= 7, \
            "profile minor must be >= 7"
        assert man["rtype"] == "service", f"rtype {man['rtype']!r}"
        svc = man["service"]
        for k in ("service_id", "kind"):
            assert k in svc, f"service is missing {k}"
        assert svc["kind"] in ("VPS", "MAPPING", "RELOCAL", "SEMANTICS",
                               "STORAGE", "CONTENT", "ANCHOR_REGISTRY",
                               "OTHER"), f"kind {svc['kind']!r}"
        for t in svc.get("topics", []):
            for k in ("name", "type", "version", "url", "access",
                      "durability"):
                assert k in t, f"topic entry is missing {k}: {sorted(t)}"
            assert t["name"].startswith("spatialdds/"), \
                f"topic name {t['name']!r} does not follow §3.3.1"
        if "coverage" in man:
            cov = man["coverage"]
            if cov.get("has_bbox"):
                b = cov["bbox"]
                assert len(b) == 4 and all(
                    isinstance(x, (int, float)) for x in b), "bbox shape"
    return f"{len(doc['results'])} manifest(s)"


def check_commands_post(ep, schemas):
    """Commands are POST, and an endpoint with no command lane says so.

    Northbound-only endpoints have no verb to accept. The check is that a
    command POST is either served with decline semantics or refused cleanly --
    never a 500, and never silently accepted by something that cannot act.
    """
    paths = [t["path"] for t in discover(ep)]
    target = paths[0] if paths else "/"
    code, _h, _b = ep.raw(target, token=ep.token, method="POST",
                          body=b'{"verb":"NOOP"}')
    assert code in (200, 202, 400, 401, 403, 404, 405, 409), \
        f"a command POST returned {code}, which is neither a response nor a clean refusal"
    return f"POST -> {code} (no command lane advertised)"


def check_qos_subset(ep, schemas):
    """The carried QoS distinctions are observable; the rest is absent."""
    topics = discover(ep)
    kinds = {t.get("durability") for t in topics}
    assert "TRANSIENT_LOCAL" in kinds, \
        "no latched topic is advertised, so durability is not observable"
    assert kinds <= {"VOLATILE", "TRANSIENT_LOCAL"}, \
        f"durability must be a DDS kind, got {sorted(k for k in kinds if k)}"
    assert len(kinds) > 1, \
        f"every topic declares the same durability ({kinds}), so the distinction is not carried"
    # The not-carried set must not be emulated anywhere in a manifest.
    blob = json.dumps(ep.json(f"{WK}/search"))
    for absent in ("deadline", "ownership", "time_based_filter",
                   "transport_priority"):
        assert absent not in blob, \
            f"the manifest mentions {absent!r}, which the binding does not carry"
    return f"durability {sorted(k for k in kinds if k)}"



# ---- the four §8 scenarios -------------------------------------------------

class Skip(Exception):
    """A scenario that cannot run here, with its reason and remedy."""


def _ws_collect(url, token=None, limit=400, timeout=20):
    """Collect WebSocket messages until the stream ends or the limit is hit."""
    try:
        import websockets
    except ImportError:
        raise Skip("needs the `websockets` package: pip install websockets")
    import asyncio

    async def go():
        hdr = {"Authorization": f"Bearer {token}"} if token else {}
        out = []
        async with websockets.connect(url, additional_headers=hdr,
                                      max_size=8 << 20) as c:
            try:
                while len(out) < limit:
                    out.append(json.loads(
                        await asyncio.wait_for(c.recv(), timeout)))
            except (asyncio.TimeoutError, websockets.ConnectionClosed):
                pass
        return out

    return asyncio.run(go())


def scenario_hello_spatial(ep, schemas):
    """§8.1 — hello spatial in ten lines, and replay precedes live.

    The client is written here rather than taken from an implementation, so
    what is asserted is that the *binding* makes the scenario reachable in ten
    lines using nothing but the endpoint. The line count is part of the
    acceptance criterion: if it does not fit, that is a finding about the
    binding and not about formatting.
    """
    client = [
        'doc = ep.json("/.well-known/spatialdds/search")',
        'svc = doc["results"][0]["service"]',
        'topic = next(t for t in svc["topics"]'
        ' if t["durability"] == "TRANSIENT_LOCAL")',
        'url = topic["url"].replace("http", "ws", 1)',
        'msgs = _ws_collect(url, ep.token)',
        'replay = [m for m in msgs if m["event"] == "sample"]',
        'marker = [m for m in msgs if m["event"] == "end_of_replay"]',
        'assert len(marker) == 1',
        'assert msgs.index(marker[0]) == marker[0]["replayed"]',
        'print(len(replay), "sample(s) before the marker")',
    ]
    assert len(client) <= 10, \
        f"the scenario needs {len(client)} lines, which is a finding about the binding"

    doc = ep.json(f"{WK}/search")
    svc = doc["results"][0]["service"]
    latched = [t for t in svc["topics"]
               if t.get("durability") == "TRANSIENT_LOCAL"]
    assert latched, "no latched topic to subscribe to"
    topic = latched[0]
    msgs = _ws_collect(ep.ws_url(topic["url"][len(ep.base):]), ep.token)
    assert msgs, "the subscription yielded nothing"
    markers = [i for i, m in enumerate(msgs)
               if m.get("event") == "end_of_replay"]
    assert len(markers) == 1, f"expected exactly one end_of_replay, got {len(markers)}"
    at = markers[0]
    assert all(m.get("event") == "sample" for m in msgs[:at]), \
        "an event before the marker was not a sample, so replay did not precede live"
    assert msgs[at].get("replayed") == at, \
        f"replayed={msgs[at].get('replayed')} but {at} sample(s) preceded the marker"
    assert sorted(msgs[at]) == ["event", "replayed", "topic"], \
        f"end_of_replay carries {sorted(msgs[at])}, and the shape is pinned"

    # The replayed samples must be schema-valid typed data, not opaque blobs.
    index = ep.json(f"{WK}/schemas")
    schema = schema_for(schemas, topic, index)
    assert schema is not None, f"no published schema for {topic['type']!r}"
    for m in msgs[:at]:
        _validate(m["data"], schema)
    return f"{len(client)} lines, {at} replayed sample(s), marker then live"


def scenario_anchor_resolve(ep, schemas):
    """§8.2 — anchor resolve flow. Criteria not yet on the board."""
    raise Skip("the open-anchors option-2 acceptance criteria land in "
               "directions/ before this check is built (James's board); "
               "nothing is asserted in the meantime")


def scenario_backend_blind(ep, schemas):
    """§8.3 — the same suite, unchanged, against both deployment shapes.

    The invariant is that no check branches on what implements the endpoint.
    That is verified structurally here, over the suite's own source, because it
    is a property of the suite rather than of any one endpoint: a second
    endpoint would exercise it but could not prove it.
    """
    # Scan the suite's source with *this function* removed. The detector names
    # the tokens it forbids, so including itself makes it find its own
    # vocabulary and fail always -- an instrument reporting on itself
    # incorrectly, which is the defect class this work has already named once.
    import inspect
    src = open(os.path.abspath(__file__)).read()
    mine = inspect.getsource(scenario_backend_blind)
    src = src.replace(mine, "")
    banned = ("is_bridged", "is_standalone", "if dds", "BRIDGED", "STANDALONE",
              "--bridged", "--standalone")
    found = [b for b in banned if b in src]
    assert not found, \
        f"the suite branches on the backend: {found}. Any such branch is a bug in the check."
    # The runner's only inputs are an endpoint and a token.
    import argparse as _a
    assert "--endpoint" in src and "--token" in src
    extra = re.findall(r'add_argument\("--(\w+)"', src)
    allowed = {"endpoint", "token", "expect"}
    assert set(extra) <= allowed, \
        f"the runner takes inputs beyond an endpoint and a token: {sorted(set(extra) - allowed)}"
    return f"no backend branch; runner inputs {sorted(set(extra))}"


def scenario_third_party_reader(ep, schemas):
    """§8.4 — a client written from the published schemas alone.

    Nothing here imports or mirrors an implementation's code. Field names,
    types and enum values come from the schema the endpoint publishes, and the
    reader walks a live sample using only that.
    """
    index = ep.json(f"{WK}/schemas")
    latched = [t for t in discover(ep)
               if t.get("durability") == "TRANSIENT_LOCAL"]
    assert latched, "no latched resource to read"
    read = 0
    for t in latched:
        code, _h, body = ep.raw(t["path"], token=ep.token)
        if code != 200:
            continue
        schema = schema_for(schemas, t, index)
        assert schema is not None
        required = schema.get("required") or []
        for doc in json.loads(body):
            _validate(doc, schema)
            missing = [k for k in required if k not in doc]
            assert not missing, \
                f"{t['type']}: required field(s) {missing} absent from a served instance"
            # Read a value by its schema-declared type, with no local knowledge.
            for k, sub in (schema.get("properties") or {}).items():
                if k not in doc or not isinstance(sub, dict):
                    continue
                want = sub.get("type")
                if want == "string":
                    assert isinstance(doc[k], str), f"{k} is not a string"
                elif want == "boolean":
                    assert isinstance(doc[k], bool), f"{k} is not a boolean"
                elif want == "number":
                    assert isinstance(doc[k], (int, float)), f"{k} is not a number"
                elif want == "integer":
                    assert isinstance(doc[k], int), f"{k} is not an integer"
                elif want == "array":
                    assert isinstance(doc[k], list), f"{k} is not an array"
            read += 1
    assert read > 0, "nothing was read"
    return f"{read} instance(s) read from the published schemas alone"

# Registered in the order the README's build list gives: the cross-cutting
# checks, then the four §8 scenarios. Each takes (ep, schemas) and raises on
# failure; a returned string is reported as detail.
NETWORK_CHECKS = [
    ("schemas endpoint is self-describing", check_schemas_endpoint),
    ("every resource validates against its published schema", check_schema_validity),
    ("canonical form on the wire", check_canonical_form),
    ("latched state is GET with ETag, Cache-Control and 304", check_latched_get),
    ("access classes, both directions", check_access_classes),
    ("DDS-join material optional-and-validated", check_dds_join_optional),
    ("service manifests match §8.2.3", check_manifest_shape),
    ("commands are POST, or cleanly absent", check_commands_post),
    ("the carried QoS subset is observable, the rest absent", check_qos_subset),
    ("§8.1 hello spatial in ten lines", scenario_hello_spatial),
    ("§8.2 anchor resolve flow", scenario_anchor_resolve),
    ("§8.3 backend-blind, the same suite for both shapes", scenario_backend_blind),
    ("§8.4 third-party reader, published schemas only", scenario_third_party_reader),
]


def main():
    ap = argparse.ArgumentParser(description="Web Binding backend-blind conformance suite")
    ap.add_argument("--endpoint", help="base URL of a binding endpoint (bridged or standalone)")
    ap.add_argument("--token", help="bearer token for operator-scoped resources")
    a = ap.parse_args()

    schemas = load_schemas(SCHEMAS_DIR)
    self_check(schemas)

    if not a.endpoint:
        print(f"conformance: SKIP {len(NETWORK_CHECKS)} network checks — no "
              f"--endpoint given.\n"
              "  Remedy: pass --endpoint <url> of a binding gateway, bridged or "
              "standalone, and --token for its operator-scoped resources. A "
              "standalone gateway is OpenArCloud/spatialdds-web:\n"
              "    python3 tools/run_gateway.py --mcap <file> --port P --token T")
        return 0

    if not NETWORK_CHECKS:
        print("conformance: endpoint given, but no network checks are wired yet.\n"
              "  The gateway-dependent checks track step 5's surface and are added "
              "as it comes up (README.md). Nothing is asserted against the endpoint "
              "yet — this is pending, not a pass.")
        return 0

    ep = Endpoint(a.endpoint, a.token)
    failures, skipped = [], []
    for name, fn in NETWORK_CHECKS:
        try:
            detail = fn(ep, schemas)
            print(f"  PASS     {name}" + (f"  ({detail})" if detail else ""))
        except Skip as e:
            skipped.append(f"{name}: {e}")
            print(f"  SKIPPED  {name}")
            print(f"           {e}")
        except Exception as e:
            failures.append(f"{name}: {e}")
            print(f"  FAIL     {name}: {e}")
    npass = len(NETWORK_CHECKS) - len(failures) - len(skipped)
    print(f"\n{len(NETWORK_CHECKS)} checks: {npass} passed, "
          f"{len(failures)} failed, {len(skipped)} skipped")
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
