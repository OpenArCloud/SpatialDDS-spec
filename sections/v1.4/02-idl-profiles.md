// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.4 (© Open AR Cloud Initiative)

## **2\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

### **2.1 IDL Profile Versioning & Negotiation (Normative)**

SpatialDDS uses semantic versioning tokens of the form `name@MAJOR.MINOR`.

* **MAJOR** increments for breaking schema or wire changes.
* **MINOR** increments for additive, compatible changes.

Participants advertise supported ranges via `caps.supported_profiles` (discovery) and manifest capabilities blocks. Consumers select the **highest compatible minor** within any shared major. Backward-compatibility clauses from 1.3 are retired; implementations only negotiate within their common majors. All legacy quaternion and field-compatibility shims are removed—SpatialDDS 1.4 uses a single canonical quaternion order `(x, y, z, w)` across manifests, discovery payloads, and IDL messages.

### **2.2 Optional Fields (Normative)**

SpatialDDS encodes optionality explicitly. To avoid ambiguous parsing and sentinel misuse, producers and consumers SHALL follow these rules across every profile:

* **Presence flags** — For any scalar, struct, or array field that may be absent at runtime, producers SHALL introduce a boolean presence flag immediately before the field (`boolean has_field; Type field;`). Consumers MUST ignore the field when the flag is `false`.
* **Discriminated unions** — When exactly one of multiple alternatives may appear on the wire, model the choice as a discriminated union (e.g., `CovMatrix`). Do not overload presence flags for mutual exclusivity.
* **@appendable omission is only for evolution** — Schema omission via `@appendable` remains reserved for forward/backward compatibility. Producers SHALL NOT omit fields at runtime to signal “missing data.”
* **No NaN sentinels** — Floating-point NaN (or other sentinel values) MUST NOT be used to indicate absence. Presence flags govern field validity.

These conventions apply globally (Core, Discovery, Anchors, and all Sensing extensions) and supersede earlier guidance that relied on NaN or implicit omission semantics.

> **Clarification:** `@appendable` omission remains reserved for schema evolution across versions. Runtime optionality SHALL be expressed with presence flags or discriminated unions. NaN sentinels and implicit omissions are deprecated as of SpatialDDS 1.5.

### **2.3 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. All quaternion fields follow the OGC GeoPose component order `(x, y, z, w)` so orientation data can flow between GeoPose-aware systems without reordering. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

#### Frame Identifiers (Reference)

SpatialDDS uses structured frame references via the `FrameRef { uuid, fqn }` type.  
See *Appendix G Frame Identifiers (Normative)* for the complete definition and naming rules.

### **2.4 Discovery**

Discovery is how SpatialDDS peers **find each other**, **advertise what they publish**, and **select compatible streams**. Think of it as a built-in directory that rides the same bus: nodes announce, others filter and subscribe.

#### How it works (at a glance)
1. **Announce** — each node periodically publishes an announcement with capabilities and topics.
2. **Query** — clients publish simple filters (by profile version, type, QoS) to narrow results.
3. **Select** — clients subscribe to chosen topics; negotiation picks the highest compatible minor per profile.

#### Key messages (abridged IDL)
```idl
// Message shapes shown for orientation only
@appendable struct ProfileSupport { string name; uint32 major; uint32 min_minor; uint32 max_minor; boolean preferred; }
@appendable struct Capabilities   { sequence<ProfileSupport,64> supported_profiles; sequence<string,32> preferred_profiles; sequence<string,64> features; }
@appendable struct TopicMeta      { string name; string type; string version; string qos_profile; float32 target_rate_hz; uint32 max_chunk_bytes; }

@appendable struct Announce {
  // ... node identity, endpoints ...
  Capabilities caps;                  // profiles, preferences, features
  sequence<TopicMeta,128> topics;     // typed topics offered by this node
}

@appendable struct CoverageQuery {
  // minimal illustrative fields
  string expr;        // Appendix F.X grammar; e.g., "type==\"radar_tensor\" && profile==\"discovery@1.*\""
  string reply_topic; // topic to receive results
  string query_id;    // correlate request/response
}

@appendable struct CoverageResponse {
  string query_id;
  sequence<Announce,256> results;
  string next_page_token;
}
```

