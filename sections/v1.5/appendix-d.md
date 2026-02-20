## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The **Sensing Common** module supplies reusable sensing metadata, ROI negotiation structures, and codec/payload descriptors that the specialized sensor profiles build upon. The VIO profile carries raw and fused IMU/magnetometer samples. The Vision profile shares camera metadata, encoded frames, and optional feature tracks for perception pipelines. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The Radar profile provides detection-centric radar metadata and per-frame detection sets, plus a tensor transport path for raw or processed radar data cubes used in ISAC and ML workloads. The Lidar profile transports compressed point clouds, associated metadata, and optional detections for mapping and perception workloads. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content. The Mapping profile provides map lifecycle metadata, multi-source pose graph edge types, inter-map alignment primitives, and lifecycle events for multi-agent collaborative mapping. The Spatial Events profile provides typed, spatially-scoped events, zone definitions, and zone state summaries for smart infrastructure alerting, anomaly detection, and capacity management.*

> Common type aliases and geometry primitives are defined once in Appendix A. Extension modules import those shared definitions and MUST NOT re-declare them.

### **Sensing Common Extension**

*Shared base types, enums, and ROI negotiation utilities reused by all sensing profiles (radar, lidar, vision).* 

```idl
{{include:idl/v1.5/common.idl}}
```

### **Standard Sequence Bounds (Normative)**

| Payload                           | Recommended Bound   | Rationale                              |
|-----------------------------------|---------------------|----------------------------------------|
| 2D Detections (per frame)         | `SZ_MEDIUM` (2048)  | Typical object detectors               |
| 3D Detections (LiDAR)             | `SZ_SMALL` (256)    | Clusters/objects, not raw points       |
| Radar Detections (micro-dets)     | `SZ_XL` (32768)     | Numerous sparse returns per frame      |
| Keypoints/Tracks (per frame)      | `SZ_LARGE` (8192)   | Feature-rich frames                    |

Producers SHOULD choose the smallest tier that covers real workloads; exceeding these bounds requires a new profile minor.

#### Axis Encoding (Normative)

The `Axis` struct embeds a discriminated union to ensure only one encoding is transmitted on the wire.

```idl
enum AxisEncoding { AXIS_CENTERS = 0, AXIS_LINSPACE = 1 };
@extensibility(APPENDABLE) struct Linspace { double start; double step; uint32 count; };
@extensibility(APPENDABLE) union AxisSpec switch (AxisEncoding) {
  case AXIS_CENTERS:  sequence<double, 65535> centers;
  case AXIS_LINSPACE: Linspace lin;
  default: ;
};
@extensibility(APPENDABLE) struct Axis { string name; string unit; AxisSpec spec; };
```

* `AXIS_CENTERS` — Explicit sample positions carried as `double` values.
* `AXIS_LINSPACE` — Uniform grid defined by `start + i * step` for `i ∈ [0, count‑1]`.
* Negative `step` indicates descending axes.
* `count` MUST be ≥ 1 and `step * (count – 1) + start` yields the last coordinate.


## IDL Tooling Notes (Non-Consecutive Enums)

Several enumerations in the SpatialDDS 1.5 profiles use **intentionally
sparse or non-consecutive numeric values**. These enums are designed for
forward extensibility (e.g., reserving ranges for future codecs, layouts, or
pixel formats). Because of this, certain DDS toolchains (including Cyclone
DDS’s `idlc`) may emit **non-fatal warnings** such as:

> “enum literal values are not consecutive”

These warnings do *not* indicate a schema error. All affected enums are
valid IDL4.x and interoperable on the wire.

The intentionally sparse enums are:
- `CovarianceType` (types.idl)
- `Codec` (common.idl)
- `PayloadKind` (common.idl)
- `RigRole` (vision.idl)
- `RadSensorType` (rad.idl)
- `RadTensorLayout` (rad.idl)
- `CloudEncoding` (lidar.idl)
- `ColorSpace` (vision.idl)
- `PixFormat` (vision.idl)

No changes are required for implementers. These warnings may be safely
ignored.

