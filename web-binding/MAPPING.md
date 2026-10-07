# Canonical JSON Mapping — generator implementation contract

The ratified §5 decisions (web-binding brief v1.1, step 3), stated as the rules
`gen.py` implements. This is the generator's contract, not spec text (the
binding spec, brief step 7, is written last from what the generator and gates
prove). Every rule below is mechanical and testable; the `golden/` vectors pin
the non-obvious ones.

## Primitives

| IDL | JSON value | JSON Schema | Notes |
|---|---|---|---|
| `boolean` | boolean | `{"type":"boolean"}` | |
| `octet` | number | `{"type":"integer","minimum":0,"maximum":255}` | but an `octet` **sequence/array** is base64 — see Bytes |
| `int8`/`int16`/`int32` | number | `{"type":"integer"}` width-bounded | fits ≤2³¹, safe as JSON number |
| `uint8`/`uint16`/`uint32` | number | `{"type":"integer","minimum":0}` width-bounded | |
| `int64` | **string** (decimal) | `{"type":"string","pattern":"^-?\\d+$"}` | **unconditional** — see Integers |
| `uint64` | **string** (decimal) | `{"type":"string","pattern":"^\\d+$"}` | **unconditional** |
| `float` (32) / `double` (64) | number | `{"type":"number"}` | finite only; NaN/Inf rejected per §2.3; digest form per Doubles |
| `char` / `wchar` | string (length 1) | `{"type":"string","minLength":1,"maxLength":1}` | |
| `string`/`wstring` | string | `{"type":"string"}`, `maxLength` from any IDL bound | |

### Integers (the one divergence from DDS-JSON)

`int64`/`uint64` serialize as decimal strings **always**, not value-dependent.
DDS-JSON 1.0 uses the RFC 7493 safe-range rule (number within ±(2⁵³−1), string
outside); we hold the unconditional string because our first-class consumer is a
JavaScript engine — `JSON.parse` coerces any JSON number to a double before
application code runs, and a value-dependent rule would force `oneOf:[integer,
string]` on every 64-bit field and make a field's *type* depend on its *value*.
One stable schema type per field is the honest-subset choice for the web.
(Smaller ints stay JSON numbers; they fit the 2⁵³ safe range by construction.)

### Doubles (digest canonicalization)

Wire JSON for a `float`/`double` is an ordinary JSON number and is unconstrained
beyond the schema. For **digest purposes only**, the canonical form of a number
is **the number-to-string conversion of ECMA-262** (equivalently, Ryū shortest
round-trip): `0.1 → "0.1"`, `0.1+0.2 → "0.30000000000000004"`, `1e21 → "1e+21"`,
`1.0 → "1"`, `-0.0 → "0"`. "Shortest round-trip" names a property, not a unique
string; the ECMA-262 rule *is* the pin, so a Python producer and a browser
consumer agree byte-for-byte. The round-trip gate covers this cross-language with
`golden/pose_adversarial_double.json`.

## Enums

Serialize as the JSON **string of the enumerator name** (never the ordinal):
`{"type":"string","enum":["NAME_A","NAME_B",…]}`. Names are stable and
interoperable; non-consecutive `@value` ordinals (which several profiles use) are
irrelevant to the JSON because the name carries the identity.

## Constructed types

- **struct** → JSON object. Properties are the members under their **verbatim IDL
  names**. `additionalProperties` is **true** (never `false`): unknown fields are
  ignored by readers — the APPENDABLE evolution rule restated for the web, the
  same sentence as on-bus evolution. `@key` has no JSON effect (keying is a
  bus-side concern). `required` lists exactly the members that are neither
  guarded (see Optionality) nor absent.
- **union** → **tagged object**: `{"type": "<DISCRIMINATOR_ENUMERATOR_NAME>",
  "<selected_member_name>": <value>}`. The discriminator key is the literal
  `"type"`, aligning with the spec's existing covariance JSON (Appendix D,
  `{"type":"COV_POS3","pos":[…]}`) — align-before-invent (principle 4). An empty
  branch is `{"type":"COV_NONE"}` with no member. **Generator MUST error** if any
  union member's name equals the discriminator key `"type"` (none do today); this
  guards the one collision the aligned choice could create. Schema: `oneOf` over
  branches, each `{"required":["type"],"properties":{"type":{"const":"<ENUM>"},
  "<member>":<schema>}}`.
