// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.4 (© Open AR Cloud Initiative)

## **3\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

_See §2 Conventions for global normative rules._

### **3.1 IDL Profile Versioning & Negotiation (Normative)**

SpatialDDS uses semantic versioning tokens of the form `name@MAJOR.MINOR`.

* **MAJOR** increments for breaking schema or wire changes.
* **MINOR** increments for additive, compatible changes.

Identifier conventions: Profile tokens use `name@MAJOR.MINOR` (e.g., `core@1.4`). Module identifiers use `spatial.<profile>/MAJOR.MINOR` (e.g., `spatial.core/1.4`). These are canonically related: `core@1.4 ⇔ spatial.core/1.4`.

Participants advertise supported ranges via `caps.supported_profiles` (discovery) and manifest capabilities blocks. Consumers select the **highest compatible minor** within any shared major. Backward-compatibility clauses from 1.3 are retired; implementations only negotiate within their common majors. SpatialDDS 1.4 uses a single canonical quaternion order `(x, y, z, w)` across manifests, discovery payloads, and IDL messages.

### **3.2 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. All quaternion fields follow the OGC GeoPose component order `(x, y, z, w)` so orientation data can flow between GeoPose-aware systems without reordering. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

#### Frame Identifiers (Reference)

SpatialDDS uses structured frame references via the `FrameRef { uuid, fqn }` type.
See *Appendix G Frame Identifiers (Informative Reference)* for the complete definition and naming rules.

Each Transform expresses a pose that maps coordinates from the `from` frame into the `to` frame (parent → child).

### **3.3 Discovery**

Discovery is how SpatialDDS peers **find each other**, **advertise what they publish**, and **select compatible streams**. Think of it as a built-in directory that rides the same bus: nodes announce, others filter and subscribe.

#### How it works (at a glance)
1. **Announce** — each node periodically publishes an announcement with capabilities and topics.
2. **Query** — clients publish simple filters (by profile version, type, QoS) to narrow results.
3. **Select** — clients subscribe to chosen topics; negotiation picks the highest compatible minor per profile.