### **VIO / Inertial Extension**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
{{include:idl/v1.5/vio.idl}}
```

### **Vision Extension**

*Camera intrinsics, video frames, and keypoints/tracks for perception and analytics pipelines. ROI semantics follow §2 Conventions for global normative rules; axes use the Sensing Common AXIS_CENTERS/AXIS_LINSPACE union encoding.* See §2 Conventions for global normative rules.

**Pre-Rectified Images (Normative)**  
When images have been rectified (undistorted) before publication, producers MUST set `dist = NONE`, `dist_params` to an empty sequence, and `model = PINHOLE`. Consumers receiving `dist = NONE` MUST NOT apply any distortion correction.

**Image Dimensions (Normative)**  
`CamIntrinsics.width` and `CamIntrinsics.height` are REQUIRED and MUST be populated from the actual image dimensions. A `VisionMeta` sample with `width = 0` or `height = 0` is malformed and consumers MAY reject it.

**Distortion Model Mapping (Informative)**  
Vision uses `CamModel` + `Distortion`, while SLAM Frontend uses `DistortionModelKind`. Implementers bridging the two SHOULD map as follows:

| Vision | SLAM Frontend | Notes |
|---|---|---|
| `Distortion.NONE` | `DistortionModelKind.NONE` | No distortion |
| `Distortion.RADTAN` | `DistortionModelKind.RADTAN` | Brown-Conrady |
| `Distortion.KANNALA_BRANDT` | `DistortionModelKind.KANNALA_BRANDT` | Fisheye |
| `CamModel.FISHEYE_EQUIDISTANT` | `DistortionModelKind.EQUIDISTANT` | Equivalent naming |

```idl
{{include:idl/v1.5/vision.idl}}
```

### **SLAM Frontend Extension**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

```idl
{{include:idl/v1.5/slam_frontend.idl}}
```

### **Semantics / Perception Extension**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).*

**Size Convention (Normative)**  
`Detection3D.size` is the extent of the oriented bounding box in the object's local frame (center + q):  
`size[0]` = width (local X), `size[1]` = height (local Z), `size[2]` = depth (local Y).  
All values are in meters and MUST be non-negative. For datasets that use `(width, length, height)`, map as `(width, height, length)`.

```idl
{{include:idl/v1.5/semantics.idl}}
```

### **Radar Extension**

*Radar metadata, per-frame detection sets, and raw/processed tensor transport. The detection-centric path (`RadSensorMeta` / `RadDetectionSet`) serves automotive-style point detections. The tensor path (`RadTensorMeta` / `RadTensorFrame`) serves raw or processed radar data cubes for ISAC and ML workloads. Deployments may use either or both. ROI semantics follow §2 Conventions for global normative rules.* See §2 Conventions for global normative rules.

```idl
{{include:idl/v1.5/rad.idl}}
```

### **Lidar Extension**

*Lidar metadata, compressed point cloud frames, and detections. ROI semantics follow §2 Conventions for global normative rules; axes use the Sensing Common AXIS_CENTERS/AXIS_LINSPACE union encoding.* See §2 Conventions for global normative rules.

**`BIN_INTERLEAVED` Encoding (Normative)**  
`BIN_INTERLEAVED` indicates raw interleaved binary where each point is a contiguous record of fields defined by the `PointLayout` enum. There is no header. The ring field is serialized as `uint16` per the `LidarDetection.ring` type.

| Layout | Fields per point | Default byte-width per field |
|---|---|---|
| `XYZ_I` | x, y, z, intensity | 4 × float32 = 16 bytes |
| `XYZ_I_R` | x, y, z, intensity, ring | 4 × float32 + 1 × uint16 = 18 bytes |
| `XYZ_I_R_N` | x, y, z, intensity, ring, nx, ny, nz | 4 × float32 + 1 × uint16 + 3 × float32 = 30 bytes |
| `XYZ_I_R_T` | x, y, z, intensity, ring, t | 4 × float32 + 1 × uint16 + 1 × float32 = 22 bytes |
| `XYZ_I_R_T_N` | x, y, z, intensity, ring, t, nx, ny, nz | 4 × float32 + 1 × uint16 + 1 × float32 + 3 × float32 = 34 bytes |

When `BIN_INTERLEAVED` is used, consumers MUST interpret the blob as `N × record_size` bytes where `N = blob_size / record_size`.

**Per-Point Timestamps (Normative)**  
Layouts `XYZ_I_R_T` and `XYZ_I_R_T_N` include a per-point relative timestamp field `t` serialized as `float32`, representing seconds elapsed since `FrameHeader.t_start`. Consumers performing motion compensation SHOULD use `t_start + point.t` as the acquisition time for each point.

**Computing `t_end` for Spinning Lidars (Informative)**  
When a source provides only `t_start`, producers SHOULD compute `t_end` as `t_start + (1.0 / nominal_rate_hz)` for spinning lidars, or as `t_start + max(point.t)` when per-point timestamps are available. Producers MUST populate `t_end` rather than leaving it as zero.

```idl
{{include:idl/v1.5/lidar.idl}}
```

### **AR + Geo Extension**

*Multi-frame geo-referenced nodes for AR clients, VPS services, and multi-agent alignment.*

`NodeGeo` extends `core::Node` with an array of metric poses in different coordinate frames and an optional geographic anchor. A VPS service localizing a client against multiple overlapping maps returns one `NodeGeo` carrying poses in each map's frame. In hierarchical spaces (building → floor → room → table), the same message carries poses at every level of the hierarchy. Consumers select the frame they need; producers include only the frames they can compute.

The `poses` array uses `core::FramedPose` — each entry is self-contained with its own frame reference and covariance. This replaces the previous pattern of a single bare `PoseSE3` with frame_ref and cov as sibling fields, which could only express one local pose and left the relationship between the top-level cov and the geopose's cov ambiguous.

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS AR+Geo 1.5

#ifndef SPATIAL_CORE_INCLUDED
#define SPATIAL_CORE_INCLUDED
#include "core.idl"
#endif

module spatial {
  module argeo {

    const string MODULE_ID = "spatial.argeo/1.5";

    typedef builtin::Time Time;
    typedef spatial::core::PoseSE3    PoseSE3;
    typedef spatial::core::FramedPose FramedPose;
    typedef spatial::core::GeoPose    GeoPose;
    typedef spatial::core::CovMatrix  CovMatrix;
    typedef spatial::common::FrameRef FrameRef;

    // A pose-graph node with one or more metric-frame poses and an
    // optional geographic anchor.
    //
    // Keyed by node_id (same key as core::Node). Published alongside
    // core::Node when geo-referencing is available.
    //
    // poses[] carries the node's position in one or more local/metric
    // coordinate frames. Each FramedPose is self-contained (pose +
    // frame_ref + cov + stamp). Typical entries:
    //   - SLAM map frame (always present)
    //   - ENU frame anchored to a surveyed point
    //   - Building / floor / room frames in hierarchical spaces
    //   - Alternative map frames when multiple maps overlap
    //
    // geopose provides the WGS84 anchor (lat/lon/alt) when known.
    // It remains a separate field because geographic coordinates use
    // degrees, not meters — they cannot share the FramedPose type.
    @extensibility(APPENDABLE) struct NodeGeo {
      string map_id;
      @key string node_id;               // same id as core::Node

      // One or more metric poses in different frames.
      // The first entry SHOULD be the primary SLAM map frame.
      // Additional entries provide the same physical pose expressed
      // in alternative coordinate frames (other maps, hierarchical
      // spaces, ENU anchors). Consumers select by frame_ref.
      sequence<FramedPose, 8> poses;

      // Geographic anchor (optional — absent for indoor-only maps)
      boolean has_geopose;
      GeoPose geopose;

      string  source_id;
      uint64  seq;                       // per-source monotonic
      uint64  graph_epoch;               // increments on major rebases/merges
    };

  }; // module argeo
};

```

