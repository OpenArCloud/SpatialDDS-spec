// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.8 (© Open AR Cloud Initiative)

## **2. Conventions (Normative)**

This section centralizes the rules that apply across every SpatialDDS profile. Individual sections reference these shared requirements instead of repeating them. See Appendix A (core), Appendix B (discovery), Appendix C (anchors), and Appendix D (extensions) for the canonical IDL definitions that implement these conventions.

### **2.1 Orientation & Frame References**

- All quaternion fields, manifests, and IDLs SHALL use the `(x, y, z, w)` order that aligns with OGC GeoPose.
- Frames are represented exclusively with `FrameRef { uuid, fqn, coord_convention? }`. The UUID is authoritative; the fully qualified name is a human-readable alias; the optional `coord_convention` selects the axis convention for poses in this frame (see §2.12). Appendix G defines the authoritative frame model.
- Example JSON shape:
  ```json
  "frame_ref": { "uuid": "00000000-0000-4000-8000-000000000000", "fqn": "earth-fixed/map/device" }
  ```

**Quaternion Convention Reference (Informative)**

SpatialDDS uses `(x, y, z, w)` component order for all quaternion fields, aligning with OGC GeoPose. Adjacent ecosystems use different conventions; implementers ingesting external data MUST reorder components before publishing to the bus.

| Source | Order | Conversion to SpatialDDS |
|---|---|---|
| OGC GeoPose | (x, y, z, w) | None |
| ROS 2 (`geometry_msgs/Quaternion`) | (x, y, z, w) | None |
| nuScenes / pyquaternion | (w, x, y, z) | `(q[1], q[2], q[3], q[0])` |
| Eigen (default) | (w, x, y, z) | `(q.x(), q.y(), q.z(), q.w())` |
| Unity | (x, y, z, w) | None (left-handed) |
| Unreal Engine | (x, y, z, w) | None (left-handed) |
| OpenXR | (x, y, z, w) | None |
| glTF | (x, y, z, w) | None |

**Handedness note (Informative):** SpatialDDS does not prescribe a single global handedness. Frame semantics are defined by `FrameRef` and transform chains, not by a global axis convention. Producers from left-handed engines (Unity, Unreal) must ensure the transform chain is consistent, not merely that the quaternion component order matches. Use `FrameRef.coord_convention` (§2.12) to make the per-frame axis convention explicit so that consumers can detect and resolve mismatches automatically.

### **2.2 Optional Fields & Discriminated Unions**

- Optional scalars, structs, and arrays MUST be guarded by an explicit `has_*` boolean immediately preceding the field. String fields are exempt: an empty string denotes absence for optional strings (e.g., `auth_hint`, `next_page_token`) unless a profile states otherwise.
- Mutually exclusive payloads SHALL be modeled as discriminated unions; do not overload presence flags to signal exclusivity.
- Schema evolution leverages `@extensibility(APPENDABLE)`; omit fields only when the IDL version removes them, never as an on-wire sentinel.
- See `CovMatrix` in Appendix A for the reference discriminated union pattern used for covariance.
- See `FramedPose` in Appendix A for the reference bundled-pose pattern. Prefer `FramedPose` over scattering `PoseSE3` + `FrameRef` + `CovMatrix` + `Time` as sibling fields on a struct.

### **2.3 Numeric Validity & NaN Deprecation**

- `NaN`, `Inf`, or other sentinels SHALL NOT signal absence or "unbounded" values; explicit presence flags govern validity.
- Fields guarded by `has_*` flags are meaningful only when the flag is `true`. When the flag is `false`, consumers MUST ignore the payload regardless of its contents.
- When a `has_*` flag is `true`, non-finite numbers MUST be rejected wherever geographic coordinates, quaternions, coverage bounds, or similar numeric payloads appear.
- Producers SHOULD avoid emitting non-finite numbers; consumers MAY treat such samples as malformed and drop them.

### **2.4 Conventions Quick Table (Informative)**

| Pattern | Rule |
|--------|------|
| Optional fields | All optional values use a `has_*` flag. |
| NaN/Inf | Never valid; treated as malformed input. |
| Quaternion order | Always `(x, y, z, w)` GeoPose order. |
| Frames | `FrameRef.uuid` is authoritative. |
| Ordering | `(source_id, seq)` is canonical. |

