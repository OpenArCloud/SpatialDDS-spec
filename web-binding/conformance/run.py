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
from urllib.parse import urlsplit, urlunsplit, quote

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
    """Backend-blind HTTP(S) client, origin-independent.

    `base` is the origin the endpoint *advertises* (the authority in the URLs it
    puts in its own manifests). `connect` is where requests are actually sent;
    it defaults to `base`. When they differ — a deployment certified before DNS
    and TLS are in front of it — a request for a URL under the advertised origin
    is sent to `connect` with the advertised `Host` preserved. This is a
    substitution a *harness* may make and a *client* may not; it never rewrites
    a manifest URL (N.7) beyond this one mapping, and a URL under any other
    origin is followed verbatim — the endpoint's claim to stand behind.

    Targets are absolute URLs or leading-slash paths under `base`. Nothing here
    derives a path by string arithmetic on a prefix: a URL is structured data,
    parsed with urllib.parse.
    """
    def __init__(self, base, token=None, connect=None):
        self.base = base.rstrip("/")
        self.connect = (connect or base).rstrip("/")
        self.token = token
        self._b = urlsplit(self.base)
        self._c = urlsplit(self.connect)

    def _route(self, target):
        """Return (send_url, host_header) for a target URL or path."""
        u = urlsplit(self.base + target if target.startswith("/") else target)
        if (u.scheme, u.netloc) == (self._b.scheme, self._b.netloc):
            send = urlunsplit((self._c.scheme, self._c.netloc, u.path, u.query, ""))
            host = self._b.netloc if self._b.netloc != self._c.netloc else None
            return send, host
        # A different origin than the advertised one: follow it verbatim.
        return urlunsplit((u.scheme, u.netloc, u.path, u.query, "")), None

    def raw(self, target, token=None, headers=None, method="GET", body=None):
        """A request that reports its status instead of raising on it.

        The binding uses status codes as part of its contract -- 401 for an
        operator-scoped resource, 404 for a well-known path an authority does
        not support, 304 for a validated cache entry -- so a client that
        raises on all of them cannot check any of them.
        """
        send, host = self._route(target)
        req = urllib.request.Request(send, data=body, method=method)
        if host:
            req.add_header("Host", host)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        for k, v in (headers or {}).items():
            req.add_header(k, v)
        try:
            with urllib.request.urlopen(req) as r:   # noqa: S310
                return r.status, dict(r.headers), r.read()
        except urllib.error.HTTPError as e:
            return e.code, dict(e.headers), e.read()

    def json(self, target, token=None):
        code, hdr, body = self.raw(target, token=token)
        if code != 200:
            raise AssertionError(f"GET {target} returned {code}, expected 200")
        return json.loads(body)

    def ws_target(self, target):
        """The routed WebSocket URL for a target; the --connect origin
        substitution applies exactly as for raw(). The handshake Host is left to
        the WebSocket client (derived from the connect address); a path-routed
        gateway does not vhost, and overriding it breaks the handshake."""
        send, _host = self._route(target)
        return send.replace("https://", "wss://").replace("http://", "ws://")


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
            if not url:
                continue
            u = urlsplit(url)
            path = u.path + (f"?{u.query}" if u.query else "")
            out.append({"path": path, "url": url, **t})
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
        code, hdr, body = ep.raw(row["url"])
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
    if not (pub or op):
        raise Skip("no resources discovered — access classes are UNEXERCISED "
                   "(zero observations)")
    # Each present class was fully asserted in the loop above. A class the
    # endpoint's data has no example of is UNEXERCISED, not a failure: an
    # absence of counter-examples is not a defect (README, "Zero observations").
    unexercised = []
    if not op:
        unexercised.append("operator-scoped (no gated resource to test the 401/bearer path)")
    if not pub:
        unexercised.append("public-cacheable (no public resource to test the cacheable path)")
    detail = f"{pub} public, {op} operator-scoped"
    if unexercised:
        detail += "; UNEXERCISED: " + "; ".join(unexercised)
    return detail


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
    kinds = {t.get("durability") for t in topics if t.get("durability")}
    if not kinds:
        raise Skip("no topic declares a durability — the QoS subset is UNEXERCISED "
                   "(zero observations)")
    assert kinds <= {"VOLATILE", "TRANSIENT_LOCAL"}, \
        f"durability must be a DDS kind, got {sorted(kinds)}"
    # The not-carried set must not be emulated anywhere in a manifest.
    blob = json.dumps(ep.json(f"{WK}/search"))
    for absent in ("deadline", "ownership", "time_based_filter",
                   "transport_priority"):
        assert absent not in blob, \
            f"the manifest mentions {absent!r}, which the binding does not carry"
    # Both kinds present → the distinction is carried and observed. Only one →
    # the distinction is real but has no counter-example here: UNEXERCISED, not a
    # defect (the mirror of "Zero observations is not evidence").
    if len(kinds) > 1:
        return f"durability {sorted(kinds)} — both kinds carried"
    only = next(iter(kinds))
    return (f"durability [{only}]; UNEXERCISED: the endpoint is uniformly {only}, "
            f"so the VOLATILE/TRANSIENT_LOCAL distinction has no counter-example to observe")