#### Minimal examples (JSON)
**Announce (capabilities + topics)**
```json
{
  "caps": {
    "supported_profiles": [
      { "name": "core",           "major": 1, "min_minor": 0, "max_minor": 3 },
      { "name": "discovery",      "major": 1, "min_minor": 1, "max_minor": 2 }
    ],
    "preferred_profiles": ["discovery@1.2"],
    "features": ["blob.crc32"]
  },
  "topics": [
    { "name": "spatialdds/perception/cam_front/video_frame/v1", "type": "video_frame", "version": "v1", "qos_profile": "VIDEO_LIVE" },
    { "name": "spatialdds/perception/radar_1/radar_tensor/v1",  "type": "radar_tensor", "version": "v1", "qos_profile": "RADAR_RT"   }
  ]
}
```

**Query + Response**
```json
{ "query_id": "q1", "expr": "type==\"radar_tensor\" && profile==\"discovery@1.*\"", "reply_topic": "spatialdds/sys/queries/q1" }
```
```json
{ "query_id": "q1", "results": [ { "caps": { "supported_profiles": [ { "name": "discovery", "major": 1, "min_minor": 1, "max_minor": 2 } ] }, "topics": [ { "name": "spatialdds/perception/radar_1/radar_tensor/v1", "type": "radar_tensor", "version": "v1", "qos_profile": "RADAR_RT" } ] } ], "next_page_token": "" }
```

#### Norms & filters
* Announces **MUST** include `caps.supported_profiles`; peers choose the highest compatible minor within a shared major.
* Each advertised topic **MUST** declare `name`, `type`, `version`, and `qos_profile` per Topic Identity (§2.4.1); optional throughput hints (`target_rate_hz`, `max_chunk_bytes`) are additive.
* `caps.preferred_profiles` is an optional tie-breaker **within the same major**.
* `caps.features` carries namespaced feature flags; unknown flags **MUST** be ignored.
* `CoverageQuery.expr` follows the boolean grammar in Appendix F.X and MAY filter on profile tokens (`name@MAJOR.*` or `name@MAJOR.MINOR`), topic `type`, and `qos_profile` strings.
* Responders page large result sets via `next_page_token`; every response **MUST** echo the caller’s `query_id`.

#### What fields mean (quick reference)
| Field | Use |
|------|-----|
| `caps.supported_profiles` | Version ranges per profile. Peers select the **highest compatible minor** within a shared major. |
| `caps.preferred_profiles` | Optional tie-breaker hint (only within a major). |
| `caps.features` | Optional feature flags (namespaced strings). Unknown flags can be ignored. |
| `topics[].type` / `version` / `qos_profile` | Topic Identity keys used to filter and match streams. |
| `reply_topic`, `query_id` | Allows asynchronous, paged responses and correlation. |

#### Practical notes
* Announce messages stay small and periodic; re-announce whenever capabilities, coverage, or topics change.
* Queries are stateless filters. Responders may page through results; clients track `next_page_token` until empty.
* Topic names follow `spatialdds/<domain>/<stream>/<type>/<version>`; filter by `type` and `qos_profile` instead of parsing payloads.
* Negotiation is automatic once peers see each other’s `supported_profiles`; emit diagnostics like `NO_COMMON_MAJOR(name)` when selection fails.

#### Summary
Discovery keeps the wire simple: nodes publish what they have, clients filter for what they need, and the system converges on compatible versions. Use typed topic metadata to choose streams, rely on capabilities to negotiate versions without handshakes, and treat discovery traffic as the lightweight directory for every SpatialDDS deployment.

#### **2.4.1 Topic Identity & QoS (Normative)**

SpatialDDS topics are identified by a structured **name**, a **type**, a **version**, and a declared **Quality-of-Service (QoS) profile**. Together these define both *what* a stream carries and *how* it behaves on the wire.

##### Topic Naming Pattern

