// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.5 (© Open AR Cloud Initiative)

## **2. Conventions (Normative)**

This section centralizes the rules that apply across every SpatialDDS profile. Individual sections reference these shared requirements instead of repeating them. See Appendix A (core), Appendix B (discovery), Appendix C (anchors), and Appendix D (extensions) for the canonical IDL definitions that implement these conventions.

### **2.1 Orientation & Frame References**

- All quaternion fields, manifests, and IDLs SHALL use the `(x, y, z, w)` order that aligns with OGC GeoPose.
- Frames are represented exclusively with `FrameRef { uuid, fqn }`. The UUID is authoritative; the fully qualified name is a human-readable alias. Appendix G defines the authoritative frame model.
- Example JSON shape:
  ```json
  "frame_ref": { "uuid": "00000000-0000-4000-8000-000000000000", "fqn": "earth-fixed/map/device" }
  ```

### **2.2 Optional Fields & Discriminated Unions**

- Optional scalars, structs, and arrays MUST be guarded by an explicit `has_*` boolean immediately preceding the field.
- Mutually exclusive payloads SHALL be modeled as discriminated unions; do not overload presence flags to signal exclusivity.
- Schema evolution leverages `@extensibility(APPENDABLE)`; omit fields only when the IDL version removes them, never as an on-wire sentinel.
- See `CovMatrix` in Appendix A for the reference discriminated union pattern used for covariance.

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
SpatialDDS deployments that require authentication, authorization, integrity, or confidentiality over DDS **MUST** use **OMG DDS Security**.

**Minimum conformance profile:**
- **Authentication:** PKI-based authentication as defined by DDS Security.
- **Access control:** governance and permissions documents configured per DDS Security.
- **Cryptographic protection:** when confidentiality or integrity is required by policy, endpoints **MUST** enable DDS Security cryptographic plugins to provide message protection.

**Operational mapping (non-exhaustive):**
- Participants join a DDS **Domain**; security configuration applies to DomainParticipants and topics as governed by DDS Security governance rules.
- Discovery/ANNOUNCE messages that convey service identifiers, manifest URIs, or access hints **SHOULD** be protected when operating on untrusted networks.

**Interoperability note (informative):**
This specification does not redefine DDS Security. Implementations should use vendor-compatible DDS Security configuration mechanisms.