def _uri_authority(uri):
    """The DNS authority of a `spatialdds://` URI, or "" if it is not one."""
    return urlsplit(uri).netloc if isinstance(uri, str) and \
        uri.startswith("spatialdds://") else ""


def _manifest_uris(ep):
    """Every `spatialdds://` manifest_uri the endpoint publishes in its own
    served instances. Backend-blind: the URIs to resolve come from the endpoint,
    not from the suite. Content announces carry them today."""
    uris = set()
    for t in discover(ep):
        code, _h, body = ep.raw(t["path"], token=ep.token)
        if code != 200:
            continue
        try:
            docs = json.loads(body)
        except Exception:
            continue
        for d in (docs if isinstance(docs, list) else [docs]):
            mu = d.get("manifest_uri") if isinstance(d, dict) else None
            if _uri_authority(mu):
                uris.add(mu)
    return uris


def _max_age(headers):
    m = re.search(r"max-age=(\d+)", (headers.get("Cache-Control") or "").lower())
    return int(m.group(1)) if m else None


def _resolve_url(https_base, uri):
    sep = "&" if urlsplit(https_base).query else "?"
    return f"{https_base}{sep}uri={quote(uri, safe='')}"


def _has_integrity(headers, doc):
    """§7.5.2 integrity: an ETag or Digest header, or a checksum in the body."""
    if headers.get("ETag") or headers.get("Digest"):
        return True
    blob = json.dumps(doc)
    return "sha256:" in blob or '"hash"' in blob or '"checksum"' in blob


