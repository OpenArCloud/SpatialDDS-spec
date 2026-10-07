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

## Pinned wire surface (normative — the step-5 contract)

The gateway (step 5) **implements** this surface; it does not get to invent it. It
is pinned here, with the conformance definition, so the suite tests a fixed
contract rather than whatever the gateway happened to do. Step 7 moves it into
the binding spec text; until then this section is the contract the step-5
directive hands the demo agent. Grounded in existing spec where noted; every item
marked **[invented]** is a decision made here for lack of a prior one — flag for
step-7 ratification.

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

### Invented here — flag list for step 7 / the step-5 directive

1. `/.well-known/spatialdds/schemas[/{type}]` paths + index shape.
2. The latched-resource HTTP path mapping (`{base}/{scene}/{stream}/{type}/{version}[/{key}]`).
3. The WS event-envelope field names (`event`,`topic`,`key`,`data`,`replayed`,`reason`,`alive`) and the `end_of_replay.replayed` count.
   (The four event-type tokens themselves are fixed by direction, not invented here.)

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
runner takes nothing but an endpoint and a token — because that is a property of
the suite rather than of any one endpoint, and a second endpoint would exercise
it without proving it.