**Usage scenarios (informative):**

*Multi-map localization:* A VPS service localizes a client against three overlapping maps and returns:
```json
{
  "node_id": "vps-fix/client-42/0017",
  "map_id": "mall-west",
  "poses": [
    {
      "pose": { "t": [12.3, -4.1, 1.5], "q": [0, 0, 0, 1] },
      "frame_ref": { "uuid": "aaa-...", "fqn": "mall-west/lidar-map" },
      "cov": { "type": "COV_POSE6", "pose": [ ... ] },
      "stamp": { "sec": 1714071000, "nanosec": 0 }
    },
    {
      "pose": { "t": [12.1, -4.3, 1.5], "q": [0, 0, 0.01, 1] },
      "frame_ref": { "uuid": "bbb-...", "fqn": "mall-west/photo-map" },
      "cov": { "type": "COV_POSE6", "pose": [ ... ] },
      "stamp": { "sec": 1714071000, "nanosec": 0 }
    }
  ],
  "has_geopose": true,
  "geopose": {
    "lat_deg": 37.7749, "lon_deg": -122.4194, "alt_m": 15.0,
    "q": [0, 0, 0, 1], "frame_kind": "ENU",
    "frame_ref": { "uuid": "ccc-...", "fqn": "earth-fixed/enu" },
    "stamp": { "sec": 1714071000, "nanosec": 0 },
    "cov": { "type": "COV_POS3", "pos": [ ... ] }
  },
  "source_id": "vps/mall-west-service",
  "seq": 17,
  "graph_epoch": 3
}
```

