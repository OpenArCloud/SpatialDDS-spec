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

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
{{include:idl/v1.5/argeo.idl}}
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

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Mapping Extension 1.5
//
// Map lifecycle metadata, multi-source edge types, and inter-map
// alignment primitives for multi-agent collaborative mapping.

#ifndef SPATIAL_CORE_INCLUDED
#define SPATIAL_CORE_INCLUDED
#include "core.idl"
#endif

module spatial {
  module mapping {

    const string MODULE_ID = "spatial.mapping/1.5";

    typedef builtin::Time Time;
    typedef spatial::core::PoseSE3    PoseSE3;
    typedef spatial::core::FrameRef   FrameRef;
    typedef spatial::core::CovMatrix  CovMatrix;
    typedef spatial::core::BlobRef    BlobRef;
    typedef spatial::common::MetaKV   MetaKV;


    // ================================================================
    // 1. MAP METADATA
    // ================================================================

    // Representation kind — what type of spatial map this describes.
    // The enum identifies the high-level representation; the actual
    // encoding and codec live in TileMeta.encoding as today.
    enum MapKind {
      @value(0) POSE_GRAPH,       // sparse keyframe graph (Node + Edge)
      @value(1) OCCUPANCY_GRID,   // 2D or 2.5D grid (nav planning)
      @value(2) POINT_CLOUD,      // dense 3D point cloud
      @value(3) MESH,             // triangle mesh / surface
      @value(4) TSDF,             // truncated signed distance field
      @value(5) VOXEL,            // volumetric voxel grid
      @value(6) NEURAL_FIELD,     // NeRF, 3DGS, neural SDF (see neural profile)
      @value(7) FEATURE_MAP,      // visual place recognition / bag-of-words
      @value(8) SEMANTIC,         // semantic / panoptic map layer
      @value(9) OTHER
    };

    // Map status — lifecycle state.
    enum MapStatus {
      @value(0) BUILDING,         // actively being constructed (SLAM running)
      @value(1) OPTIMIZING,       // global optimization / bundle adjustment in progress
      @value(2) STABLE,           // optimized and not actively changing
      @value(3) FROZEN,           // immutable reference map (no further updates)
      @value(4) DEPRECATED        // superseded by a newer map; consumers should migrate
    };

    // Quality metrics — optional per-map health indicators.
    // All fields are optional via has_* flags to avoid mandating
    // metrics that not every SLAM system produces.
    @extensibility(APPENDABLE) struct MapQuality {
      boolean has_loop_closure_count;
      uint32  loop_closure_count;       // total loop closures accepted

      boolean has_mean_residual;
      double  mean_residual;            // mean constraint residual after optimization (meters)

      boolean has_max_drift_m;
      double  max_drift_m;              // estimated worst-case drift (meters)

      boolean has_coverage_pct;
      float   coverage_pct;             // fraction of declared extent actually mapped [0..1]

      boolean has_keyframe_count;
      uint32  keyframe_count;           // number of keyframes / nodes

      boolean has_landmark_count;
      uint32  landmark_count;           // number of 3D landmarks
    };

    // Top-level map descriptor. Published with RELIABLE + TRANSIENT_LOCAL
    // so late joiners discover all active maps immediately.
    //
    // One MapMeta per (map_id, source_id) — a single physical map may have
    // multiple representations (e.g., pose graph + occupancy grid + mesh),
    // each published as a separate MapMeta with the same map_id but
    // different kind and source_id.
    @extensibility(APPENDABLE) struct MapMeta {
      @key string map_id;               // unique map identifier
      @key string source_id;            // producing agent / SLAM system

      MapKind   kind;                   // representation type
      MapStatus status;                 // lifecycle state
      string    algorithm;              // e.g., "ORB-SLAM3", "Cartographer", "RTAB-Map", "LIO-SAM"
      FrameRef  frame_ref;              // map's canonical coordinate frame

