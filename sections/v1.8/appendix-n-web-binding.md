## **Appendix N: Web Binding (Normative)**

A SpatialDDS participant joins a DDS domain. A browser cannot, and neither can
most of what people actually build on top of a spatial commons: a dashboard, a
phone, a serverless function, a CDN edge. This appendix defines how the same
typed content reaches them — HTTPS `GET` for state, a WebSocket for streams,
JSON on the wire — so that a client with `fetch` and a WebSocket reads
SpatialDDS without a DDS library, a domain, or a discovery handshake.

It is deliberately an **honest subset**, in the sense §7 already uses for QoS.
The binding carries the distinctions a web client can observe and act on, and
it does not emulate the ones it cannot. Where the bus leaves something implicit
that a web client has no way to infer, the binding makes it an explicit
message; where DDS offers something the web has no equivalent for, the binding
says so rather than approximating it.

**Two deployment shapes, one surface.** An endpoint may *bridge* a DDS domain,
or it may be *web-native*, serving content that never transited a bus. A client
MUST NOT be able to tell which, and nothing in this appendix permits an
endpoint to advertise which it is. That is not politeness: the moment a
conformance test can distinguish the two, the two drift, and the binding
becomes two bindings. Every normative requirement below is therefore written so
that a web-native endpoint can satisfy it.

This appendix was written last, from two independent implementations and the
conformance suite that certifies them, rather than first from intent. Several
of its requirements exist because a second implementation could not satisfy the
first draft of them.

### **N.1 Representation: canonical JSON**

Every payload is JSON derived mechanically from the IDL. The mapping is a pure
function of the type and MUST be implemented as such; a hand-written JSON shape
for any type in this specification is non-conformant.

| IDL | JSON |
|---|---|
| `boolean` | boolean |
| `int8`…`int32`, `uint8`…`uint32` | number, width-bounded |
| `int64`, `uint64` | **string**, decimal, unconditional |
| `float`, `double` | number; finite only, NaN and infinities rejected per §2.3 |
| `string`, `wstring` | string |
| `enum` | string, the **enumerator name** |
| `struct` | object, members under their **verbatim IDL names** |
| `union` | tagged object, `{"type": "<ENUMERATOR>", "<member>": value}` |
| `sequence<T,N>`, `T[N]` | array |
| `sequence<octet>`, `octet[N]` | **base64 string** |

Four of these are easy to get wrong and are therefore stated as requirements.

**Sixty-four-bit integers MUST be decimal strings, always**, not only when the
value exceeds the safe range. The binding's first-class consumer is a
JavaScript engine, where `JSON.parse` coerces every JSON number to a double
before application code runs. A value-dependent rule would make a field's
*type* depend on its *value*, forcing `oneOf: [integer, string]` on every
64-bit field and denying consumers a stable schema. One type per field is the
honest choice; this is the binding's one deliberate divergence from DDS-JSON
1.0.

**Members MUST appear under their verbatim IDL names.** A code generator that
renames a member to satisfy its target language — `global` and `from` are
reserved words in several — MUST reverse the rename before publishing. This is
stated because it was violated: eleven generated schemas in this
specification's own tooling published a generator's identifiers for a time, and
`additionalProperties: true` made the mismatch silent in both directions.

**A `has_*` guard is translated literally.** The guard appears as the boolean
it is, and the member it qualifies is **always present**, because that is what
the wire carries: CDR serializes a guarded member regardless of its guard. A
reader MUST consult the guard before relying on the member. Presence-mapping is
non-conformant: it would emulate an optionality DDS does not provide.

**An empty union branch is the discriminator alone.** `{"type": "COV_NONE"}`
and no member, even where the IDL declares a placeholder member for that case
and the wire carries a byte for it. This does not contradict the literal `has_*`
rule above: a guarded member is a declared member carrying a typed value, which
a reader may need once it has consulted the guard, whereas a union placeholder
is an encoding artifact with no semantic content — consumed when reading the
wire, and represented nowhere. A generator MUST record which branches are empty
in its published tables, because the distinction is not recoverable from the
IDL.

#### **N.1.1 Canonical form, for digests**