- **sequence\<T,N\>** → JSON array → `{"type":"array","items":<T>,"maxItems":N}`.
- **T[N]** (fixed array) → JSON array → `{"type":"array","items":<T>,
  "minItems":N,"maxItems":N}`.

  The two produce the same JSON shape, and the schema separates them by
  `minItems`. The **serializer tables must separate them too**: a fixed array
  carries `"length": N`, a bounded sequence carries `"bound": N`. The
  distinction is not cosmetic for anything that reads the wire, where a
  sequence is length-prefixed and a fixed array is not, and a table that
  erased it could not be used as a decoder's type model. Same for an octet
  payload, where base64 hides the difference entirely: `{"t":"base64",
  "length":N}` against `{"t":"base64","bound":N}`.
- **typedef/alias** → resolves to the aliased type's mapping. So `Vec3`
  (`double[3]`) → 3-number array; `Aabb3D` (`double[6]`) → 6-number flat array
  (the §2.10 flat form); `Mat3x3` (`double[9]`) → 9-number array.

## Bytes

An `octet` **sequence** (`sequence<octet>` / `sequence<octet,N>`) or **`octet[N]`
array** → a **base64 string** → `{"type":"string","contentEncoding":"base64"}`
(add `maxLength` reflecting the byte bound where present). This overrides the
per-`octet` number rule above: byte payloads are base64, not arrays of integers.

## Optionality — the `has_*` guard idiom → **literal translation**

**The rule is: no rule.** A `has_*` guard is translated like any other field — the
guard boolean appears in JSON as the boolean it is, and the guarded member is
**always present**, exactly as the wire carries it. CDR serializes a guarded
member regardless of its guard; the guard is a *semantic* flag ("is this value
meaningful"), not wire optionality. A reader consults the guard before trusting
the member — the same contract every binding has. (Brief v1.2; a formal step-3
reopening of this one §5 rule, decided on the census below. This reverses the
earlier presence-mapping decision.)

Mechanically: every declared member is present and `required`; `has_*` booleans
are ordinary `{"type":"boolean"}` fields; nothing is dropped, nothing is made
conditional. The binding text carries one informative sentence telling readers to
consult a `has_*` guard before relying on the member it qualifies, citing the
spec's existing guard semantics. The generator therefore has **no** pairing
logic, no inference, and no ambiguous-pairing case — the hardest code path is
simply absent.

**Why literal, not presence-mapping (the census conclusion, not a concession).**
Presence-mapping was never the honest JSON form of the wire: the wire always
carries the guarded member, so presence-mapping emulates an optionality DDS is
not actually providing. The census (`guard-census.txt`, all 178 guards from
idlc's AST) proved that emulation needs knowledge the IDL does not encode —
`has_*` is overloaded three ways and no structural rule recovers the pairings:

- **Over-capture:** a guard that is last in its struct would swallow mandatory
  trailing fields — `Detection3D.has_tile → [tile_key, class_id, score, center,
  size, q]` captures the mandatory `class_id/score/center/size/q`.
- **Capability flags, not guards:** `RadioSensorMeta.has_rssi/has_rtt/has_aoa/
  has_csi` (and `LidarFrame.has_per_point_timestamps`) govern no member — they are
  data. Under the literal rule this overload simply does not matter, which is
  itself confirmation the literal rule is right.
- **Swept plain booleans:** `global` (idlc: `_global`) is an always-present flag
  no guard owns.

A 178-guard annotation pass (the alternative) would have been a standing
editorial liability maintained forever for prettier JSON that *diverges from the
wire*. Rejected. The overload of `has_*` is now a documented spec-side fact (see
the alignment findings note); making it machine-readable is a possible future
editorial item, and the binding waits on none of it.

## Canonical serialization (digest only)

For content-digest pinning (brief §5, §6): object keys sorted lexicographically;
numbers by the ECMA-262 rule above; strings minimally escaped per JSON; no
insignificant whitespace. Wire JSON is **not** required to be canonical — only
the digest input is. Schemas are published beside the IDL, content-digest pinned,
and served at a well-known path so an endpoint is self-describing.