      // Spatial extent (axis-aligned in frame_ref)
      boolean has_extent;
      spatial::core::Aabb3 extent;      // bounding box of mapped region

      // Geo-anchor: where this map sits on Earth (when known)
      boolean has_geopose;
      spatial::core::GeoPose geopose;   // map origin in WGS84

      // Versioning — aligns with core Node/Edge graph_epoch
      uint64  graph_epoch;              // increments on major rebases / merges
      uint64  revision;                 // monotonic within an epoch (fine-grained updates)

      // Quality
      boolean has_quality;
      MapQuality quality;

      // Timing
      Time    created;                  // map creation time
      Time    stamp;                    // last update time

      // Content references — how to get the map data
      // For pose graphs: subscribe to Node/Edge on the standard topic with this map_id
      // For dense maps: these blob_ids reference the backing TileMeta/BlobChunk data
      sequence<BlobRef, 32> blob_refs;  // optional: pre-built map artifacts

      // Extensible metadata (encoding details, sensor suite, etc.)
      sequence<MetaKV, 32> attributes;

      string schema_version;            // MUST be "spatial.mapping/1.5"
    };


    // ================================================================
    // 2. EXTENDED EDGE TYPES
    // ================================================================

    // Extends core::EdgeTypeCore (ODOM=0, LOOP=1) with constraint types
    // needed for multi-agent, multi-sensor pose graph optimization.
    //
    // Values 0-1 are identical to EdgeTypeCore. Core consumers that
    // only understand ODOM/LOOP can safely downcast by treating
    // unknown values as LOOP.
    enum EdgeType {
      @value(0)  ODOM,            // odometry (sequential)
      @value(1)  LOOP,            // intra-map loop closure
      @value(2)  INTER_MAP,       // cross-map loop closure (between two agents' maps)
      @value(3)  GPS,             // absolute pose from GNSS
      @value(4)  ANCHOR,          // constraint from recognizing a shared anchor
      @value(5)  IMU_PREINT,      // IMU pre-integration factor
      @value(6)  GRAVITY,         // gravity direction prior
      @value(7)  PLANE,           // planar constraint (e.g., ground plane)
      @value(8)  SEMANTIC,        // semantic co-observation ("both see the same door")
      @value(9)  MANUAL,          // human-provided alignment
      @value(10) OTHER
    };

    // Extended edge that carries the richer EdgeType plus provenance.
    // Supplements core::Edge — publishers that produce multi-source
    // constraints publish mapping::Edge; the fields are a superset
    // of core::Edge.
    @extensibility(APPENDABLE) struct Edge {
      string map_id;
      @key string edge_id;
      string from_id;                   // source node (may be in a different map_id)
      string to_id;                     // target node
      EdgeType type;                    // extended type enum
      PoseSE3 T_from_to;               // relative pose: from_id → to_id
      spatial::common::Mat6x6 information; // 6x6 info matrix (row-major)
      Time   stamp;
      string source_id;                 // who produced this constraint
      uint64 seq;
      uint64 graph_epoch;

      // Cross-map provenance (populated when type == INTER_MAP)
      boolean has_from_map_id;
      string  from_map_id;              // map_id of from_id's origin
      boolean has_to_map_id;
      string  to_map_id;                // map_id of to_id's origin

      // Match quality for loop closures and cross-map edges
      boolean has_match_score;
      float   match_score;              // similarity / inlier ratio [0..1]
      boolean has_inlier_count;
      uint32  inlier_count;             // feature inliers supporting this edge
    };


    // ================================================================
    // 3. MAP ALIGNMENT
    // ================================================================

    // How an alignment was established.
    enum AlignmentMethod {
      @value(0) VISUAL_LOOP,      // feature-based visual loop closure
      @value(1) LIDAR_ICP,        // point cloud registration (ICP / NDT)
      @value(2) ANCHOR_MATCH,     // shared anchor recognition
      @value(3) GPS_COARSE,       // GPS-derived coarse alignment
      @value(4) SEMANTIC_MATCH,   // semantic landmark co-observation
      @value(5) MANUAL,           // operator-provided ground truth
      @value(6) MULTI_METHOD,     // combination of methods
      @value(7) OTHER
    };