*Hierarchical spaces:* A localization service returns poses in building, floor, and room frames:
```json
{
  "node_id": "vps-fix/headset-07/0042",
  "map_id": "building-west",
  "poses": [
    {
      "pose": { "t": [45.2, 22.1, 9.3], "q": [0, 0, 0, 1] },
      "frame_ref": { "uuid": "bld-...", "fqn": "building-west/enu" },
      "cov": { "type": "COV_POS3", "pos": [ ... ] },
      "stamp": { "sec": 1714071000, "nanosec": 0 }
    },
    {
      "pose": { "t": [15.2, 8.1, 0.3], "q": [0, 0, 0, 1] },
      "frame_ref": { "uuid": "fl3-...", "fqn": "building-west/floor-3" },
      "cov": { "type": "COV_POS3", "pos": [ ... ] },
      "stamp": { "sec": 1714071000, "nanosec": 0 }
    },
    {
      "pose": { "t": [3.2, 2.1, 0.3], "q": [0, 0, 0, 1] },
      "frame_ref": { "uuid": "rmB-...", "fqn": "building-west/floor-3/room-B" },
      "cov": { "type": "COV_POS3", "pos": [ ... ] },
      "stamp": { "sec": 1714071000, "nanosec": 0 }
    }
  ],
  "has_geopose": true,
  "geopose": { "lat_deg": 37.7750, "lon_deg": -122.4190, "alt_m": 24.3, "..." : "..." },
  "source_id": "vps/building-west-indoor",
  "seq": 42,
  "graph_epoch": 1
}
```

### **Mapping Extension**

*Map lifecycle metadata, multi-source edge types, inter-map alignment, and lifecycle events for multi-agent collaborative mapping.*

The Core profile provides the mechanical primitives for map data: `Node`/`Edge` for pose graphs, `TileMeta`/`TilePatch`/`BlobRef` for geometry transport, `FrameTransform` for frame alignment, and `SnapshotRequest`/`SnapshotResponse` for tile catch-up. The SLAM Frontend profile carries feature-level data for re-localization. The Anchors profile handles durable landmarks with incremental sync.

This extension adds the **map lifecycle layer** — the metadata and coordination types that let multiple independent SLAM agents discover, align, merge, version, and qualify each other's maps without prior arrangement:

- **`MapMeta`** — top-level map descriptor: what exists, what it covers, its quality and lifecycle state.
- **`mapping::Edge`** — extends `core::Edge` with richer constraint types for multi-source pose graphs (cross-map loop closures, GPS, anchor, IMU, semantic constraints).
- **`MapAlignment`** — the inter-map transform with provenance, uncertainty, and evidence references.
- **`MapEvent`** — lightweight lifecycle notifications so subscribers react to map state changes without polling.

**Design note — no new map formats.** This profile does not add occupancy grid, TSDF, or voxel map types. Those are representation-specific formats expressed as `TileMeta.encoding` values (e.g., `"occupancy_grid/uint8"`, `"tsdf/f32"`, `"voxel_hash/f32"`). The mapping profile addresses **coordinating and aligning maps**, not inventing new map formats.

**Topic Layout**

| Type | Topic | QoS | Notes |
|---|---|---|---|
| `MapMeta` | `spatialdds/<scene>/mapping/meta/v1` | RELIABLE + TRANSIENT\_LOCAL, KEEP\_LAST(1) per key | One sample per (map\_id, source\_id). Late joiners get current state. |
| `mapping::Edge` | `spatialdds/<scene>/mapping/edge/v1` | RELIABLE, KEEP\_ALL | Superset of `core::Edge` for multi-source constraints. |
| `MapAlignment` | `spatialdds/<scene>/mapping/alignment/v1` | RELIABLE + TRANSIENT\_LOCAL, KEEP\_LAST(1) per key | Durable inter-map transforms. |
| `MapEvent` | `spatialdds/<scene>/mapping/event/v1` | RELIABLE, KEEP\_LAST(32) | Lightweight lifecycle notifications. |

Core `Node` and `Edge` topics remain unchanged. Agents that produce cross-map constraints publish on the `mapping/edge` topic; agents that only produce intra-map odometry/loop closures continue using core topics. Consumers that need cross-map awareness subscribe to both.

**Range-only constraints:** When `type == RANGE`, the edge carries a scalar distance measurement between `from_id` and `to_id` in the `range_m` / `range_std_m` fields. The `T_from_to` and `information` fields SHOULD be set to identity / zero respectively. Pose graph optimizers that encounter a RANGE edge SHOULD treat it as a distance-only factor: `||pos(from_id) - pos(to_id)|| = range_m`. Common sources include UWB inter-robot ranging, acoustic ranging (underwater), and BLE RSSI-derived distances. Range edges may reference nodes in different maps (with `has_from_map_id` / `has_to_map_id` populated), enabling range-assisted inter-map alignment.