### **2.5 Canonical Ordering & Identity**

These rules apply to any message that carries the trio `{ stamp, source_id, seq }`.

**Field semantics**

- `stamp` — Event time chosen by the producer.
- `source_id` — Stable writer identity within a deployment.
- `seq` — Per-`source_id` strictly monotonic unsigned 64-bit counter.

**Identity & idempotency**

- The canonical identity of a sample is the tuple (`source_id`, `seq`).
- Consumers MUST treat duplicate tuples as the same logical sample.
- If `seq` wraps or resets, the producer MUST change `source_id` (or use a profile with an explicit writer epoch).

**Ordering rules**

1. **Intra-source** — Order solely by `seq`. Missing values under RELIABLE QoS indicate loss.
2. **Inter-source merge** — Order by (`stamp`, `source_id`, `seq`) within a bounded window selected by the consumer.

**Synthesizing (`source_id`, `seq`) from External Data (Informative)**  
Datasets and replay tools that lack native per-writer sequence counters SHOULD synthesize them as follows:
1. Set `source_id` to a stable identifier for the data source (e.g., dataset name + sensor channel).
2. Assign `seq` by sorting samples by timestamp within each `source_id` and numbering from 0.
3. If the dataset contains gaps or non-monotonic timestamps, sort by the dataset's native ordering key and number from 0.

This produces a valid (`source_id`, `seq`) tuple without requiring the original system to have had one.

### **2.6 DDS / IDL Structure**

- All SpatialDDS modules conform to OMG IDL 4.2 and DDS-XTypes 1.3.
- Extensibility SHALL be declared via `@extensibility(APPENDABLE)`.
- Consumers MUST ignore unknown appended fields in APPENDABLE types.
- Compound identity SHALL be declared with multiple `@key` annotations.
- Field initialization remains a runtime concern and SHALL NOT be encoded in IDL.
- Abridged snippets within the main body are informative; the appendices contain the authoritative IDLs listed above.

### **2.7 Security Model (Normative)**

#### **2.7.1 Threat model (informative background)**
SpatialDDS deployments may involve untrusted or partially trusted networks and intermediaries. Threats include:
- **Spoofing:** malicious participants advertising fake services or content.
- **Tampering:** modification of messages, manifests, or blob payloads in transit.
- **Replay:** re-sending previously valid messages (e.g., ANNOUNCE, responses) outside their intended validity window.
- **Unauthorized access:** clients subscribing to sensitive streams or publishing unauthorized updates.
- **Privacy leakage:** exposure of user location, sensor frames, or inferred trajectories.

#### **2.7.2 Trust boundaries**
SpatialDDS distinguishes among:
- **Local transport fabric** (e.g., DDS domain): participants may be on a shared L2/L3 network, but not necessarily trusted.
- **Resolution channels** (e.g., HTTPS retrieval or local cache): used to fetch manifests and referenced resources.
- **Device/app policy:** the client’s local trust store and decision logic.

#### **2.7.3 Normative requirements**
1. **Service authenticity.** A client **MUST** authenticate the authority of a `spatialdds://` URI (or the service/entity that advertises it) before trusting any security-sensitive content derived from it (e.g., localization results, transforms, anchors, content attachments).
2. **Integrity.** When security is enabled by deployment policy or indicated via `auth_hint`, clients **MUST** reject data that fails integrity verification.
3. **Authorization.** When security is enabled, services **MUST** enforce authorization for publish/subscribe operations that expose or modify sensitive spatial state (e.g., anchors, transforms, localization results, raw sensor frames).
4. **Confidentiality.** Services **SHOULD** protect confidentiality for user-associated location/sensor payloads when transmitted beyond a physically trusted local network.
5. **Discovery trust.** Clients **MUST NOT** treat Discovery/ANNOUNCE messages as sufficient proof of service authenticity on their own. ANNOUNCE may be used for bootstrapping **only** when accompanied by one of: (a) transport-level security that authenticates the publisher (e.g., DDS Security), or (b) authenticated retrieval and verification of an authority-controlled artifact (e.g., a manifest fetched over HTTPS/TLS, or a signed manifest) that binds the service identity to the advertised topics/URIs.