Wire JSON need not be canonical. Where a digest is taken — an `ETag`, a content
pin — the input MUST be the canonical form: object keys sorted lexicographically,
strings minimally escaped, no insignificant whitespace, and numbers rendered by
the **ECMA-262 `Number::toString` rule** (`0.1` → `0.1`, `0.1+0.2` →
`0.30000000000000004`, `1e21` → `1e+21`, `1.0` → `1`, `-0.0` → `0`).

"Shortest round-trip" names a property, not a unique string. The ECMA-262 rule
*is* the pin, so that a producer and a browser agree byte for byte and an ETag
computed on one side matches the other.

#### **N.1.2 Generated artifacts**

An implementation MUST derive its JSON from the published JSON Schemas and
serializer tables for the version it implements, or from the IDL directly.
A serializer table MUST distinguish a fixed array from a bounded sequence —
`length` against `bound` — because a sequence is length-prefixed on the wire
and a fixed array is not, and a table that erases the distinction cannot serve
as a decoder's type model. The same applies to an octet payload, where base64
hides the difference entirely.

### **N.2 Well-known paths**

All under the single `/.well-known/spatialdds` namespace registered per RFC 8615.

| Path | Method | Returns |
|---|---|---|
| `/.well-known/spatialdds/search` | `GET`, `POST` | service manifests (§3.3.0) |
| `/.well-known/spatialdds/schemas` | `GET` | the schema index |
| `/.well-known/spatialdds/schemas/{type}` | `GET` | one JSON Schema |
| `/.well-known/spatialdds/bootstrap` | `GET` | bootstrap manifest, where offered |
| `/.well-known/spatialdds/resolver` | `GET` | resolver metadata, where offered |

**`bootstrap` and `resolver` are REQUIRED only of an endpoint that offers DDS
access.** Both exist to hand a client the parameters for joining a domain. A
web-native endpoint has no domain, no peers and no partitions, and MUST return
`404` rather than fabricate them; a `404` from these two paths is conformant and
a conformance suite MUST accept it. A fabricated `domain_id` is worse than an
absence, because a client acts on it.

The schema index is a JSON array, one entry per published type:

```json
[{"type": "spatial.core.GeoAnchor",
  "url": "https://host/.well-known/spatialdds/schemas/spatial_core_GeoAnchor",
  "digest": "sha256:3af2…"}]
```

`{type}` is the schema's file basename: the dotted FQN with `.` replaced by `_`.
Each schema response MUST carry an `ETag` that is the digest of its canonical
form, and that digest MUST equal the `digest` the index advertises. An endpoint
MUST publish a schema for every type it serves, so that a consumer can decode
everything it receives from the published contract alone.

### **N.3 Latched state is a GET resource**

A `TRANSIENT_LOCAL` instance is a cacheable representation. Its path mirrors the
§3.3.1 topic name one-to-one, with the `spatialdds/` prefix supplied by the base
URL:

```
spatialdds/<domain>/<stream>/<type>/<version>   on the bus
     {base}/<domain>/<stream>/<type>/<version>  the collection
     {base}/<domain>/<stream>/<type>/<version>/<key>  one instance
```

`<key>` is the value of the member the IDL marks `@key`. The collection returns
a JSON array of instances; the instance path returns one object, or `404`.

Every such response MUST carry an `ETag` whose value is the digest of the
canonical form of the body's content, and a `Cache-Control` consistent with the
resource's access class (N.4). An endpoint MUST honour `If-None-Match` with
`304 Not Modified` and an empty body on a match. An `ETag` MUST be a function of
content alone: two endpoints serving the same state MUST produce the same
`ETag`, and restarting an endpoint MUST NOT change it.

*Plain statement:* a validator that changes while the content does not is worse
than no validator, because a cache will serve a stale body under a fresh one.

### **N.4 Access classes**

Every resource an endpoint serves MUST declare exactly one access class, in the
`access` field of its manifest topic entry (N.7):

- **`public-cacheable`** — served without authentication, with a positive
  `max-age`. Shared caches and CDNs MAY store it.
- **`operator-scoped`** — served only against a valid bearer credential, and
  `Cache-Control: no-store`. A `401` MUST carry `WWW-Authenticate: Bearer`.

