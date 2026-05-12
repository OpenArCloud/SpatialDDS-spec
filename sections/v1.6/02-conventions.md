// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.6 (© Open AR Cloud Initiative)

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

- Optional scalars, structs, and arrays MUST be guarded by an explicit `has_*` boolean immediately preceding the field.
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

- **Geographic CRS (WGS84):** `bbox` arrays MUST use GeoJSON ordering: `[lon_min, lat_min, lon_max, lat_max]` (2D) or `[lon_min, lat_min, alt_min, lon_max, lat_max, alt_max]` (3D).
- **Local / ENU CRS:** `Aabb3` uses `{min_xyz, max_xyz}` where each is a `Vec3` in the local coordinate frame.

JSON examples throughout this specification MUST follow these conventions. Where a `CoverageElement` uses `crs = "EPSG:4326"`, the `bbox` array uses GeoJSON ordering. Where `crs` is absent or local, the `aabb` field uses `Aabb3` semantics.

### **2.11 Schema Stability Signaling (Normative)**

The `schema_version` string present on all Meta and Frame types (e.g., `"spatial.sensing.vision/1.5"`) implicitly indicates stability: profiles listed in Appendices A–D are stable; profiles in Appendix E are provisional or informative.

For runtime discrimination, producers of provisional types SHOULD include a `MetaKV` entry with `namespace = "schema"` and key `stability` set to `"provisional"`. Consumers in production deployments MAY use this flag to filter or warn on provisional data.

Example:

```json
{
  "namespace": "schema",
  "json": "{\"stability\": \"provisional\"}"
}
```

Additionally, the `caps.features` field in `Announce` MAY carry feature flags prefixed with `provisional.` (e.g., `"provisional.rf_beam"`, `"provisional.radio"`). Consumers MAY filter `Announce` messages to exclude provisional features in production deployments.

### **2.12 Coordinate Axis Convention (Normative)**

`FrameRef` carries an optional `coord_convention` field (added in 1.6) that specifies the axis convention for all poses expressed in this frame. The five predefined conventions are:

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