    // Inter-map transform: aligns map_id_from's frame to map_id_to's frame,
    // with provenance and quality metadata.
    //
    // This is the merge primitive. When a multi-robot SLAM system determines
    // that two maps overlap, it publishes a MapAlignment. Downstream consumers
    // (planning, visualization, fleet coordination) use this to reason across
    // maps without waiting for a full graph merge.
    @extensibility(APPENDABLE) struct MapAlignment {
      @key string alignment_id;         // unique alignment identifier

      string map_id_from;               // source map
      string map_id_to;                 // target map (reference)
      PoseSE3 T_to_from;               // transform: map_id_from frame → map_id_to frame
      CovMatrix cov;                    // uncertainty of the alignment

      AlignmentMethod method;           // how the alignment was computed
      Time   stamp;                     // when the alignment was computed
      string source_id;                 // who computed it

      // Quality evidence
      boolean has_match_score;
      float   match_score;              // overall alignment quality [0..1]
      boolean has_overlap_pct;
      float   overlap_pct;              // estimated spatial overlap [0..1]
      boolean has_supporting_edges;
      uint32  supporting_edges;         // number of cross-map edges backing this alignment

      // Versioning — alignment may be refined as more evidence accumulates
      uint64  revision;                 // monotonic; newer revision supersedes older

      // Optional: list of cross-map edge_ids that support this alignment
      sequence<string, 64> evidence_edge_ids;

      string schema_version;            // MUST be "spatial.mapping/1.5"
    };


    // ================================================================
    // 4. MAP LIFECYCLE EVENTS
    // ================================================================

    // Lightweight event published when a map undergoes a significant
    // lifecycle transition. Subscribers (fleet managers, UI dashboards,
    // data pipelines) can react without polling MapMeta.
    enum MapEventKind {
      @value(0) CREATED,          // new map started
      @value(1) EPOCH_ADVANCE,    // graph_epoch incremented (rebase / merge)
      @value(2) STATUS_CHANGE,    // status field changed (e.g., BUILDING → STABLE)
      @value(3) ALIGNMENT_NEW,    // new MapAlignment published involving this map
      @value(4) ALIGNMENT_UPDATE, // existing MapAlignment revised
      @value(5) DEPRECATED,       // map marked deprecated
      @value(6) DELETED           // map data removed from bus
    };

    @extensibility(APPENDABLE) struct MapEvent {
      @key string map_id;
      MapEventKind event;
      string source_id;
      Time   stamp;

      // Context (populated per event kind)
      boolean has_new_status;
      MapStatus new_status;             // for STATUS_CHANGE

      boolean has_new_epoch;
      uint64  new_epoch;                // for EPOCH_ADVANCE

      boolean has_alignment_id;
      string  alignment_id;             // for ALIGNMENT_NEW / ALIGNMENT_UPDATE

      // Human-readable reason
      boolean has_reason;
      string  reason;                   // e.g., "merged with map/robot-B after 42 loop closures"
    };

  }; // module mapping
};   // module spatial
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
// SPDX-License-Identifier: MIT
// SpatialDDS Spatial Events Extension 1.5
//
// Typed, spatially-scoped events for zone monitoring, anomaly detection,
// and smart infrastructure alerting.

#ifndef SPATIAL_CORE_INCLUDED
#define SPATIAL_CORE_INCLUDED
#include "core.idl"
#endif

module spatial {
  module events {

    const string MODULE_ID = "spatial.events/1.5";

    typedef builtin::Time Time;
    typedef spatial::core::PoseSE3   PoseSE3;
    typedef spatial::core::FrameRef  FrameRef;
    typedef spatial::core::Aabb3     Aabb3;
    typedef spatial::core::BlobRef   BlobRef;
    typedef spatial::common::MetaKV  MetaKV;