#### **2.7.4 Validity and replay considerations**
Implementations **SHOULD** enforce TTL and timestamps to mitigate replay. Where TTL exists (e.g., in Discovery messages), recipients **SHOULD** discard messages outside the declared validity interval.

#### **2.7.5 DDS Security Binding (Normative)**
SpatialDDS deployments that require authentication, authorization, integrity, or confidentiality over DDS **MUST** use **OMG DDS Security** as the minimum on-bus security contract. This includes:

- **Authentication:** PKI-based authentication as defined by DDS Security.
- **Access control:** governance and permissions documents configured per DDS Security.
- **Cryptographic protection:** when confidentiality or integrity is required by policy, endpoints **MUST** enable DDS Security cryptographic plugins.

Cloud and enterprise authorization mechanisms (OAuth 2.0/OIDC, SPIFFE/SPIRE, mutual TLS) MAY be layered via the `auth_hint` field. `auth_hint` extends the authorization model to HTTP-resolved resources (manifests, blob stores, service APIs) without replacing the on-bus DDS Security contract.

**Operational mapping (non-exhaustive):**
- Participants join a DDS **Domain**; security configuration applies to DomainParticipants and topics as governed by DDS Security governance rules.
- Discovery/ANNOUNCE messages that convey service identifiers, manifest URIs, or access hints **SHOULD** be protected when operating on untrusted networks.

**Interoperability note (informative):**
This specification does not redefine DDS Security. Implementations should use vendor-compatible DDS Security configuration mechanisms.

#### **2.7.6 Spatial Privacy (Normative Guidance)**

SpatialDDS streams carrying `GeoPose`, `FramedPose`, or ego-pose trajectories constitute personal location data when they describe individual users or devices. Deployments operating under privacy regulations (GDPR, CCPA, or equivalent) SHOULD apply the following mitigations:

- **Pose quantization.** Reduce pose precision to the minimum required by the application (e.g., 1 m position, 5° orientation for building-level occupancy; full precision for SLAM).
- **Trajectory truncation.** Limit the temporal extent of published pose histories. Fixed-lag smoothing windows (sensing profiles) naturally bound trajectory length; persistent storage of full trajectories requires explicit consent.
- **Pseudonymization.** Use rotating `source_id` values that cannot be linked across sessions without a key held by the data controller.
- **Consent and purpose limitation.** Operators publishing ego-pose streams to shared SpatialDDS domains MUST ensure that participants have consented to the spatial data sharing arrangement and that the data is used only for the stated purpose (e.g., collaborative SLAM, fleet coordination).

These mitigations are normative guidance (SHOULD), not normative requirements (MUST), because privacy requirements vary by jurisdiction, deployment context, and application domain. Implementers are responsible for compliance with applicable privacy regulations.

### **2.8 Enum Serialization (Normative)**

When SpatialDDS types are serialized to JSON (manifests, HTTP payloads, diagnostic logs), enum values MUST be emitted as their IDL identifier string (e.g., `"GAUSSIAN_SPLAT"`, not `1`). Decoders MUST accept both the string identifier and the integer `@value` form. Unknown string identifiers MUST be rejected; unknown integer values MUST be treated as the enum's highest-numbered fallback value (e.g., `OTHER_RADIO`, `CUSTOM`) if one exists, or rejected otherwise.

On the DDS wire (CDR encoding), enum values use their integer `@value(N)` per OMG IDL specification. This rule applies only to JSON serialization contexts.

### **2.9 Time Semantics (Normative)**

All `Time` values in SpatialDDS MUST represent UTC seconds since the Unix epoch (1970-01-01T00:00:00Z), excluding leap seconds (i.e., POSIX time / `clock_gettime(CLOCK_REALTIME)`). `nanosec` MUST be in the range `[0, 999999999]`.

Producers operating in environments with hardware time synchronization SHOULD document their clock source via a `MetaKV` entry on the associated meta type with `namespace = "time"` and the following keys:

| Key | Values | Example |
|-----|--------|---------|
| `clock_source` | `ptp`, `pps`, `gnss`, `ntp`, `system` | `"ptp"` |
| `clock_accuracy_ns` | estimated accuracy in nanoseconds | `"1000"` |
| `leap_second_mode` | `posix` (default), `tai`, `utc_with_leap` | `"posix"` |