Each topic follows this pattern:
```
spatialdds/<domain>/<stream>/<type>/<version>
```
| Segment | Meaning | Example |
|----------|----------|----------|
| `<domain>` | Logical app domain | `perception` |
| `<stream>` | Sensor or stream ID | `cam_front` |
| `<type>` | Registered data type | `video_frame` |
| `<version>` | Schema or message version | `v1` |

###### Example
```json
{
  "name": "spatialdds/perception/radar_1/radar_tensor/v1",
  "type": "radar_tensor",
  "version": "v1",
  "qos_profile": "RADAR_RT"
}
```

##### Registered Types (v1)

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Large, reliable transfers |
| `video_frame` | Encoded video/image | Real-time camera streams |
| `radar_tensor` | N-D float/int tensor | Structured radar data |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation |
| `desc_array` | Feature descriptor sets | Vector or embedding batches |

These registered types ensure consistent topic semantics without altering wire framing. New types can be registered additively through this table or extensions.

##### Standard QoS Profiles (v1)

QoS profiles define delivery guarantees and timing expectations for each topic type.

| Profile | Reliability | Ordering | Typical Deadline | Use Case |
|----------|--------------|----------|------------------|-----------|
| `GEOM_TILE` | Reliable | Ordered | 200 ms | 3D geometry, large tile data |
| `VIDEO_LIVE` | Best-effort | Ordered | 33 ms | Live video feeds |
| `VIDEO_ARCHIVE` | Reliable | Ordered | 200 ms | Replay or stored media |
| `RADAR_RT` | Partial | Ordered | 20 ms | Real-time radar tensors |
| `SEG_MASK_RT` | Best-effort | Ordered | 33 ms | Live segmentation masks |
| `DESC_BATCH` | Reliable | Ordered | 100 ms | Descriptor or feature batches |

###### Notes

* Each topic advertises its `qos_profile` during discovery.
* Profiles capture trade-offs between latency, reliability, and throughput.
* Implementations may tune low-level DDS settings, but the profile name is canonical.
* Mixing unrelated data (e.g., radar + video) in a single QoS lane is discouraged.

##### Discovery and Manifest Integration

Every `Announce.topics[]` entry and manifest topic reference SHALL include:
- `type` — one of the registered type values
- `version` — the schema or message version
- `qos_profile` — one of the standard or extended QoS names

Consumers use these three keys to match and filter streams without inspecting payload bytes. Brokers and routers SHOULD isolate lanes by `(topic, stream_id, qos_profile)` to avoid head-of-line blocking.

##### Implementation Guidance (Non-Normative)

* No change to on-wire framing — this metadata lives at the discovery layer.
* Named QoS profiles simplify cross-vendor interoperability and diagnostics.
* For custom types, follow the same naming pattern and document new QoS presets.
* All examples and tables herein are **additive**; legacy 1.3 compatibility language has been removed.

### **2.5 Anchors**

The Anchors profile provides a structured way to share and update collections of durable, world-locked anchors. While Core includes individual GeoAnchor messages, this profile introduces constructs such as AnchorSet for publishing bundles (e.g., a venue’s anchor pack) and AnchorDelta for lightweight updates. This makes it easy for clients to fetch a set of anchors on startup, stay synchronized through incremental changes, and request full snapshots when needed. Anchors complement VPS results by providing the persistent landmarks that make AR content and multi-device alignment stable across sessions and users.

### **2.6 Canonical Ordering & Identity (Normative)**

This section applies to any message that includes the trio: `Time stamp`, `string source_id`, and `uint64 seq`.

**Field semantics**

* `stamp` — Event time chosen by the producer (may reflect device/measurement time and is not guaranteed globally monotonic across sources).
* `source_id` — Stable writer identity within a deployment (e.g., a sensor, process, or node).
* `seq` — Per-`source_id` strictly monotonic unsigned 64-bit counter that increments by 1 for each new sample.

**Identity & idempotency**

* The canonical identity of a sample is the tuple **(`source_id`, `seq`)**.
* Consumers MUST treat duplicated **(`source_id`, `seq`)** as the same logical sample (idempotent).
* If `seq` wraps or resets, the producer MUST change `source_id` (or use a profile that defines an explicit writer epoch).

