# Web Binding — Conformance Suite (backend-blind)

Step 6 of the web-binding brief: the suite that certifies an endpoint speaks the
binding. It lives in the spec repo because it *is* the binding's conformance
definition. This file is the stable definition; the runnable network checks are
built against the gateway as it comes up (step 5, sidecar repo), so the concrete
HTTP/WS request/response details are not encoded here ahead of that gateway.

## The one invariant: backend-blind

The suite runs against an endpoint — a base URL plus an optional bearer token —
and **cannot tell whether a DDS bus or a web-native implementation is behind it.**
No flag selects "bridged" or "standalone"; any check that would need to know
which is behind the endpoint is a bug in the check. That blindness is the design
requirement that keeps the two deployment shapes (brief §3) from drifting apart:
the same suite, byte-for-byte, must pass against both.

Invocation (skips clean with reason and remedy when no endpoint is given,
matching the gates):

```sh
python3 web-binding/conformance/run.py --endpoint https://host/… [--token T]
```

### Origin independence — the `--connect` substitution

An endpoint advertises an origin: the authority in the URLs it puts in its own
manifests. Before DNS and TLS are in front of it, that origin is not yet where
the process can be reached. `--connect <base>` maps the advertised origin to a
connect address: a request for a URL under the advertised origin is sent to
`<base>` with the advertised `Host` preserved, and a URL under any other origin
is followed verbatim (N.7 — the endpoint's claim is not ours to rewrite). It is
URL-structured routing, never string arithmetic on a prefix.

```sh
# certify a deployment advertising demo.spatialdds.org while it runs on loopback
python3 web-binding/conformance/run.py \
    --endpoint https://demo.spatialdds.org --connect http://127.0.0.1:8802 --token T
```

This is a substitution **a harness may make and a client may not**. It exists so
a deployment can be certified before DNS and TLS are in front of it, it maps
origin to address and reveals nothing about what implements the endpoint (so it
does not relax backend-blindness), and **a run that used it says so in its
output header**. The WebSocket handshake `Host` is left to the client, derived
from the connect address: a path-routed gateway does not vhost, and overriding
it breaks the handshake.

## Pinned wire surface — now **Appendix N** of the specification

**This section is historical.** Step 7 moved the surface into the specification
proper, as *Appendix N: Web Binding (Normative)*, which is now the contract. The
items once marked **[invented]** here were ratified and are normative there:
the `schemas` paths, the latched-resource path mapping, the WebSocket envelope
field names, and `url`/`access` on a manifest topic entry.

Appendix N also carries what this section could not, because it was learned
afterwards from a second implementation: `closing` as a fifth event so a
subscription's end has a reason, an optional `as_of` on `end_of_replay`,
declared liveliness granularity, `application/problem+json` for errors, and
`service.connection`, `bootstrap` and `resolver` as optional-and-validated
rather than required.

What follows is kept as the record of what was pinned, and when, during step 5.
Where it differs from Appendix N, Appendix N governs.

### Well-known paths

- `GET|POST /.well-known/spatialdds/search` — discovery, incl. the geohash GET
  convenience form (`?geohash=&kind=`). **Existing** (§3.3.0); consolidated into
  the binding. This GET is the gated "geohash discovery GET" 1.8 item.
- `GET /.well-known/spatialdds/{bootstrap,resolver}` — **existing** (§3.3.0,
  §7.5.2); unchanged.
- `GET /.well-known/spatialdds/schemas` — index of published JSON Schemas:
  `[{"type":"<FQN>","url":"<schema url>","digest":"sha256:<hex>"}]`. **[invented]**
  (brief §6: an endpoint serves its schemas so it is self-describing; consistent
  with the existing `/.well-known/spatialdds` namespace, RFC 8615).
- `GET /.well-known/spatialdds/schemas/{type}` — the JSON Schema for one type
  (`{type}` = the schema file basename in `web-binding/schemas/`, e.g.
  `spatial_core_GeoAnchor`), content-digest pinned via `ETag`. **[invented]**

### Latched resource pattern

A latched (TRANSIENT_LOCAL) instance is a GET resource whose path mirrors the
on-bus topic name `spatialdds/<scene>/<stream>/<type>/<version>` (§3.3.1)
one-to-one: `GET {base}/{scene}/{stream}/{type}/{version}` returns the collection
(a JSON array of instances), and `.../{version}/{key}` returns one keyed instance.
Responses validate against the type's schema and carry `ETag` + `Cache-Control`
per the resource's access class (public-cacheable | operator-scoped). **[invented]**
the HTTP path mapping (derived from the §3.3.1 topic grammar so the on-bus and web
names are the same mental model); step 7 formalizes it.

### WebSocket subscription and event envelope

A subscription is a WebSocket opened to the collection URL above (WS upgrade).
Every message is a JSON object with an `event` field drawn from a fixed set of
four type names, and the ordering contract below. The four **event type names are
fixed** (`sample`, `end_of_replay`, `dispose`, `liveliness`); the envelope field
names and shapes are **[invented]** (semantics per brief §4 and §2.14):

```jsonc
{"event":"sample",        "topic":"<topic>", "key":"<key>", "data":{ …typed, schema-valid… }}
{"event":"end_of_replay", "topic":"<topic>", "replayed":<N>}        // exactly once; see below
{"event":"dispose",       "topic":"<topic>", "key":"<key>", "reason":"<human-readable>"}
{"event":"liveliness",    "topic":"<topic>", "key":"<key>", "alive":true|false}
```

- **Ordering (normative).** On subscribe the server sends zero or more `sample`
  events (the latched replay, current value per key), then **exactly one**
  `end_of_replay`, then live events. A client knows the latched set is complete
  only at `end_of_replay` — the marker the bus leaves implicit and the web must
  state.
- **`end_of_replay` exact shape:** `{"event":"end_of_replay","topic":"<topic>",
  "replayed":<N>}` where `N` is the count of `sample` events that preceded it in
  the replay phase (so a client can assert it received them all). No other fields.
- **Removal (normative, §2.14):** a deliberate removal is a `sample` event
  carrying the instance's terminal state, **immediately followed by** a `dispose`
  event for the same `key` with the reason. Liveliness loss is **not** removal and
  MUST NOT be sent as `dispose`.
- **`liveliness`** is an explicit event; a client MUST NOT infer liveliness or
  removal from the WS connection dropping.

### Invented here — the flag list for chosen names

Where a name this work chose sits until it is ratified. Items 1 to 3 were
flagged during step 5 and are **ratified**: they are normative in Appendix N.
Items 4 and 5 are names chosen during step 7, inside queue items that were
ruled, and are **flagged pending ratification** — the decision to add each was
made elsewhere; only the spelling is ours.

1. **Ratified.** `/.well-known/spatialdds/schemas[/{type}]` paths + index shape.
2. **Ratified.** The latched-resource HTTP path mapping
   (`{base}/{scene}/{stream}/{type}/{version}[/{key}]`).
3. **Ratified.** The WS event-envelope field names
   (`event`,`topic`,`key`,`data`,`replayed`,`reason`,`alive`) and the
   `end_of_replay.replayed` count. (The four event-type tokens themselves were
   fixed by direction, not invented here.)
4. **Pending.** `closing` as the fifth event-type token (Appendix N.5.4), and
   its `reason` and `code` members. That a subscription's end needs a terminal
   event carrying a reason was ruled; the token is a name we picked. The four
   original tokens were fixed by direction, so a fifth is the first addition to
   that set and the spelling should be deliberate.
5. **Pending.** The `liveliness` member on a manifest topic entry and its three
   values, `"per-key"`, `"per-writer"`, `"none"` (Appendix N.5.3). That
   granularity should be declared rather than assumed was ruled; the member
   name and the vocabulary are ours.

6. **Ratified, by removal.** `LIVE` as a `qos_profile` value meaning "not
   latched" is **gone**, and nothing replaced it that needed naming. A topic
   entry now carries a `durability` member taking the DDS kinds verbatim,
   `"VOLATILE"` or `"TRANSIENT_LOCAL"`, and `qos_profile` keeps its free-form
   §3.3.2 meaning untouched.

   Worth keeping as a record of how it was found. One review question — *is
   `LIVE` a defined term, or a token the gateway coined and the appendix
   inherited?* — turned up two defects for the price of one. `LIVE` appeared
   exactly once in the entire specification, in the appendix asserting it, so a
   reader could resolve it from neither DDS vocabulary nor existing text. And
   checking that exposed the larger problem the question had not asked about:
   `qos_profile` is already a free-form profile *name* in §3.3.2, carrying
   `VIDEO_LIVE` and `POSE_RT`, so durability carried there collided with an
   established use. The resolution invented no vocabulary at all, which is
   usually the sign that the first shape was carrying something that did not
   belong to it.

Also chosen rather than ruled, and recorded here for completeness: `url` and
`access` on a manifest topic entry were flagged at step 5 and ratified, and
`application/problem+json` (N.8) is an existing standard adopted rather than a
name invented, so neither needs a slot above.

## Zero observations is not evidence

A stated principle of this suite, and permanent vocabulary: **a rule the
endpoint's data never exercises reports UNEXERCISED, never a counted pass.**

It is here because the suite nearly broke it. The canonical-form check counted
the §5 rules it observed and asserted that some were non-zero; the tagged-union
count sat at zero, because the check did not resolve `$ref` and so never
reached the `CovMatrix` inside a `GeoPose`. A green row would have reported a
rule as satisfied on the strength of never having looked at it.

So a count of zero is now reported in the detail as UNEXERCISED and read as an
absence of evidence rather than evidence of conformance. An endpoint whose data
happens not to contain a union is not thereby conformant about unions; it is
untested about unions, and the manifest says which.

**The mirror: an absence of counter-examples is not a defect.** The same
principle run the other way. A check with a non-triviality guard — "both access
classes must appear", "both durability kinds must appear" — must not turn a
legitimately homogeneous endpoint into a failure. An anchor recording that is
all public and all latched has no operator-scoped resource and no volatile topic
to show, and that is a property of honest site data, not a conformance fault.
Such a check asserts everything the data *can* exercise (public resources are
served uncredentialed and cacheable; latched topics replay) and reports the
untested direction as UNEXERCISED, exactly as a zero count does — never as FAIL.
Zero observations is not evidence; zero counter-examples is not a defect. Both
are the manifest saying what it could not test.

This is the same discipline as a SKIPPED check, applied one level down: a check
that cannot run says so by name, and a rule that had nothing to run against
says so too.

## Cross-cutting checks (brief §4, §5, §7)

- **Schema validity.** Every resource an endpoint returns MUST validate against its
  published JSON Schema in `web-binding/schemas/`. This ties the suite to the
  generator's output — the same schemas gate 1 pins — so "conformant" means
  "matches the generated contract," not a hand-maintained parallel.
- **Canonical form.** int64/uint64 as decimal strings, doubles by ECMA-262,
  enums by name, unions as `{"type":…}` tagged objects, `has_*` literal (guards
  present as booleans, guarded members always present). Enforced by schema
  validation plus the canonical-form helpers reused from `gate_roundtrip.py`
  (`ecma262`, `canon`).
- **Latched state = GET.** TRANSIENT_LOCAL resources are HTTPS GET with `ETag` and
  `Cache-Control`. Each resource carries an explicit **access class**:
  public-cacheable (CDN-served) or operator-scoped (bearer, uncacheable). The
  check asserts cache headers follow the class mechanically and that auth and
  cacheability never contradict (an operator-scoped resource is never served
  cacheable).
- **Streams = WebSocket.** Subscribe → **latched replay, then an explicit
  end-of-replay marker, then live stream** (the marker is data the web must state;
  the bus leaves it implicit). **Removal** arrives as a final terminal sample with
  reason followed by an explicit **dispose** event; **liveliness** loss is an
  explicit event. None of removal/liveliness/caught-up is inferred from connection
  state.
- **Commands = POST.** Decline semantics carried in the response, per the
  keyed-command conventions (Appendix M.1).
- **QoS subset (§7).** The carried distinctions are observable (RELIABLE vs
  BEST_EFFORT, TRANSIENT_LOCAL-via-replay, KEEP_LAST(1)-per-key, keyed identity,
  removal, liveliness-as-events); the not-carried set (deadline, ownership,
  time-based filter, partitions, transport priority) is absent, not emulated.

## Scenarios (brief §8)

1. **Hello spatial in ten lines.** GET coverage by geohash → schema-valid service
   manifests; open one WS subscription → typed, schema-valid samples. Asserts the
   client is ≤10 lines and that latched replay precedes the live stream.
2. **Anchor resolve flow.** GET anchors near a geohash (schema-valid) → fetch an
   anchor's asset by reference → resolve on device. This is the open-anchors
   option-2 acceptance scenario; its criteria land in `directions/` before this
   check is built (James's board).
3. **Sidecar standalone.** The whole suite passes, unchanged, against the
   standalone gateway *and* a bridged DDS deployment. This is the backend-blind
   invariant exercised end to end.
4. **Third-party reader.** A client written from the published `web-binding/schemas/`
   alone — sharing none of our code — consumes a live endpoint correctly. The
   validation bar the rest of 1.8 already meets, applied to the binding.

## Build order within step 6 — done, with one scenario held

1. This definition (stable; here). **Done.**
2. The runner skeleton: argument handling, schema loader, backend-blind endpoint
   client, skip-clean without `--endpoint`. **Done.**
3. Cross-cutting checks, then the four scenarios. **Done**, nine checks and four
   scenarios, wired against the standalone gateway in
   `OpenArCloud/spatialdds-web`.

`§8.2 anchor resolve` SKIPs with its reason: the open-anchors option-2
acceptance criteria land in `directions/` before that check is built. Nothing is
asserted for it in the meantime, which is the point of printing the skip.

**The rulings this suite implements**, from step 5's report:

- **DDS-join material is optional-and-validated, never required.**
  `service.connection`, `bootstrap` and `resolver` are correct when present and
  conformant when absent (an omission, or a 404). The suite never demands DDS of
  an endpoint that never claimed any, which is what lets the standalone shape
  pass the suite that exists to certify it.
- **A topic entry's `url` and `access` are expected.** `TopicMeta` has no URL;
  adding one is what makes discovery hypermedia, so a client follows a link
  rather than rebuilding `{base}/{scene}/{stream}/{type}/{version}` by string
  surgery. Ratified into the pinned surface.
- **Error bodies are taken as found**, pending the RFC 7807
  `application/problem+json` evaluation at step 7. The suite asserts status
  codes and that a refusal says how to authenticate, not a body shape.

**Fault-injected before trusted**, against a deliberately broken endpoint: an
operator-scoped resource served cacheable, a suppressed `end_of_replay`, and a
renamed member on a served instance. Each is caught by the check that should
catch it. The renamed-member case is the one worth noting, because it is the
shape of finding 10: `additionalProperties: true` means a tolerant reader
accepts the wrong name silently, and the suite is what notices.

A green run against one shape is not certification. The same suite, unchanged,
passing against a bridged DDS deployment is the other half, and that half is
unexercised: there is no bridged endpoint yet. `§8.3` therefore verifies the
invariant structurally — that no check branches on the backend, and that the
runner takes nothing but an endpoint, a token, and the origin-routing
`--connect` (which maps origin to address and reveals no backend) — because that
is a property of the suite rather than of any one endpoint, and a second
endpoint would exercise it without proving it.

## Findings addressed (demo-agent reports, closed in this batch)

Both are instrument defects in this suite, created by erratum 169fabd making the
resolver a path an endpoint can be *required* to serve — the suite was written
when nobody served it. Origin is the demo agent's reports against
`spatialdds-web`.

- **Finding 22 — origin independence.** The suite derived paths by string
  arithmetic on the advertised base (`url[len(ep.base):]`), so an endpoint
  advertising one origin while reachable at another produced six failures that
  were the suite's, not the endpoint's (`Port could not be cast to integer value
  as '8812ds.org'`). All URL handling is now `urllib.parse`-structured, and the
  `--connect` substitution (above) certifies such a deployment before DNS/TLS.
  Closed.
- **Finding 21 — the resolver is a checked surface.** The suite accepted a
  resolver `200` and validated nothing inside; `https_base` appeared nowhere. The
  resolver is now first-class: metadata validation, an end-to-end resolve of a
  URI discovered in the endpoint's own served instances, the N.4 `ttl_sec`
  precedence observed on the wire, the constructed error branches (no-uri → 400,
  non-`spatialdds` → 400, foreign-authority → 404, N.8 problem-details), and
  authority consistency. A `404` metadata is conformant (not an authority,
  169fabd) and the resolve surface is then UNEXERCISED, not passed. Every leg is
  fault-injected — missing `https_base`, no integrity signal, `max-age` pinned
  against a document `ttl_sec`, a foreign-authority `200` — and each produces the
  FAIL it should. Closed.

**Totals, both reference shapes** (`spatialdds-web` at `cc881b5`, fountain-anchors
with `--manifests`): **14 checks — 13 passed, 0 failed, 1 skipped**, identical in
plain loopback and in advertise-`demo.spatialdds.org` + `--connect`-loopback.
This supersedes the earlier "13 checks, 12 passed, 1 skipped" as the deploy
checklist's acceptance line. The resolver check is UNEXERCISED on loopback (not
an authority) and fully exercised under `--connect`; it passes in both shapes,
never passing in one and failing in the other.