Consumers performing cross-device temporal association (e.g., multi-robot loop closure, multi-operator fusion) SHOULD verify that all sources share a common clock domain before assuming sub-millisecond time alignment. When clock domains differ, consumers MUST estimate and compensate clock offsets before temporal association.

**Default assumption:** If no `time` metadata is present, consumers MUST assume `clock_source = "system"` with no accuracy guarantee.

### **2.10 Bounding Box Ordering (Normative)**

- **Geographic CRS (WGS84):** `bbox` arrays MUST use GeoJSON ordering: `[lon_min, lat_min, lon_max, lat_max]` (2D) or `[lon_min, lat_min, alt_min, lon_max, lat_max, alt_max]` (3D). The 6-element 3D form applies to JSON manifests and HTTP payloads only. On-bus `CoverageElement.bbox` is always the 4-element 2D form; volumetric coverage on the bus uses `aabb`.
- **Local / ENU CRS:** `Aabb3` uses `{min_xyz, max_xyz}` where each is a `Vec3` in the local coordinate frame.

JSON examples throughout this specification MUST follow these conventions. Where a `CoverageElement` uses `crs = "EPSG:4326"`, the `bbox` array uses GeoJSON ordering. Where `crs` is absent or local, the `aabb` field uses `Aabb3` semantics.

### **2.11 Schema Stability Signaling (Normative)**

The `schema_version` string present on all Meta and Frame types (e.g., `"spatial.sensing.vision/1.8"`) implicitly indicates stability: profiles listed in Appendices A–D are stable; profiles in Appendix E are provisional or informative.

For runtime discrimination, producers of provisional types SHOULD include a `MetaKV` entry with `namespace = "schema"` and key `stability` set to `"provisional"`. On a type whose metadata is carried as a plain `KV` sequence rather than `MetaKV` (for example `owm::Entity.properties`), the equivalent marking is a `KV` with key `schema.stability` and value `provisional`. Consumers in production deployments MAY use either form to filter or warn on provisional data.

Example:

```json
{
  "namespace": "schema",
  "json": "{\"stability\": \"provisional\"}"
}
```

Additionally, the `caps.features` field in `Announce` MAY carry feature flags prefixed with `provisional.` (e.g., `"provisional.rf_beam"`, `"provisional.radio"`). Consumers MAY filter `Announce` messages to exclude provisional features in production deployments.

`schema_version` appears on Meta, Frame, and latched/durable types (descriptors that outlive a session or are recorded standalone). High-rate graph and sample types (`Node`, `Edge`, chunks) omit it; their schema identity travels via the topic's `TopicMeta` and `MODULE_ID`. Types in a provisional 0.x module (for example `spatial.owm/0.1`) MAY omit `schema_version` entirely regardless of their latched/durable status: the module's version identity lives in its `MODULE_ID` and provenance note (Appendix E), and a 0.x module carries no per-sample schema-version guarantee to signal.

### **2.12 Coordinate Axis Convention (Normative)**

`FrameRef` carries an optional `coord_convention` field (added in 1.6) that specifies the axis convention for all poses expressed in this frame. The predefined conventions are:

| Convention | X | Y | Z | Handedness | Used By |
|---|---|---|---|---|---|
| `ENU` | East | North | Up | Right | ROS REP-103, GeoPose, SpatialDDS default |
| `CV` | Right | Down | Forward | Right | OpenCV, colmap, hloc, ORB-SLAM, DSO |
| `GRAPHICS` | Right | Up | Backward | Right | WebXR, OpenGL, three.js, Rerun |
| `UNITY_LH` | Right | Up | Forward | Left | Unity |
| `NED` | North | East | Down | Right | Aviation, PX4, ArduPilot, MAVLink |
| `OTHER` | — | — | — | — | Custom; producer MUST document axes in `MetaKV` |

**Default assumption.** When `has_coord_convention` is `false` (or the field is absent because the publisher predates 1.6), consumers MUST assume `ENU`. This matches the GeoPose protocol and ROS REP-103.