```idl
{{include:idl/v1.5/mapping.idl}}
```

### **Spatial Events Extension**

*Typed, spatially-scoped events for zone monitoring, anomaly detection, and smart infrastructure alerting. Bridges perception streams (Detection3DSet) and application logic (fleet management, building automation, safety systems).*

The Semantics profile provides spatial facts — "what is where." This extension adds spatial interpretations — "something happened that matters." Events are derived from perception streams plus zone definitions plus temporal rules (dwell thresholds, speed limits, capacity caps). They are typed, severity-graded, tied to triggering detections, and scoped to named spatial zones.

The profile defines three types:

- **`SpatialZone`** — named spatial regions with rules (restricted, speed-limited, capacity-capped). Published latched so all participants know the zone layout.
- **`SpatialEvent`** — typed event tied to a zone, triggering detection, optional media evidence, and severity.
- **`ZoneState`** — periodic zone occupancy and status snapshot for dashboards and capacity management.

**Integration with Discovery:** Zone publishers announce via `disco::Announce` with `kind: OTHER` (or a future `ZONE_MANAGER` kind) and `coverage` matching the zone's spatial extent. Consumers use `CoverageQuery` filtered by `module_id_in: ["spatial.events/1.5"]` to discover event sources in a region. `SpatialZone` geometry reuses the same `Aabb3` and `FrameRef` primitives as `CoverageElement`, ensuring consistent spatial reasoning.

**Topic Layout**

| Type | Topic | QoS | Notes |
|---|---|---|---|
| `SpatialZone` | `spatialdds/<scene>/events/zone/v1` | RELIABLE + TRANSIENT\_LOCAL, KEEP\_LAST(1) per key | Latched zone definitions. Late joiners get full zone set. |
| `SpatialEvent` | `spatialdds/<scene>/events/event/v1` | RELIABLE, KEEP\_LAST(64) | Event stream. Consumers filter by zone\_id, severity, event type. |
| `ZoneState` | `spatialdds/<scene>/events/zone\_state/v1` | BEST\_EFFORT, KEEP\_LAST(1) per key | Periodic zone status snapshots. |

```idl
{{include:idl/v1.5/events.idl}}
```

**Example JSON (Informative)**

Zone Definition:
```json
{
  "zone_id": "zone/facility-west/pedestrian-corridor-B",
  "name": "Pedestrian Corridor B",
  "kind": "RESTRICTED",
  "frame_ref": { "uuid": "f1a2b3c4-...", "fqn": "facility-west/enu" },
  "bounds": { "min_xyz": [10.0, 0.0, 0.0], "max_xyz": [25.0, 5.0, 3.0] },
  "has_geopose": false,
  "has_speed_limit_mps": false,
  "has_capacity": false,
  "has_dwell_limit_sec": true,
  "dwell_limit_sec": 120.0,
  "class_filter": ["forklift", "agv", "pallet_truck"],
  "has_schedule": true,
  "schedule": "R/2024-01-01T06:00:00/PT14H",
  "provider_id": "safety/zone-manager",
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "schema_version": "spatial.events/1.5"
}
```

Event:
```json
{
  "event_id": "evt/facility-west/2024-04-26T12:05:00Z/001",
  "type": "DWELL_TIMEOUT",
  "severity": "ALERT",
  "state": "ACTIVE",
  "has_zone_id": true,
  "zone_id": "zone/facility-west/pedestrian-corridor-B",
  "has_position": true,
  "position": [17.2, 2.1, 0.5],
  "frame_ref": { "uuid": "f1a2b3c4-...", "fqn": "facility-west/enu" },
  "has_trigger_det_id": true,
  "trigger_det_id": "det/fused/forklift-07",
  "has_trigger_track_id": true,
  "trigger_track_id": "track/forklift-07",
  "trigger_class_id": "forklift",
  "has_measured_dwell_sec": true,
  "measured_dwell_sec": 247.0,
  "confidence": 0.94,
  "has_evidence": true,
  "evidence": { "blob_id": "snap-20240426-120500-cam3", "role": "evidence/jpeg", "checksum": "sha256:ab12..." },
  "has_description": true,
  "description": "Forklift stopped in pedestrian corridor B near loading-bay-3 for 4 min 7 sec",
  "event_start": { "sec": 1714131653, "nanosec": 0 },
  "stamp": { "sec": 1714131900, "nanosec": 0 },
  "source_id": "analytics/zone-monitor",
  "schema_version": "spatial.events/1.5"
}
```