#### Key messages (abridged IDL)
*(Abridged IDL — see Appendix B for full definitions.)*
```idl
// Message shapes shown for orientation only
@extensibility(APPENDABLE) struct ProfileSupport { string name; uint32 major; uint32 min_minor; uint32 max_minor; boolean preferred; }
@extensibility(APPENDABLE) struct Capabilities   { sequence<ProfileSupport,64> supported_profiles; sequence<string,32> preferred_profiles; sequence<string,64> features; }
@extensibility(APPENDABLE) struct TopicMeta      { string name; string type; string version; string qos_profile; float32 target_rate_hz; uint32 max_chunk_bytes; }

@extensibility(APPENDABLE) struct Announce {
  // ... node identity, endpoints ...
  Capabilities caps;                  // profiles, preferences, features
  sequence<TopicMeta,128> topics;     // typed topics offered by this node
}

@extensibility(APPENDABLE) struct CoverageQuery {
  // minimal illustrative fields
  string expr;        // Appendix F.X grammar; e.g., "type==\"radar_tensor\" && profile==\"discovery@1.*\""
  string reply_topic; // topic to receive results
  string query_id;    // correlate request/response
}

The expression syntax is defined formally in the CoverageQuery ABNF grammar (see Appendix F.X).

@extensibility(APPENDABLE) struct CoverageResponse {
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
* Each advertised topic **MUST** declare `name`, `type`, `version`, and `qos_profile` per Topic Identity (§3.3.1); optional throughput hints (`target_rate_hz`, `max_chunk_bytes`) are additive.
* Discovery topics SHALL restrict `type` to {`geometry_tile`, `video_frame`, `radar_tensor`, `seg_mask`, `desc_array`}, `version` to `v1`, and `qos_profile` to {`GEOM_TILE`, `VIDEO_LIVE`, `RADAR_RT`, `SEG_MASK_RT`, `DESC_BATCH`}.
* `caps.preferred_profiles` is an optional tie-breaker **within the same major**.
* `caps.features` carries namespaced feature flags; unknown flags **MUST** be ignored.
* `CoverageQuery.expr` follows the boolean grammar in Appendix F.X and MAY filter on profile tokens (`name@MAJOR.*` or `name@MAJOR.MINOR`), topic `type`, and `qos_profile` strings.
* Responders page large result sets via `next_page_token`; every response **MUST** echo the caller’s `query_id`.

#### Asset references

Discovery announcements and manifests share a single `AssetRef` structure composed of URI, media type, integrity hash, and optional `MetaKV` metadata bags. AssetRef and MetaKV are normative types for asset referencing in the Discovery profile.

#### What fields mean (quick reference)
| Field | Use |
|------|-----|
| `caps.supported_profiles` | Version ranges per profile. Peers select the **highest compatible minor** within a shared major. |
| `caps.preferred_profiles` | Optional tie-breaker hint (only within a major). |
| `caps.features` | Optional feature flags (namespaced strings). Unknown flags can be ignored. |
| `topics[].type` / `version` / `qos_profile` | Topic Identity keys used to filter and match streams; see the allowed sets above. |
| `reply_topic`, `query_id` | Allows asynchronous, paged responses and correlation. |

#### Practical notes
* Announce messages stay small and periodic; re-announce whenever capabilities, coverage, or topics change.
* Queries are stateless filters. Responders may page through results; clients track `next_page_token` until empty.
* Topic names follow `spatialdds/<domain>/<stream>/<type>/<version>` per §3.3.1; filter by `type` and `qos_profile` instead of parsing payloads.
* Negotiation is automatic once peers see each other’s `supported_profiles`; emit diagnostics like `NO_COMMON_MAJOR(name)` when selection fails.

#### Summary
Discovery keeps the wire simple: nodes publish what they have, clients filter for what they need, and the system converges on compatible versions. Use typed topic metadata to choose streams, rely on capabilities to negotiate versions without additional application-level handshakes, and treat discovery traffic as the lightweight directory for every SpatialDDS deployment.

#### **3.3.1 Topic Naming (Normative)**

SpatialDDS topics are identified by a structured **name**, a **type**, a **version**, and a declared **Quality-of-Service (QoS)** profile. Together these define both *what* a stream carries and *how* it behaves on the wire.

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

#### **3.3.2 Typed Topics Registry**

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Large, reliable transfers |
| `video_frame` | Encoded video/image | Real-time camera streams |
| `radar_tensor` | N-D float/int tensor | Structured radar data |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation |
| `desc_array` | Feature descriptor sets | Vector or embedding batches |

These registered types ensure consistent topic semantics without altering wire framing. New types can be registered additively through this table or extensions.

Implementations defining custom `type` and `qos_profile` values SHOULD follow the naming pattern (`myorg.depth_frame`, `DEPTH_LIVE`) and document their DDS QoS mapping.

#### **3.3.3 QoS Profiles**

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

For each advertised topic, `type`, `version`, and `qos_profile` MUST be present and MUST either match a registered value in this specification or a documented deployment-specific extension.

Consumers use these three keys to match and filter streams without inspecting payload bytes. Brokers and routers SHOULD isolate lanes by `(topic, stream_id, qos_profile)` to avoid head-of-line blocking.

#### **3.3.4 Coverage Model (Normative)**

- `coverage_frame_ref` is the canonical frame for an announcement. `CoverageElement.frame_ref` MAY override it, but SHOULD be used sparingly (e.g., mixed local frames). If absent, consumers MUST use `coverage_frame_ref`.
- When `coverage_eval_time` is present, consumers SHALL evaluate any referenced transforms at that instant before interpreting `coverage_frame_ref`.
- `global == true` means worldwide coverage regardless of regional hints. Producers MAY omit `bbox`, `geohash`, or `elements` in that case.
- When `global == false`, producers MAY supply any combination of regional hints; consumers SHOULD treat the union of all regions as the effective coverage.
- Manifests MAY provide any combination of `bbox`, `geohash`, and `elements`. Discovery coverage MAY omit `geohash` and rely solely on `bbox` and `aabb`. Consumers SHALL treat all hints consistently according to the Coverage Model.
- When `has_bbox == true`, `bbox` MUST contain finite coordinates; consumers SHALL reject non-finite values. When `has_bbox == false`, consumers MUST ignore `bbox` entirely. Same rules apply to `has_aabb` and `aabb`.
- Earth-fixed frames (`fqn` rooted at `earth-fixed`) encode WGS84 longitude/latitude/height. Local frames MUST reference anchors or manifests that describe the transform back to an earth-fixed root (Appendix G).
- Discovery announces and manifests share the same coverage semantics and flags. `CoverageQuery` responders SHALL apply these rules consistently when filtering or paginating results.
- See §2 Conventions for global normative rules.

### Earth-fixed roots and local frames

For global interoperability, SpatialDDS assumes that earth-fixed frames
(e.g., WGS84 longitude/latitude/height) form the root of the coverage
hierarchy. Local frames (for devices, vehicles, buildings, or ships) may
appear in coverage elements, but if the coverage is intended to be
globally meaningful, these local frames must be relatable to an
earth-fixed root through declared transforms or manifests.

Implementations are not required to resolve every local frame at runtime,
but when they do, the resulting coverage must be interpretable in an
earth-fixed reference frame.

#### Coverage Evaluation Pseudocode (Informative)
```
if coverage.global:
    regions = WORLD