**Chaining rule.** Consumers MUST NOT chain poses (via `FrameTransform` or parent-child relationships) across `FrameRef` values with different `coord_convention` values without an intervening axis-swap transform. Libraries SHOULD provide automatic axis-swap utilities based on the enum:

- `CV` → `ENU`: rotate 90° around X, then 90° around Z.
- `GRAPHICS` → `ENU`: rotate 90° around X.
- `NED` → `ENU`: rotate 180° around Z, then 90° around X.
- `UNITY_LH` → `ENU`: negate Z, then rotate 90° around X.

(Indicative — implementations MUST derive the correct transform from the axis definitions in the table above. Quaternion order remains `(x, y, z, w)` per §2.1.)

**Producer guidance:**

- Producers bridging from computer-vision pipelines (OpenCV, colmap, hloc, ORB-SLAM, DSO) SHOULD set `coord_convention = CV`.
- Producers bridging from WebXR, OpenGL, or three.js SHOULD set `coord_convention = GRAPHICS`.
- Producers bridging from Unity SHOULD set `coord_convention = UNITY_LH`.
- Producers bridging from drone / aviation systems (PX4, ArduPilot, MAVLink) SHOULD set `coord_convention = NED`.
- Producers publishing SpatialDDS-native pipelines (GeoPose, ROS 2 bridge) SHOULD set `coord_convention = ENU` explicitly — even though it is the default — for clarity.
- When `coord_convention = OTHER`, producers MUST document the axis convention in a `MetaKV` entry with `namespace = "frame"` and keys `axis_x`, `axis_y`, `axis_z` (values from: `"east"`, `"north"`, `"up"`, `"right"`, `"down"`, `"forward"`, `"backward"`, `"left"`).

### **2.13 Frame Scale (Normative)**

`FrameRef` carries optional scale fields (added in 1.8): `has_scale`, `scale_status`, `meters_per_unit`, and `display_unit`. Scale is, like the axis convention of §2.12, an unstated frame property that silently corrupts every pose expressed in the frame: a monocular or image-only reconstruction has arbitrary units, and a scale error is proportional, invisible, and survives every existing validity check. The predefined scale states are:

| `scale_status` | Meaning |
|---|---|
| `SCALE_UNKNOWN` | Scale has not been established; `meters_per_unit` is not meaningful. |
| `SCALE_DECLARED` | The producer asserts `meters_per_unit` directly (metric SLAM/LiDAR/GNSS, surveyed frames). |
| `SCALE_DERIVED` | `meters_per_unit` was recovered rather than asserted (e.g. from a legacy similarity transform). |

**Default assumption.** When `has_scale` is `false` (or the field is absent because the publisher predates 1.8), consumers MUST assume the frame is **metric**: one frame unit equals one metre. Every pre-1.8 publisher therefore remains correct by construction. A producer publishing a frame whose metric scale it has **not** established MUST set `has_scale = true` with `scale_status = SCALE_UNKNOWN`. **Absence is not the unknown state** — silence means metric, not "I don't know."

**Conversion rule.** Consumers MUST NOT compose poses across `FrameRef` values of differing or unknown `meters_per_unit` without an explicit scale conversion, and MUST NOT treat poses in a `SCALE_UNKNOWN` frame as metric at all. Libraries SHOULD provide the conversion automatically from `meters_per_unit`, mirroring the axis-swap rule of §2.12.

**Covariance interpretation.** A `CovMatrix` position block expressed in a scaled frame is in **frame units squared**; multiply by `meters_per_unit²` to obtain metres squared. In a frame of unknown scale, the metric interpretation of a position covariance is undefined.

**Producer guidance:**

- `meters_per_unit` is the single source of truth. `display_unit` (e.g. `"m"`, `"mm"`, `"ft"`) is presentation only and MUST NOT be used for computation.
- Producers from metric pipelines (metric SLAM, LiDAR, GNSS-aligned, surveyed) SHOULD set `scale_status = SCALE_DECLARED` with `meters_per_unit = 1.0` (or the true factor if the native unit is not the metre).
- Producers from monocular or image-only SfM that have not resolved metric scale MUST set `scale_status = SCALE_UNKNOWN`.
- Producers that recover scale after the fact (for example from a legacy similarity transform) SHOULD set `scale_status = SCALE_DERIVED`.
- *Migration note (non-normative):* deriving `meters_per_unit` from an existing deployment's similarity-transform matrix is the documented path for populating scale on legacy frames. The frame-scale design was motivated and prototyped by G. Sörös's map-autoscaling work.