**Auth and cacheability MUST NOT contradict.** An operator-scoped resource MUST
NOT be served with any cache lifetime, in either direction, authenticated or
not. A bearer-gated body carrying `max-age` sits in a shared cache where the
next unauthenticated request can be served it, which defeats the gate entirely.

A credential MUST NOT be accepted in a URL query parameter. Credentials belong
in the `Authorization` header, for both `GET` and the WebSocket handshake; a
query parameter writes the credential into proxy logs and `Referer` headers.

An endpoint SHOULD classify by what a resource describes rather than by who
asks: configured geometry — zones, crossing lines, frames, georeferences — is
ordinarily public, and observations of people ordinarily are not.

### **N.5 Streams are a WebSocket**

A subscription is a WebSocket opened to a collection URL. Every message is a
JSON object with an `event` member drawn from a fixed set:

```jsonc
{"event":"sample",        "topic":"<topic>", "key":"<key>", "data":{ … }}
{"event":"end_of_replay", "topic":"<topic>", "replayed":<N>, "as_of":{ … }}
{"event":"dispose",       "topic":"<topic>", "key":"<key>", "reason":"<text>"}
{"event":"liveliness",    "topic":"<topic>", "key":"<key>", "alive":true|false}
{"event":"closing",       "topic":"<topic>", "reason":"<text>", "code":"<token>"}
```

A client MUST ignore an `event` it does not recognise, which is the APPENDABLE
evolution rule applied to the envelope.

#### **N.5.1 Ordering**

On subscribe an endpoint MUST send zero or more `sample` events — the latched
set, current value per key — then **exactly one** `end_of_replay`, then live
events. `replayed` MUST equal the number of `sample` events that preceded it.

This marker is the single thing the binding adds that the bus does not have. On
a DDS domain "you now hold the whole latched set" is implicit in the QoS and a
late joiner simply receives it. Over a WebSocket a client that has received two
zones cannot distinguish three zones with one in flight from two zones and a
quiet topic. The binding makes the boundary a message and the count checkable.

A second `end_of_replay` is non-conformant, not merely redundant: it would
restart a client's notion of being caught up.

`as_of` is OPTIONAL and, when present, is a `builtin.Time` stating the instant
the replayed set describes. An endpoint serving recorded content SHOULD include
it, because for such an endpoint "now" is not self-evident.

#### **N.5.2 Removal**

A deliberate removal MUST be a `sample` carrying the instance's terminal state,
**immediately followed** by a `dispose` for the same key with a human-readable
reason. Not a `dispose` alone, which tells a client the instance is gone without
saying what it last was; and not a `dispose` separated from its sample by other
events, after which a client cannot tell which sample was terminal. This is
§2.14 over the web.

#### **N.5.3 Liveliness**

Liveliness MUST be an explicit event. A client MUST NOT infer liveliness, or
removal, or being caught up, from the WebSocket closing.

Granularity is declared, not assumed. A topic entry MAY carry
`liveliness: "per-key" | "per-writer" | "none"`. An endpoint whose upstream has
no writer-liveliness concept — a translation from a transport that does not
carry one — MUST declare `"none"` or `"per-writer"` rather than synthesise
per-instance liveliness it cannot observe. Loss of liveliness is **not** removal
and MUST NOT be sent as `dispose`.

#### **N.5.4 Ending a subscription**

An endpoint that stops a subscription MUST send `closing`, with a reason, before
closing the socket, whenever it is able to. The contract forbids a client from
reading meaning into the close, so the close cannot carry the meaning: without
this event an expired credential, a withdrawn topic and a restarting server all
arrive as the same silence. `code` is a short machine-readable token;
`reason` is for a human reading a log.

### **N.6 Commands are a POST**

Where an endpoint exposes a command surface, a command is a `POST` to the
resource it acts on, and the response carries the outcome, including an explicit
decline, per the keyed-command conventions of Appendix M.1.

An endpoint with no command lane — a northbound translation, a recording — has
nothing to accept a verb for. It MUST refuse cleanly, with `405` or `404`, and
MUST NOT accept a command it cannot act on. A conformance suite MUST NOT require
a command surface to exist.

### **N.7 Service manifests**

Discovery returns §8.2.3 service manifests. For the web binding, each entry of
`service.topics` MUST carry:

| Field | Required | Meaning |
|---|---|---|
| `name` | REQUIRED | the §3.3.1 topic name |
| `type` | REQUIRED | the registry type segment |
| `version` | REQUIRED | the version segment |
| `durability` | REQUIRED | `"VOLATILE"` or `"TRANSIENT_LOCAL"`, the DDS durability kinds verbatim |
| `qos_profile` | OPTIONAL | the deployment's QoS profile name, as §3.3.2 already uses it (`VIDEO_LIVE`, `POSE_RT`) |
| `url` | REQUIRED | the absolute URL of that topic's collection resource |
| `access` | REQUIRED | the access class of N.4 |
| `liveliness` | OPTIONAL | the granularity of N.5.3 |

`durability` is a separate member and not a `qos_profile` value. `qos_profile`
names a deployment's profile — §3.3.2 uses `VIDEO_LIVE`, `POSE_RT`, `VPS_REQ` —
and is free-form by design, so durability carried there would collide with an
established use and could not be read reliably. The two DDS kinds are used
verbatim, so a reader resolves them from DDS vocabulary and this binding coins
nothing.

`url` is what makes discovery **hypermedia** rather than a path-construction
exercise. Without it a client holding a manifest must know the N.3 path mapping
and rebuild each URL by string surgery on a topic name; with it, the client
follows a link. That is the difference between a ten-line client and one that
re-implements the specification.

`service.connection` remains OPTIONAL per §8.2.3. An endpoint that offers no DDS
access MUST omit it, and a client MUST treat its absence as conformant. §3.3.0's
requirement that a client be able to extract `service.connection` and join a
domain applies only to results that carry the block.

A manifest is JSON produced by this binding and follows N.1, including `stamp`,
whose `sec` is a decimal string.

### **N.8 Errors**

An error response SHOULD use `application/problem+json` per RFC 7807: `type`,
`title`, `status`, `detail`, `instance`. The binding defines no error body of
its own. Aligning with an existing standard is preferred to inventing a shape,
and this specification's earlier habit of an ad-hoc `{"error": …}` object is
deprecated for new implementations.

Status codes carry the contract: `304` for a validated cache entry, `401` with
`WWW-Authenticate` for an operator-scoped resource, `404` for a well-known path
an authority does not support, `400` for a malformed query.

### **N.9 The QoS subset**

**Carried, and observable:** reliability as a per-topic property; durability,
declared in a topic entry's `durability` member (N.7) and observable as latched
replay terminated by the `end_of_replay` marker; `KEEP_LAST(1)` per key, as the
collection returning one instance per key; keyed identity, as the instance path;
removal, as terminal sample plus `dispose`; liveliness, as an event.

**Not carried, and not emulated:** deadline, ownership and ownership strength,
time-based filter, partitions, transport priority, history depth beyond one.
An endpoint MUST NOT advertise these in a manifest or approximate them in the
envelope. A client needing them belongs on the bus.

### **N.10 Conformance**

An endpoint is conformant when it satisfies this appendix and the suite in
`web-binding/conformance/` passes against it. The suite takes a base URL and an
optional bearer token and nothing else: no flag selects a deployment shape, and
any check that would need to know which shape it is talking to is a defect in
the check.

Certification requires the same suite, unchanged, passing against **both** a
bridged and a web-native endpoint. Either alone demonstrates that one
implementation works; both together demonstrate that the binding is one binding.

### Why this belongs in the standard (Informative)

A bus that only bus participants can read is a smaller commons than it looks.
Most of the clients that would consume a spatial commons cannot join a DDS
domain, and the usual answer — a bespoke REST façade per deployment — gives
every deployment its own dialect, so a client written for one works nowhere
else. That is the failure this appendix exists to prevent: not an absence of
HTTP access, but an abundance of incompatible HTTP access.

Making the binding normative also forces the honesty the bus gets for free. A
DDS reader knows from the QoS when it holds a complete latched set; a web client
only knows if someone decided to tell it. Writing that down as `end_of_replay`,
with a count, is the kind of requirement that only becomes visible when a second
implementation tries to use the first one's output and finds it cannot tell a
slow replay from a quiet topic.