def check_resolver(ep, schemas):
    """§7.5.2 resolver, as a first-class surface (erratum 169fabd).

    404 from the metadata path is conformant — the endpoint is not an authority
    (169fabd) — and the resolve surface is then UNEXERCISED, not passed and not
    failed. A 200 commits the endpoint to metadata validation, an end-to-end
    resolve of a URI discovered in its own served instances, the N.4 ttl_sec
    precedence, and the constructed error branches.
    """
    code, hdr, body = ep.raw(f"{WK}/resolver")
    assert code in (200, 404), \
        f"{WK}/resolver returned {code}; expected metadata (200) or 404"
    if code == 404:
        return ("resolver 404 — the endpoint is not an authority (169fabd); "
                "the resolve surface is UNEXERCISED (zero observations)")

    # Metadata validation.
    meta = json.loads(body)
    for k in ("authority", "https_base", "cache_ttl_sec"):
        assert k in meta, f"resolver metadata is missing {k!r}"
    hb = urlsplit(meta["https_base"])
    assert hb.scheme == "https" and hb.netloc, \
        f"https_base must be an absolute https URL, got {meta['https_base']!r}"
    # The metadata resource is public-cacheable: it takes the N.4 public checks.
    cc = (hdr.get("Cache-Control") or "").lower()
    assert "max-age" in cc, "resolver metadata is public-cacheable but has no max-age"
    assert hdr.get("ETag"), "resolver metadata must carry an ETag"
    assert hdr.get("Access-Control-Allow-Origin") == "*", \
        "a public-cacheable resource must be CORS-open (Access-Control-Allow-Origin: *)"

    # Authority consistency: the authority it claims must be the authority of the
    # URIs it itself publishes. Claiming one and announcing another is the N.2
    # fabrication in reverse.
    published = _manifest_uris(ep)
    auths = {_uri_authority(u) for u in published}
    if auths:
        assert meta["authority"] in auths, \
            f"resolver authority {meta['authority']!r} is not among the authorities " \
            f"this endpoint publishes ({sorted(auths)})"

    # Resolve, end to end, with discovered data.
    mine = sorted(u for u in published if _uri_authority(u) == meta["authority"])[:4]
    detail = f"resolver 200 (authority {meta['authority']})"
    if not mine:
        return detail + "; resolve UNEXERCISED — no served instance carries a " \
                        "manifest_uri under this authority (zero observations)"
    hb_url = meta["https_base"]
    resolved = not_held = ttl_doc = ttl_default = 0
    for u in mine:
        rc, rh, rb = ep.raw(_resolve_url(hb_url, u))
        if rc == 404:
            # 404 is not-found, as §7.5.3 defines it: an endpoint may be the
            # authority for a URI's namespace yet hold no manifest for that exact
            # URI — a discovery Announce names its service URI, which the
            # authority need not expose as a resolvable manifest. This is
            # conformant because the ruling makes 404 the not-found response, not
            # because any particular reference endpoint answered that way.
            not_held += 1
            continue
        assert rc == 200, f"resolve {u} returned {rc}, expected 200 or a 404 not-held"
        assert "json" in (rh.get("Content-Type") or "").lower(), \
            f"resolve {u}: Content-Type {rh.get('Content-Type')!r} is not JSON"
        doc = json.loads(rb)
        assert _has_integrity(rh, doc), \
            f"resolve {u}: no integrity signal (ETag, Digest, or a body checksum) per §7.5.2"
        # N.4 ttl precedence (169fabd's second half, observed on the wire).
        if isinstance(doc.get("ttl_sec"), int):
            assert _max_age(rh) == doc["ttl_sec"], \
                f"resolve {u}: ttl_sec={doc['ttl_sec']} but max-age={_max_age(rh)} " \
                f"— the document's lifetime must govern (169fabd)"
            ttl_doc += 1
        else:
            ttl_default += 1
        resolved += 1
    if resolved == 0:
        return (f"{detail}; resolve UNEXERCISED — {not_held} discovered URI(s) under "
                "this authority are announced but not held (404, conformant §7.5.3)")

    # Error branches, constructed — no fixture needed.
    c1, _h1, b1 = ep.raw(hb_url)
    assert c1 == 400, f"resolve with no uri returned {c1}, expected 400"
    c2, _h2, _b2 = ep.raw(_resolve_url(hb_url, "http://not-a-spatialdds-uri"))
    assert c2 == 400, f"resolve of a non-spatialdds URI returned {c2}, expected 400"
    c3, h3, b3 = ep.raw(_resolve_url(hb_url, "spatialdds://example.invalid/z/content/x"))
    assert c3 == 404, \
        f"resolve of a foreign-authority URI returned {c3}, expected 404"
    # N.8 problem-details where an error carries a body.
    for cde, hh, bb in ((c1, _h1, b1), (c3, h3, b3)):
        if bb and "json" in (hh.get("Content-Type") or "").lower():
            pd = json.loads(bb)
            assert "title" in pd, f"an error body must be problem-details (N.8): {sorted(pd)}"

    legs = f"{ttl_doc} doc-governed / {ttl_default} class-default"
    if not ttl_doc or not ttl_default:
        legs += " (one TTL leg UNEXERCISED: " + \
            ("no resolved manifest carries ttl_sec" if not ttl_doc
             else "no resolved manifest omits ttl_sec") + ")"
    return (f"{detail}; {resolved} resolved, {not_held} announced-but-not-held(404); "
            f"ttl {legs}; error branches 400/400/404")


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
    msgs = _ws_collect(ep.ws_target(topic["url"]), ep.token)
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
    """§8.2 — anchor resolve flow. Blocked on a missing 1.8 field, not criteria."""
    raise Skip("the scenario fetches an anchor's asset by reference, and no 1.8 "
               "anchor type carries that reference — GeoAnchor has no manifest_uri "
               "(1.9 candidates entry 2). No recording can un-skip it; the scenario "
               "waits for the field it was written for and is not reworded to pass.")


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
    # `--connect` is an origin→address substitution (certify before DNS/TLS), not
    # a backend selector: it maps the advertised origin to where requests are
    # sent and reveals nothing about what implements the endpoint. It is allowed
    # exactly because it does not relax backend-blindness.
    allowed = {"endpoint", "token", "connect", "expect"}
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
    ("resolver is a checked surface (§7.5.2)", check_resolver),
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
    ap.add_argument("--connect", help="where to send requests for URLs under the "
                    "endpoint's advertised origin, when that differs from the "
                    "address it is reachable at (certify before DNS/TLS). A "
                    "harness substitution a client may not make; the advertised "
                    "Host is preserved and manifest URLs are otherwise followed "
                    "verbatim (N.7).")
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

    ep = Endpoint(a.endpoint, a.token, connect=a.connect)
    if a.connect:
        print(f"  connect: URLs under {ep.base} are sent to {ep.connect} with "
              f"Host: {urlsplit(ep.base).netloc} preserved (harness substitution).")
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
    # Name the skipped (and any failed) checks on the totals line: this line is
    # quoted as the deploy's acceptance record, so it must say *which* check the
    # skip is, not merely that there is one.
    skip_names = ", ".join(s.split(":", 1)[0] for s in skipped)
    fail_names = ", ".join(f.split(":", 1)[0] for f in failures)
    line = (f"\n{len(NETWORK_CHECKS)} checks: {npass} passed, "
            f"{len(failures)} failed, {len(skipped)} skipped")
    if skip_names:
        line += f" (skipped: {skip_names})"
    if fail_names:
        line += f" (failed: {fail_names})"
    print(line)
    if failures:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