    // ================================================================
    // 1. SPATIAL ZONES
    // ================================================================

    // Zone classification — what kind of spatial region this is.
    enum ZoneKind {
      @value(0) RESTRICTED,       // entry prohibited or requires authorization
      @value(1) SPEED_LIMITED,    // maximum speed enforced
      @value(2) CAPACITY_LIMITED, // maximum occupancy enforced
      @value(3) ONE_WAY,          // directional traffic constraint
      @value(4) LOADING,          // loading/unloading area with dwell rules
      @value(5) HAZARD,           // known hazard zone (chemical, height, machinery)
      @value(6) MONITORING,       // general observation zone (no specific constraint)
      @value(7) GEOFENCE,         // boundary-crossing detection only
      @value(8) OTHER
    };

    // Named spatial region with associated rules.
    // Published with RELIABLE + TRANSIENT_LOCAL so late joiners
    // receive the full zone layout.
    @extensibility(APPENDABLE) struct SpatialZone {
      @key string zone_id;              // unique zone identifier

      string name;                      // human-readable name (e.g., "Loading Bay 3")
      ZoneKind kind;                    // zone classification
      FrameRef frame_ref;               // coordinate frame for geometry

      // Zone geometry (axis-aligned in frame_ref)
      Aabb3 bounds;                     // 3D bounding box

      // Optional geo-anchor for earth-fixed zones
      boolean has_geopose;
      spatial::core::GeoPose geopose;   // zone center in WGS84

      // Zone rules (optional per kind)
      boolean has_speed_limit_mps;
      float   speed_limit_mps;          // max speed in m/s (for SPEED_LIMITED)

      boolean has_capacity;
      uint32  capacity;                 // max occupancy count (for CAPACITY_LIMITED)

      boolean has_dwell_limit_sec;
      float   dwell_limit_sec;          // max dwell time in seconds (for LOADING, RESTRICTED)

      // Applicable object classes — which detection class_ids trigger events.
      // Empty means all classes.
      sequence<string, 32> class_filter;

      // Schedule (optional) — zone is only active during specified hours.
      // Format: ISO 8601 recurring interval or cron-like string in attributes.
      boolean has_schedule;
      string  schedule;                 // e.g., "R/2024-01-01T06:00:00/PT12H" or deployment-specific

      // Owner / authority
      string provider_id;               // who defines this zone
      Time   stamp;                     // last update time

      // Extensible metadata
      sequence<MetaKV, 16> attributes;

      string schema_version;            // MUST be "spatial.events/1.5"
    };


    // ================================================================
    // 2. SPATIAL EVENTS
    // ================================================================

    // Event type — what happened.
    enum EventType {
      @value(0)  ZONE_ENTRY,      // object entered the zone
      @value(1)  ZONE_EXIT,       // object exited the zone
      @value(2)  DWELL_TIMEOUT,   // object exceeded dwell time limit
      @value(3)  SPEED_VIOLATION, // object exceeded speed limit
      @value(4)  CAPACITY_BREACH, // zone occupancy exceeded capacity
      @value(5)  WRONG_WAY,       // object traveling against one-way direction
      @value(6)  PROXIMITY_ALERT, // two tracked objects closer than safe distance
      @value(7)  UNATTENDED,      // object stationary without associated person
      @value(8)  ANOMALY,         // general anomaly (ML-detected, pattern deviation)
      @value(9)  LINE_CROSS,      // object crossed a defined trip line
      @value(10) LOITERING,       // person/object lingering beyond threshold
      @value(11) TAILGATING,      // unauthorized entry following authorized person
      @value(12) OTHER
    };

    // Severity level.
    enum Severity {
      @value(0) INFO,             // informational (logging, analytics)
      @value(1) WARNING,          // advisory — may require attention
      @value(2) ALERT,            // actionable — requires human review
      @value(3) CRITICAL          // immediate intervention required
    };

