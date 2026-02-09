## **Appendix J: Comparison with ROS 2 (Informative)**

*This appendix compares SpatialDDS 1.5 with ROS 2 (Jazzy / Rolling, circa 2025) across architecture, message design, and deployment scope. The goal is to help implementers who are familiar with one system understand the other, and to clarify where the two are complementary rather than competing.*

---

### **J.1 Architectural Differences**

SpatialDDS is a protocol specification -- a set of IDL profiles over OMG DDS. It defines message schemas, QoS contracts, discovery semantics, and coordinate conventions, but provides no build system, CLI tools, or simulation bindings.

ROS 2 is a full robotics framework. It includes a middleware abstraction (rmw) that defaults to DDS, a build system (colcon/ament), CLI tooling (`ros2 topic`, `ros2 bag`), visualization (RViz2), simulation integration (Gazebo), and thousands of community packages. Its message definitions are distributed across independently maintained packages (`sensor_msgs`, `geometry_msgs`, `vision_msgs`, `radar_msgs`, `nav_msgs`).

Because both systems use DDS as their transport layer, they can coexist on the same DDS domain. A ROS 2 node and a SpatialDDS participant can exchange data directly when message types are aligned, or through a lightweight bridge when they are not.

| Dimension | SpatialDDS 1.5 | ROS 2 |
|---|---|---|
| Identity | Protocol specification over DDS | Full robotics framework with DDS middleware |
| IDL corpus | Single versioned spec with profiles | Fragmented across independent packages |
| Extensibility | `@extensibility(APPENDABLE)` on all structs | `.msg` files require new versions for changes |
| Payload strategy | Blob-reference: large data out of band via `BlobRef` | Inline: pixel/point data carried in message body |
| Schema version | Embedded `schema_version` field per Meta struct | Per-package versioning; no cross-package version |

---

### **J.2 Coordinate Frames & Transforms**

Both systems use `(x, y, z, w)` quaternion component order. Orientation data flows between them without reordering.

| Dimension | SpatialDDS 1.5 | ROS 2 |
|---|---|---|
| Frame identity | `FrameRef { uuid, fqn }` -- UUID authoritative | `string frame_id` -- plain string |
| Frame graph | `PoseSE3` DAG with anchors bridging local to global | `tf2` strict tree via `/tf` and `/tf_static` topics |
| Geo-anchoring | First-class: `GeoAnchor`, GeoPose, VPS integration | GPS via `NavSatFix`; geo-transforms are custom |
| Handedness | Not prescribed; semantics defined by transform chains | REP-0103: right-handed, X-forward/Y-left/Z-up |
| Convention table | §2 maps nuScenes, Eigen, Unity, Unreal, OpenXR, glTF | No formal conversion table |

SpatialDDS's `FrameRef` model with UUIDs is designed for multi-device environments where string collisions between independent participants would be problematic. ROS 2's string-based `frame_id` is simpler and sufficient for single-robot or tightly coordinated fleets.

---

### **J.3 Sensor Message Comparison**

#### Camera / Vision

| Dimension | SpatialDDS `sensing.vision` | ROS 2 `sensor_msgs` |
|---|---|---|
| Metadata | `VisionMeta` (latched) + per-frame `VisionFrame` | `CameraInfo` sent with every frame |
| Intrinsics | `CamModel` enum + explicit `fx/fy/cx/cy` | `float64[9] K` matrix + free-form `distortion_model` string |
| Distortion | `Distortion` enum (NONE, RADTAN, KB) with normative `dist = NONE` prose | Free-form string; no enum constraint |
| Pixel format | `PixFormat` enum + `ColorSpace` enum | Free-form `string encoding`; no color space |
| Rig support | `RigRole` enum (12 values incl. PANORAMIC, EQUIRECTANGULAR) + `rig_id` | No standard rig concept |
| Compression | `Codec` enum including H.264/H.265/AV1 | `CompressedImage` with free-form `format` string |
| Keyframe | `is_key_frame` boolean | Not standardized |

SpatialDDS separates static metadata (latched once) from per-frame indices, avoiding redundant intrinsics on every frame. ROS 2 sends `CameraInfo` alongside every `Image`, which is simpler but repetitive.

#### Lidar

| Dimension | SpatialDDS `sensing.lidar` | ROS 2 `sensor_msgs` |
|---|---|---|
| Point layout | `PointLayout` enum (XYZ_I, XYZ_I_R, XYZ_I_R_T, etc.) | `PointField[]` -- arbitrary user-defined fields |
| Encoding | `CloudEncoding` enum (PCD, PLY, LAS, BIN_INTERLEAVED, DRACO, MPEG_PCC) | Raw binary only; compressed formats via community packages |
| Per-point timestamps | `XYZ_I_R_T` layout with normative `t` field semantics | Custom `PointField` named "t"; no standard |
| Sensor metadata | `LidarMeta` (latched): type, rings, range, FOV | No standard lidar metadata message |
| Frame timing | `t_start` / `t_end` with normative computation guidance | Single `Header.stamp` |

ROS 2's `PointCloud2` is maximally flexible -- any field layout is expressible via `PointField[]`. SpatialDDS constrains layouts via enum, enabling static validation and optimized deserialization at the cost of reduced flexibility for exotic field combinations.

#### Radar