else:
    regions = union(bbox, geohash, elements[*].aabb)
frame = coverage_frame_ref unless element.frame_ref present
evaluate transforms at coverage_eval_time if present
```

##### Implementation Guidance (Non-Normative)

* No change to on-wire framing — this metadata lives at the discovery layer.
* Named QoS profiles simplify cross-vendor interoperability and diagnostics.
* For custom types, follow the same naming pattern and document new QoS presets.
* All examples and tables herein are **additive**.

##### Discovery recipe (tying the examples together)

1. **Announce** — the producer sends `Announce` (see JSON example above) to advertise `caps` and `topics`.
2. **CoverageQuery** — the consumer issues a `CoverageQuery` (see query JSON) to filter by profile, topic type, or QoS.
3. **CoverageResponse** — the Discovery producer replies with `CoverageResponse` (see response JSON), returning results plus an optional `next_page_token` for pagination.

### **3.4 Anchors**

The Anchors profile provides a structured way to share and update collections of durable, world-locked anchors. While Core includes individual GeoAnchor messages, this profile introduces constructs such as AnchorSet for publishing bundles (e.g., a venue’s anchor pack) and AnchorDelta for lightweight updates. This makes it easy for clients to fetch a set of anchors on startup, stay synchronized through incremental changes, and request full snapshots when needed. Anchors complement VPS results by providing the persistent landmarks that make AR content and multi-device alignment stable across sessions and users.

### **3.5 Profiles Summary**

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

- spatial.core/1.4
- spatial.discovery/1.4
- spatial.anchors/1.4
- spatial.manifest/1.4 (manifest schema profile for SpatialDDS 1.4)
- spatial.argeo/1.4
- spatial.sensing.common/1.4
- spatial.sensing.rad/1.4
- spatial.sensing.lidar/1.4
- spatial.sensing.vision/1.4
- spatial.slam_frontend/1.4
- spatial.vio/1.4
- spatial.semantics/1.4

The Sensing module family keeps sensor data interoperable: `sensing.common` unifies pose stamps, calibration blobs, ROI negotiation, and quality reporting. Radar, lidar, and vision modules extend that base without redefining shared scaffolding, ensuring multi-sensor deployments can negotiate payload shapes and interpret frame metadata consistently.