### **2.14 Keyed-Instance Removal (Normative)**

The specification defines creation and update for latched keyed types but has been silent on **removal**, so a late joiner could not distinguish an instance that was deliberately retired from one that merely vanished. This section closes that gap.

**Removal rule.** For a latched keyed instance (a RELIABLE + TRANSIENT_LOCAL keyed topic) that is being deliberately removed, the writer MUST first publish a final sample carrying the instance's terminal state and a human-readable reason, and MUST then dispose the instance. The final sample is what a late joiner reads to learn that, and why, the instance was retired.

**Liveliness is not removal.** Loss of liveliness, a lease expiry, or a writer simply disappearing is **not** removal. Consumers MUST NOT treat a liveliness change as a deliberate removal, and MUST NOT purge a durable keyed instance on liveliness loss alone.

This applies to all RELIABLE + TRANSIENT_LOCAL keyed types. `EntityBinding` is named explicitly: a binding being retired MUST follow this rule (its absence was the recorded gap).

*Non-normative note:* a removal is a claim and a silence is not — the standard can require honesty about the former but can never infer it from the latter, which is exactly why the final-sample-then-dispose sequence, not liveliness, is the removal signal.

### **2.15 Payload Scope (Normative)**

Two classes of payload that spatial deployments commonly publish are
deliberately **not** typed by these profiles. Each is stated here with the
adapter mapping that carries it, so an integrator meets a decision rather than
a silence. A refusal can be planned against; an omission has to be discovered.

**Scalar sensor readings.** SpatialDDS does not define a scalar or point sensor
reading type — a temperature, humidity, air-quality, occupancy-count, or
similar single-value measurement. Such a reading is telemetry *about* a place
rather than a description *of* one: it carries no geometry, no extent, and no
frame of its own, and the formats that serve device telemetry already do it
well.

*Adapter mapping.* An adapter SHOULD attach the reading to the typed thing it
describes rather than opening a parallel stream: as a namespaced attribute on
the zone, entity, or stream the sensor observes, following the typed-first
extension rule of Appendix A (scalar and string-valued extensions in
`MetaKV.entries`, keys namespaced `org.key`). The sensor's own identity belongs
in `source_id`, not in a new field. Where the reading's spatial meaning is the
*place* rather than the device, the zone or entity carrying the attribute is
what gives it location.

**Analytics aggregates.** SpatialDDS does not define an aggregate-analytics
type — a cluster, a heatmap bucket, a flow count, a dwell histogram. An
aggregate is a **derived claim about a region over a window**, not an
observation of a thing, and typing one would mean fixing a windowing and
binning vocabulary that every analytics producer defines differently.