**Ordering rules**

1. **Within a single source (intra-source):** Order by `seq` only.
   * If two samples share the same `seq`, the later-arriving one supersedes the earlier; implementations SHOULD log a single warning per stream.
   * Missing `seq` values indicate loss under RELIABLE QoS and MAY trigger application-level recovery.
2. **Across multiple sources (inter-source merge):** Order by the tuple **(`stamp`, `source_id`, `seq`)** within a bounded reordering window Δ chosen by the consumer (e.g., 100–200 ms).
   * `stamp` provides the coarse global axis; `source_id` and `seq` disambiguate ties and ensure stability.
   * Consumers MUST NOT enforce global monotonicity by `stamp` alone; clock skew and late arrivals MUST be tolerated within Δ.

**Clock guidance**

* Producers SHOULD time-sync (NTP/PTP) where feasible.
* Consumers SHOULD bound out-of-order buffering by Δ and proceed deterministically when the window elapses.

**Notes**

* These rules are additive to transport-level ordering; they define application-level determinism independent of QoS.
* Profiles MAY further refine recovery behavior on gaps (e.g., retries, hole-filling) without altering this canonical ordering.

### **2.6 Profiles Summary**

The complete SpatialDDS IDL bundle is organized into the following profiles:

* **Core Profile**  
  Fundamental building blocks: pose graphs, geometry tiles, anchors, transforms, and blob transport.  
* **Discovery Profile**
   Lightweight announce messages plus active query/response bindings for services, coverage areas, anchors, and spatial content or experiences.
* **Anchors Profile**  
  Durable anchors and the Anchor Registry, enabling persistent world-locked reference points.

Together, Core, Discovery, and Anchors form the foundation of SpatialDDS, providing the minimal set required for interoperability.

* **Extensions**
  * **Sensing Module Family**: `sensing.common` defines shared frame metadata, calibration, QoS hints, and codec descriptors. Radar, lidar, and vision profiles inherit those types and layer on their minimal deltas—`RadDetectionSet`/`RadTensor`/`beam_params` for radar, `PointCloud`/`ScanBlock`/`return_type` for lidar, and `ImageFrame`/`SegMask`/`FeatureArray` for vision. Deployments MAY import the specialized profiles independently but SHOULD declare the `sensing.common@1.x` dependency when they do.
  * **VIO Profile**: Raw and fused IMU and magnetometer samples for visual-inertial pipelines.
  * **SLAM Frontend Profile**: Features, descriptors, and keyframes for SLAM and SfM pipelines.
  * **Semantics Profile**: 2D and 3D detections for AR occlusion, robotics perception, and analytics.
  * **AR+Geo Profile**: GeoPose, frame transforms, and geo-anchoring structures for global alignment and persistent AR content.
* **Provisional Extensions (Optional)**
  * **Neural Profile**: Metadata for neural fields (e.g., NeRFs, Gaussian splats) and optional view-synthesis requests.
  * **Agent Profile**: Generic task and status messages for AI agents and planners.

Together, these profiles give SpatialDDS the flexibility to support robotics, AR/XR, digital twins, IoT, and AI world models—while ensuring that the wire format remains lightweight, codec-agnostic, and forward-compatible.

#### **Profile Matrix (SpatialDDS 1.4)**

- spatial.core/1.0
- spatial.discovery/1.0
- spatial.anchors/1.0
- spatial.argeo/1.0
- spatial.sensing.common/1.0
- spatial.sensing.rad/1.0
- spatial.sensing.lidar/1.0
- spatial.sensing.vision/1.0
- spatial.slam_frontend/1.0
- spatial.vio/1.0
- spatial.semantics/1.0

The Sensing module family keeps sensor data interoperable: `sensing.common` unifies pose stamps, calibration blobs, ROI negotiation, and quality reporting. Radar, lidar, and vision modules extend that base without redefining shared scaffolding, ensuring multi-sensor deployments can negotiate payload shapes and interpret frame metadata consistently.