| Dimension | SpatialDDS `sensing.rad` | ROS 2 `radar_msgs` |
|---|---|---|
| Fields per detection | 16+ (xyz, velocity variants, RCS, dyn_prop, uncertainty, track ID) | 5 (range, azimuth, elevation, doppler_velocity, amplitude) |
| Position | Cartesian `xyz_m` | Polar (range + angles) |
| Velocity | Cartesian + radial + ego-compensated (three options) | Radial only (`doppler_velocity`) |
| Dynamic property | `RadDynProp` enum (7 values) | Not present |
| Sensor type | `RadSensorType` enum (SHORT/MEDIUM/LONG/IMAGING_4D/SAR) | Not present |
| Uncertainty | Per-detection position/velocity RMS, ambiguity state, false alarm probability | Not present |
| Sensor metadata | `RadSensorMeta` (latched): range limits, FOV, velocity limits | Not present |
| Tensor transport | `RadTensorMeta` / `RadTensorFrame` for raw or processed radar cubes | Not present |

SpatialDDS radar supports both detection-centric outputs (automotive datasets like nuScenes, Continental ARS 408) and raw/processed radar cubes via tensor transport for ISAC and ML pipelines. ROS 2 `radar_msgs` is minimal and has seen limited community adoption; many teams define custom messages.

#### Semantics / Object Detections

| Dimension | SpatialDDS `semantics` | ROS 2 `vision_msgs` |
|---|---|---|
| Multi-hypothesis | Single `class_id` + `score` per detection | `ObjectHypothesisWithPose[]` -- multiple class+pose hypotheses |
| Size convention | Normative: `(width, height, depth)` with dataset mapping | Not specified |
| Attributes | `sequence<MetaKV, 8>` with guard | Not present |
| Visibility | `float [0..1]` with guard | Not present |
| Evidence counts | `num_lidar_pts`, `num_radar_pts` | Not present |
| Covariance | `Mat3x3 cov_pos` + `Mat3x3 cov_rot` (separate) | `float64[36]` full 6x6 pose covariance |
| Spatial tiling | `TileKey` for spatial indexing | Not present |

ROS 2 `vision_msgs` supports multi-hypothesis detections; SpatialDDS provides richer annotation metadata that is valuable for dataset-scale workflows and multi-sensor fusion pipelines.

---

### **J.4 Discovery & Spatial Awareness**

| Dimension | SpatialDDS 1.5 | ROS 2 |
|---|---|---|
| Discovery | Application-level: ANNOUNCE / QUERY / REPLY with coverage geometry and capability negotiation | Transport-level: DDS SPDP/SEDP; application introspection via `ros2` CLI |
| Spatial filtering | CoverageModel with AABBs, spheres, geofences -- subscribers filter by spatial region | Not present; topic-level subscription only |
| ROI negotiation | ROIRequest / ROIReply for sensor ROI control | RegionOfInterest in CameraInfo; no request/reply pattern |
| Service manifests | JSON manifests with anchors, capabilities, sensor descriptions; resolvable via `spatialdds://` URIs | Launch files + `package.xml`; no runtime manifest standard |

SpatialDDS treats "where is this data relevant?" as a first-class protocol concern. ROS 2 relies on DDS-level endpoint discovery and topic names for data routing.

---

### **J.5 Large Payload Transport**

SpatialDDS uses a blob-reference architecture: DDS messages carry lightweight metadata and `BlobRef` pointers; actual sensor payloads (images, point clouds) are transferred via `BlobChunk` sequences or external blob stores. This decouples the control plane from the data plane and is designed for WAN-scale deployments where not every subscriber needs raw sensor data.

ROS 2 carries payloads inline. `sensor_msgs/Image` includes the full pixel array; `PointCloud2` includes all point data. This is simpler to implement and works well within a single machine or local network. For bandwidth-constrained links, community packages (`image_transport`, `point_cloud_transport`) add pluggable compression, but these are not part of the core message definitions.

---

### **J.6 Ecosystem & Tooling**

| Dimension | SpatialDDS 1.5 | ROS 2 |
|---|---|---|
| Visualization | DDS vendor tools; custom | RViz2, Foxglove, PlotJuggler |
| Simulation | DDS bridge to Gazebo / Isaac Sim | Native Gazebo, Isaac Sim, CARLA integration |
| Recording | DDS vendor recording | `rosbag2` -- standardized |
| Build system | N/A (protocol spec) | colcon / ament / CMake |
| Package ecosystem | Emerging (OpenArCloud) | Thousands of packages; active community |
| Embedded | DDS on embedded (Micro-XRCE-DDS) | micro-ROS via Micro-XRCE-DDS |

---

### **J.7 Complementary Deployment Pattern**

SpatialDDS and ROS 2 are not mutually exclusive. The recommended integration pattern for teams using both:

1. **On-robot:** ROS 2 manages the local perception-to-control pipeline. Sensor drivers publish `sensor_msgs` topics; perception nodes consume them; planners and controllers close the loop.
2. **Cross-device:** A bridge node subscribes to ROS 2 topics and publishes spatial summaries -- detections, pose updates, anchor observations -- to SpatialDDS topics. Other devices (AR headsets, infrastructure sensors, fleet coordinators) consume SpatialDDS data without needing a ROS 2 installation.
3. **Discovery:** SpatialDDS's ANNOUNCE / QUERY / REPLY protocol handles multi-stakeholder service discovery and spatial coverage negotiation -- capabilities that ROS 2 does not provide at the application layer.

This separation keeps the robot's internal pipeline in the well-supported ROS 2 ecosystem while using SpatialDDS for the inter-device spatial coordination it was designed for.

| Scenario | Better fit |
|---|---|
| Single-robot perception -> planning -> control | ROS 2 |
| Multi-device spatial alignment (AR + robots + infrastructure) | SpatialDDS |
| Automotive sensor fusion with rich radar/annotation metadata | SpatialDDS |
| Digital twin with spatial queries and coverage filtering | SpatialDDS |
| Rapid prototyping with simulation and visualization | ROS 2 |
| Manipulation and arm control | ROS 2 |
| Cross-domain interop (city, IoT, AR, robotics on one bus) | SpatialDDS |
| Fleet robotics with heterogeneous sensors | Either; complementary |