    // Event lifecycle state.
    enum EventState {
      @value(0) ACTIVE,           // event is ongoing
      @value(1) RESOLVED,         // condition cleared (e.g., person left zone)
      @value(2) ACKNOWLEDGED,     // human acknowledged the event
      @value(3) SUPPRESSED        // suppressed by rule or operator
    };

    // A spatially-grounded event.
    //
    // Keyed by event_id. Publishers update the same event_id as state
    // changes (ACTIVE → RESOLVED). Subscribers use KEEP_LAST per key
    // to see the latest state of each event.
    @extensibility(APPENDABLE) struct SpatialEvent {
      @key string event_id;             // unique event identifier

      EventType  type;                  // what happened
      Severity   severity;              // how urgent
      EventState state;                 // lifecycle state

      // Where — zone reference (optional; not all events are zone-scoped)
      boolean has_zone_id;
      string  zone_id;                  // references SpatialZone.zone_id

      // Where — 3D position of the event (in the zone's or scene's frame_ref)
      boolean has_position;
      spatial::common::Vec3 position;   // event location (meters)
      FrameRef frame_ref;               // coordinate frame for position

      // What — triggering detection(s)
      boolean has_trigger_det_id;
      string  trigger_det_id;           // primary triggering Detection3D.det_id

      boolean has_trigger_track_id;
      string  trigger_track_id;         // tracked object ID (from Detection3D.track_id)

      string  trigger_class_id;         // class of triggering object (e.g., "person", "forklift")

      // Who — secondary object for relational events (PROXIMITY_ALERT, TAILGATING)
      boolean has_secondary_det_id;
      string  secondary_det_id;

      // Measured values (populated per event type)
      boolean has_measured_speed_mps;
      float   measured_speed_mps;       // for SPEED_VIOLATION

      boolean has_measured_dwell_sec;
      float   measured_dwell_sec;       // for DWELL_TIMEOUT, LOITERING, UNATTENDED

      boolean has_measured_distance_m;
      float   measured_distance_m;      // for PROXIMITY_ALERT

      boolean has_zone_occupancy;
      uint32  zone_occupancy;           // current count for CAPACITY_BREACH

      // Confidence
      float   confidence;               // [0..1] — event detection confidence

      // Evidence — optional media snapshot or clip
      boolean has_evidence;
      BlobRef evidence;                 // reference to snapshot image or video clip

      // Narrative — optional human-readable description
      boolean has_description;
      string  description;              // e.g., "Forklift stopped in pedestrian corridor
                                        //  near anchor loading-bay-3 for 4 minutes"

      // Timing
      Time   event_start;               // when the event condition began
      Time   stamp;                     // latest update time (may differ from event_start)

      // Producer
      string source_id;                 // who detected this event

      // Extensible metadata
      sequence<MetaKV, 8> attributes;

      string schema_version;            // MUST be "spatial.events/1.5"
    };


    // ================================================================
    // 3. ZONE STATE (periodic summary)
    // ================================================================

    // Lightweight periodic snapshot of a zone's current status.
    // Enables dashboards and capacity management without maintaining
    // event counters client-side.
    @extensibility(APPENDABLE) struct ZoneState {
      @key string zone_id;              // references SpatialZone.zone_id

      uint32 current_occupancy;         // number of tracked objects currently in zone
      boolean has_capacity;
      uint32  capacity;                 // echoed from SpatialZone for convenience

      // Active alert count by severity
      uint32 active_info;
      uint32 active_warning;
      uint32 active_alert;
      uint32 active_critical;

      // Class breakdown (optional — top N classes present)
      sequence<MetaKV, 8> class_counts; // namespace = class_id, json = {"count": N}

      Time   stamp;
      string source_id;
    };

  }; // module events
};   // module spatial
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