*Adapter mapping.* Publish the aggregate as what it is: a derived zone
(`events::SpatialZone`, with the aggregate's footprint as its geometry) or a
derived entity, attributed to the producer that computed it via `source_id`,
with the aggregation window carried as a namespaced attribute. Where the model
in use records provenance of claims, the aggregate takes the derived basis
rather than the observed one — in `spatial.owm` that is `Basis.DERIVED`
(Appendix E). An aggregate MUST NOT be published as an `OBSERVED` claim: it is
not a measurement, and a consumer that cannot tell the difference will treat a
statistic as a sighting.

**Open metadata bags.** Where a producer carries detector-defined keys whose
vocabulary is not fixed — per-detection attributes such as re-identification
descriptors, demographic estimates, or vendor-specific scores — an adapter
carries the bag opaquely through the existing metadata mechanism
(`MetaKV.entries` for scalar and string values, `MetaKV.json` for genuinely
free-form payloads, per the typed-first extension rule in Appendix A), keys
namespaced to the originating producer.

The lossiness MUST be understood rather than hidden: a consumer receives **the
bag, not a contract**. It can round-trip the values and show them to a human;
it cannot rely on a key's presence, type, or meaning across producers. This is
an honest carry, not an interoperable one, and a type would not change that —
the obstacle is an unfixed key space, not a missing field. Agreeing a shared
registry for such keys is a conversation between producers; it is not a
specification obligation, and this document does not attempt one.

**Hardware sensor identity.** Sensor identities that arrive as hardware
identifiers — a MAC address, a serial number, a vendor device id — map to
`source_id` on the message that carries the observation. No new field is
needed, and none is added.

To keep such identifiers distinguishable from service ids, producers SHOULD
namespace them with a scheme prefix: `mac:00-1b-63-84-45-e6`,
`serial:<vendor>/<serial>`, or a URN the vendor already publishes. An
unprefixed bare identifier in `source_id` is indistinguishable from a service
id, which is the failure this convention exists to prevent. Where both a
service and a device are meaningful — a tracker publishing on behalf of a
camera — `source_id` names the publisher and the device identifier belongs in
the metadata bag above, or in an `EntityBinding` component reference.

*Non-normative note:* both refusals are the same judgement in two places. A
profile earns a type by carrying something whose **shape** is agreed across
producers; scalar telemetry and analytics windows are agreed in neither shape
nor vocabulary, so a type here would standardise one vendor's choices and call
it interoperability. The adapter mappings cost an integrator a namespaced key
and lose nothing a consumer could have relied on.

### **2.16 Crossing-Line Side Convention (Normative)**

`events::CrossingLine` (added 1.8) describes an open path that objects cross
rather than a region they occupy. A crossing is only meaningful if both ends
agree which side is which, so the sides are fixed here rather than left to the
producer.

This is the deliberate counterpart to a zone ring. A `SpatialZone` polygon is a
*closed* ring with a fixed winding (CCW), where the winding is what separates
inside from outside; a `CrossingLine` is an *open* path whose two sides are
separated instead by the path normal defined below. The asymmetry is
intentional — a region has an interior to enclose, a line has only two sides to
tell apart — and the two must not be conflated: a `CrossingLine` path is never
implicitly closed.

**Side rule.** Take the path in the order its vertices are published, from the
first toward the last, in the line's `frame_ref` XY plane. For a path direction
`d = (dx, dy)`, the **LEFT** side is the half-plane lying in the direction of
the normal `n = (-dy, dx)`; the **RIGHT** side is the opposite. Facing along
the path with the frame's Z axis up, LEFT is to the observer's left — which is
what the names are for, but the normal is the definition, because "left" is
only unambiguous once the frame's handedness is pinned. Frames follow the axis
convention of §2.12; in a frame whose Z is not up, the normal above still
defines the sides and the words LEFT and RIGHT are then labels rather than
descriptions.

**Direction reporting.** `SpatialEvent.crossing_direction` reports travel
relative to that convention: `LEFT_TO_RIGHT` or `RIGHT_TO_LEFT`. A producer
that detects a crossing but cannot resolve its direction MUST report
`CROSSING_UNKNOWN` rather than omitting `has_crossing` or guessing a direction.
Absence of the field means the producer said nothing about crossing at all;
`CROSSING_UNKNOWN` means it saw one and does not know which way.

**Vertex order is part of the definition.** Because the sides derive from
vertex order, reversing a published `CrossingLine`'s `path` swaps LEFT and
RIGHT and therefore inverts the meaning of every direction reported against it.
A producer republishing a line MUST NOT reverse its vertex order while keeping
the same `line_id`; a line whose sides need to change is a new line, or a
deliberate removal and replacement under the keyed-instance removal rule of
§2.14.

**Geometry constraints.** A `path` MUST carry at least 2 vertices and MUST NOT
be closed — the last vertex does not join the first, and consumers MUST NOT
infer closure. A path SHOULD NOT self-intersect: LEFT and RIGHT are not
globally well-defined for a self-crossing path, and a producer needing one
SHOULD publish separate lines. Where `has_bounds` is set, `bounds` MUST contain
the whole path; it exists for coarse spatial filtering and MUST NOT be used as
a crossing test.

*Non-normative note:* the reason a crossing line is not a zone with a very thin
polygon is that a zone answers "is this point inside?" and a line has no
inside. A sliver polygon makes every containment test answer a question the
geometry does not mean, and reintroduces precisely the over- and
under-claiming that polygon zones were added to remove. `EventType.LINE_CROSS`
has referred to "a defined trip line" since the enum was introduced; until 1.8
there was no such type for it to refer to.

### **2.17 Composed Scenes (Normative Guidance)**

Deployments routinely nest: a site made of buildings, a building of floors, a
floor of rooms, each with its own tracker and its own view of the objects in
it. The question this section answers is whether that needs new types. It does
not. A composed deployment is expressible end-to-end in types that already
exist, and this section walks one through so that independent implementations
converge on the same shapes rather than each inventing a hierarchy.

Nothing here adds IDL or changes a normative requirement elsewhere; it states
how existing requirements compose.

**1 — One frame per scene.** Each scene is a coordinate frame, named by a
`FrameRef` (§2.1, `fqn`). A scene is not a new kind of object; it is the frame
its contents are expressed in, plus the services that publish into it.

**2 — Coordinate nesting is a frame transform.** A child scene's placement
within its parent is a `core::FrameTransform` with `parent_ref` naming the
parent scene's frame, `child_ref` the child's, and `T_parent_child` the pose
between them. Transforms compose, so a position in a room resolves to the site
frame by walking the chain — and `cov` on each transform means the uncertainty
of that walk is expressible rather than assumed away.

**3 — Spatial containment is announced coverage.** A parent announces coverage
that encloses its children's, and names them in `coverage_source_ids`. This is
not a new convention: the derived-coverage rule (§3.3.0) already states that a
non-empty `coverage_source_ids` marks the declared coverage as an
approximation of the union of the sources' coverage, and that consumers MAY
resolve the sources for exact extents. A site announcing its buildings as
coverage sources is exactly that rule applied to composition — a coarse extent
for discovery, with the precise extents one resolution away.

**4 — Child health distinguishes silent from retired.** This is the
distinction a hierarchy most needs and the one ad-hoc designs usually miss. A
child that has stopped publishing is not the same as a child that has been
decommissioned, and both are expressible:

- A child leaving deliberately MUST dispose its `Announce` instance, and SHOULD
  publish `Depart` (§3.3.0, Announce Lifecycle). Consumers MUST treat that as
  removal from their directory.
- A child that merely goes quiet is detected by TTL expiry, the stated backstop
  for ungraceful departure — and under §2.14, loss of liveliness is **not**
  removal. A parent MUST NOT purge a durable child record because the child
  went silent.

So "my third floor is offline" and "my third floor is gone" are different
observable states, which is the whole point of a tombstone.

**5 — Cross-level identity is a binding.** An object tracked in a room and
again at the building level is one object with two component observations;
`core::EntityBinding` carries exactly that, referencing messages on other
topics without requiring either level to know the other's internal ids.

**6 — Roll-up is ordinary subscription.** Topic names carry the scene as a
segment (§3.3.1), so a parent subscribes to its children's topics with no
special mechanism, and discovery by geohash (§3.3.0) answers which scenes cover
a region. A roll-up is a consumer that subscribes widely, not a protocol
feature.

**The alignment picture.** None of this is novel, and the precedents are worth
naming. Frame trees with composable transforms are how ROS `tf` has expressed
articulated and nested spatial structure for over a decade. Containment
expressed as nested coverage with refinement on demand is the structure of 3D
Tiles, where a bounding volume hierarchy gives coarse culling and children give
detail. And for the built world, the identifiers already exist: a composed
scene SHOULD anchor to CityGML or IndoorGML identifiers through
`external_refs`-style references rather than restating a building hierarchy in
SpatialDDS types, because those vocabularies are maintained by the people who
survey buildings.

**The honest residual.** What the above expresses is *geometric* and
*operational* composition: where a child sits, what it covers, whether it is
alive, which observations are the same object. It does **not** express
*semantic* containment — the claim "this zone is part of that site" as an
assertion with a provenance, which someone could disagree with or retract. That
is a relationship claim and it needs a basis, which is exactly what the
provisional `spatial.owm` module declines to draft in 0.1: per-edge basis,
confidence, and retraction are deliberately excluded and reserved as open
design (Appendix E). Composed scenes are therefore expressible today without
that machinery, and semantic containment waits for it rather than being
approximated by a transform. A frame transform says where a thing is; it does
not say who claims it belongs.
