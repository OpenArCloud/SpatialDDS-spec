## **Appendix I: Dataset Conformance Testing (Informative)**

*This appendix documents systematic conformance testing performed against four public reference datasets. The results validated the completeness and expressiveness of the SpatialDDS 1.5 sensing, mapping, coordination, and spatial events profiles and directly informed several normative additions to this specification.*

### **Motivation**

Sensor-data specifications risk becoming disconnected from real-world workloads if they are designed in isolation. To guard against this, the SpatialDDS 1.5 profiles were validated against four complementary datasets that together exercise the full signal-to-semantics pipeline and multi-agent coordination:

| Dataset | Focus | Modalities Stressed |
|---|---|---|
| **nuScenes** (Motional / nuTonomy) | Perception → semantics | Camera (6×), lidar, radar detections (5×), 3D annotations, coordinate conventions |
| **DeepSense 6G** (ASU Wireless Intelligence Lab) | Signal → perception | Raw radar I/Q tensors, 360° cameras, lidar, IMU, GPS-RTK, mmWave beam vectors |
| **S3E** (Sun Yat-sen University / HKUST) | Multi-agent coordination | 3 UGVs × (lidar, stereo, IMU), UWB inter-robot ranging, RTK-GNSS, collaborative SLAM |
| **ScanNet** (TU Munich / Princeton) | Indoor scene understanding | RGB-D depth frames, 3D surface mesh, instance segmentation (NYU40), room-level zones, 20 scene types |

nuScenes was chosen because it stresses sensor diversity, per-detection radar fields rarely found in other corpora (compensated velocity, dynamic property, RCS), and rich annotation metadata (visibility, attributes, evidence counts). DeepSense 6G was chosen because it stresses signal-level data (raw FMCW radar cubes, phased-array beam power vectors) and ISAC modalities absent from traditional perception datasets. S3E was chosen because it is the first collaborative SLAM dataset with UWB inter-robot ranging and exercises the multi-agent capabilities — map lifecycle, inter-map alignment, range-only constraints, and fleet discovery — that differentiate SpatialDDS from single-vehicle frameworks such as ROS 2. ScanNet was chosen because it is the definitive indoor RGB-D scene understanding benchmark, uniquely exercises depth sensing (`DEPTH16`) and the Spatial Events extension (room zones, object-in-room events, per-class occupancy counts), and validates the semantics profile's instance segmentation types against a rich 40-class indoor vocabulary.

The goal was not to certify particular datasets but to answer two concrete questions: *Can every field, enum, and convention in each dataset's schema be losslessly mapped to SpatialDDS 1.5 IDL without workarounds or out-of-band agreements?* And for multi-agent scenarios: *Can the full coordination lifecycle — from independent mapping through inter-map alignment — be expressed using the standard types?*

### **Methodology**

For each dataset, a conformance harness was constructed as a self-contained Python 3 script that:

1. **Mirrors the SpatialDDS 1.5 IDL** as Python data structures (enum values, struct field lists, normative prose flags).
2. **Mirrors the dataset schema** as synthetic data (sensor names, field lists, data shapes).
3. **Runs targeted checks**, each producing a verdict:

| Verdict | Meaning |
|---|---|
| **PASS** | Dataset field maps losslessly to an existing SpatialDDS type or enum value. |
| **GAP** | A mapping exists conceptually but the required SpatialDDS type or field does not yet exist. |
| **MISSING** | No SpatialDDS construct exists for the dataset field; a new profile is needed. |

4. **Reports a per-modality scorecard.**

Neither nuScenes nor DeepSense 6G harness requires network access, a DDS runtime, or a dataset download. Both operate as static schema-vs-schema dry runs, reproducible in any CI environment. The S3E (§I.3) and ScanNet (§I.4) conformance sections were performed as manual schema analyses following the same check structure; scripted harnesses are planned for a future revision.

---

### **I.1 nuScenes Conformance**

#### Reference Dataset

**nuScenes** (Motional / nuTonomy) is a multimodal autonomous driving dataset containing:

| Dimension | Value |
|---|---|
| Scenes | 1,000 (20 s each) |
| Cameras | 6 surround-view (FRONT, FRONT_LEFT, FRONT_RIGHT, BACK, BACK_LEFT, BACK_RIGHT) |
| Lidar | 1 x 32-beam spinning (Velodyne HDL-32E), ~34 k points/scan |
| Radar | 5 x Continental ARS 408 (FRONT, FRONT_LEFT, FRONT_RIGHT, BACK_LEFT, BACK_RIGHT) |
| 3D annotations | 1.4 M oriented bounding boxes, 23 object classes |
| Annotation metadata | visibility tokens, attribute tokens, per-box lidar/radar point counts |
| Coordinate convention | Right-handed; quaternions in (w, x, y, z) order |

#### Checks Performed (27)

##### Radar — Detection Path (6 checks)

| ID | Check | Description |
|---|---|---|
| R-01 | Detection-centric profile | `RadDetection` struct exists with per-detection xyz, velocity, RCS, dyn_prop. |
| R-02 | Per-detection velocity | Cartesian `velocity_xyz` (preferred) + scalar `v_r_mps` (fallback), both with `has_*` guards. |
| R-03 | Ego-compensated velocity | `velocity_comp_xyz` field for ego-motion-compensated velocity. |
| R-04 | Dynamic property enum | `RadDynProp` covers all 7 nuScenes values (UNKNOWN through STOPPED). |
| R-05 | Per-detection RCS | `rcs_dbm2` field in dBm² with `has_rcs_dbm2` guard. |
| R-06 | Sensor type enum | `RadSensorType` differentiates SHORT_RANGE, LONG_RANGE, IMAGING_4D, etc. |

##### Vision (5 checks)

| ID | Check | Description |
|---|---|---|
| V-01 | RigRole coverage | `RigRole` enum includes FRONT, FRONT_LEFT, FRONT_RIGHT, BACK, BACK_LEFT, BACK_RIGHT. |
| V-02 | Pre-rectified images | Normative prose documents `dist = NONE` with `model = PINHOLE` semantics. |
| V-03 | Image dimensions | `CamIntrinsics.width` / `height` are REQUIRED; zero values are malformed. |
| V-04 | Keyframe flag | `VisionFrame.is_key_frame` boolean. |
| V-05 | Quaternion reorder | §2 table maps nuScenes `(w,x,y,z)` to SpatialDDS `(x,y,z,w)`. |

##### Lidar (6 checks)

| ID | Check | Description |
|---|---|---|
| L-01 | BIN_INTERLEAVED encoding | `CloudEncoding` value for raw interleaved binary with normative record layout table. |
| L-02 | Per-point timestamps | `PointLayout.XYZ_I_R_T` and `XYZ_I_R_T_N` with normative prose for the `t` field. |
| L-03 | Metadata guards | `LidarMeta` uses `has_range_limits`, `has_horiz_fov`, `has_vert_fov` guards. |
| L-04 | Timestamp presence flag | `LidarFrame.has_per_point_timestamps` signals per-point timing in the blob. |
| L-05 | t_end computation | Normative guidance for computing `t_end` from `t_start + 1/rate_hz` or `max(point.t)`. |
| L-06 | Ring field | `PointLayout.XYZ_I_R` carries ring as `uint16`. |

##### Semantics (5 checks)

| ID | Check | Description |
|---|---|---|
| S-01 | Size convention | Normative: `size[0]` = width (X), `size[1]` = height (Z), `size[2]` = depth (Y). nuScenes `(w,l,h)` -> `(w,h,l)` mapping documented. |
| S-02 | Attributes | `Detection3D.attributes` as `sequence<MetaKV, 8>` with `has_attributes` guard. |
| S-03 | Visibility | `Detection3D.visibility` float [0..1] with `has_visibility` guard. |
| S-04 | Evidence counts | `num_lidar_pts` + `num_radar_pts` with `has_num_pts` guard. |
| S-05 | Quaternion reorder | §2 table covers annotation quaternion conversion. |

##### Common / Core (5 checks)

| ID | Check | Description |
|---|---|---|
| C-01 | Quaternion table | §2 convention table covering GeoPose, ROS 2, nuScenes, Eigen, Unity, Unreal, OpenXR, glTF. |
| C-02 | FQN guidance | `FrameRef { uuid, fqn }` semantics documented; UUID is authoritative. |
| C-03 | Local-frame coverage | §3.3.4 covers local-only deployments. |
| C-04 | has_* pattern consistency | All new optional fields use the `has_*` guard pattern uniformly. |
| C-05 | Sequence bounds | Standard bounds table: SZ_MEDIUM (2048), SZ_SMALL (256), SZ_XL (32768), SZ_LARGE (8192). |

#### Results

All 27 nuScenes checks pass.

| Modality | Checks | Pass | Remaining Gaps |
|---|---|---|---|
| Radar (detections) | 6 | 6 | 0 |
| Vision | 5 | 5 | 0 |
| Lidar | 6 | 6 | 0 |
| Semantics | 5 | 5 | 0 |
| Common / Core | 5 | 5 | 0 |
| **Total** | **27** | **27** | **0** |

---

### **I.2 DeepSense 6G Conformance**

#### Reference Dataset

**DeepSense 6G** (Arizona State University, Wireless Intelligence Lab) is a large-scale multi-modal sensing and communication dataset containing:

| Dimension | Value |
|---|---|
| Scenarios | 40+ across 12+ locations |
| Snapshots | 1.08 M+ synchronized samples |
| FMCW Radar | 76–81 GHz, 3 Tx × 4 Rx, complex I/Q tensor [4×256×128], 10 Hz |
| 3D Lidar | Ouster OS1-32, 32×1024, 120 m range, 865 nm, 10–20 Hz |
| Camera | ZED2 stereo (960×540) + Insta360 ONE X2 360° (5.7K) |
| GPS-RTK | 10 Hz, ≤1 cm accuracy (RTK fix), DOP + satellite metadata |
| IMU | 6-axis, 100 Hz |
| mmWave Comm | 60 GHz phased array, 64-beam codebook, 90° FoV, 10 Hz |
| Deployment types | V2I, V2V (4× arrays/vehicle), ISAC indoor, drone |

The dataset was chosen because it stresses signal-level data (raw FMCW radar cubes consumed directly by ML pipelines), 360° camera rigs, and ISAC modalities (beam power vectors, blockage state) absent from perception-focused datasets.

#### Checks Performed (41)

##### Radar — Tensor Path (8 checks)

| ID | Check | Description |
|---|---|---|
| DT-01 | Tensor meta struct | `RadTensorMeta` exists with `axes`, `voxel_type`, `layout`, `physical_meaning`. |
| DT-02 | Complex sample type | `SampleType.CF32` covers complex I/Q data. |
| DT-03 | Channel axis | `RadTensorLayout.CH_FAST_SLOW` maps raw FMCW [Rx, samples, chirps]. |
| DT-04 | MIMO antenna config | `num_tx`, `num_rx`, `num_virtual_channels` with `has_antenna_config` guard. |
| DT-05 | Waveform params | `bandwidth_hz`, `center_freq_hz`, `samples_per_chirp`, `chirps_per_frame` with guard. |
| DT-06 | Frame blob transport | `RadTensorFrame.hdr.blobs[]` carries the raw cube; size computable from axes × sample size. |
| DT-07 | Sensor type | `RadSensorType` covers FMCW radar as MEDIUM_RANGE or IMAGING_4D. |
| DT-08 | StreamMeta extrinsics | `T_bus_sensor` (PoseSE3) + `nominal_rate_hz` for hand-eye calibration and 10 Hz cadence. |

##### Vision (7 checks)

| ID | Check | Description |
|---|---|---|
| DV-01 | Standard camera | `PixFormat.RGB8` + `CamIntrinsics.width`/`height` cover ZED2 at 960×540. |
| DV-02 | Camera extrinsics | `VisionMeta.base` → `StreamMeta.T_bus_sensor` for hand-eye calibration. |
| DV-03 | Camera model | `CamModel.PINHOLE` for ZED2 pre-rectified output. |
| DV-04 | Frame rate | `StreamMeta.nominal_rate_hz` = 10 (downsampled from 30 Hz). |
| DV-05 | 360° rig roles | `RigRole.PANORAMIC` and `EQUIRECTANGULAR` for Insta360 ONE X2 in V2V scenarios. |
| DV-06 | Keyframe flag | `VisionFrame.is_key_frame` boolean. |
| DV-07 | Compression codec | `Codec` enum covers JPEG/H264/H265/AV1. |

##### Lidar (7 checks)

| ID | Check | Description |
|---|---|---|
| DL-01 | Lidar type | `LidarType.MULTI_BEAM_3D` for Ouster OS1-32 (spinning, 32 rings). |
| DL-02 | Ring count + FOV | `LidarMeta.n_rings`, `has_horiz_fov`, `has_vert_fov` with guards. |
| DL-03 | Range limits | `has_range_limits` + `max_range_m` = 120 m. |
| DL-04 | Point layout | `PointLayout.XYZ_I_R` for x, y, z, intensity, ring. |
| DL-05 | Cloud encoding | `CloudEncoding.BIN_INTERLEAVED` for raw binary transport. |
| DL-06 | Sensor wavelength | `LidarMeta.wavelength_nm` with `has_wavelength` guard (865 nm). |
| DL-07 | Frame rate | `StreamMeta.nominal_rate_hz` covers 10–20 Hz. |

##### IMU (4 checks)

| ID | Check | Description |
|---|---|---|
| DI-01 | 6-axis sample | `ImuSample` with accel (Vec3, m/s²) + gyro (Vec3, rad/s). |
| DI-02 | Noise densities | `ImuInfo.accel_noise_density` + `gyro_noise_density` + random walk params. |
| DI-03 | Frame reference | `ImuInfo.frame_ref` for sensor-to-bus mounting. |
| DI-04 | Timestamp + sequence | `ImuSample.stamp` + `.seq` for 100 Hz temporal ordering. |

##### GPS (6 checks)

| ID | Check | Description |
|---|---|---|
| DG-01 | Position | `GeoPose.lat_deg`/`lon_deg`/`alt_m` for GPS-RTK coordinates. |
| DG-02 | Orientation | `GeoPose.q` (QuaternionXYZW) for heading-derived orientation. |
| DG-03 | Timestamp | `GeoPose.stamp` for 10 Hz GPS samples. |
| DG-04 | Covariance | `GeoPose.cov` for positional uncertainty (RTK ≤1 cm). |
| DG-05 | GNSS quality | `NavSatStatus` provides DOP, fix type, and satellite count with `has_dop` guard. |
| DG-06 | Speed over ground | `NavSatStatus.speed_mps` + `course_deg` with `has_velocity` guard. |

##### mmWave Beam (8 checks)

| ID | Check | Description |
|---|---|---|
| DB-01 | Beam power vector | `RfBeamFrame.power` (sequence<float,1024>) carries per-beam received power. 64 entries for DeepSense exhaustive sweep. Provisional `rf_beam` profile (K-B1). |
| DB-02 | Codebook metadata | `RfBeamMeta.n_beams` (64), `n_elements` (16), `center_freq_ghz` (60.0), `fov_az_deg` (90), `codebook_type`. |
| DB-03 | Optimal beam index | `RfBeamFrame.best_beam_idx` (uint16) with `has_best_beam` guard. Ground-truth label: beam maximizing SNR. |
| DB-04 | Blockage status | `RfBeamFrame.is_blocked` (boolean) + `blockage_confidence` (float 0..1) with `has_blockage_state` guard. |
| DB-05 | Multi-array set | `RfBeamArraySet.arrays` (sequence<RfBeamFrame,8>) batches per-array frames. `overall_best_array_idx` + `overall_best_beam_idx` for cross-array best beam. Covers V2V 4-array rig. |
| DB-06 | Sparse sweep indices | `RfBeamFrame.beam_indices` maps `power[i]` to codebook position for PARTIAL/TRACKING sweeps. `BeamSweepType` enum: EXHAUSTIVE, HIERARCHICAL, TRACKING, PARTIAL. |
| DB-07 | Power unit convention | `RfBeamMeta.power_unit` (PowerUnit enum: DBM, LINEAR_MW, RSRP) declares units for `RfBeamFrame.power`. |
| DB-08 | Stream linkage | `RfBeamFrame.stream_id` matches `RfBeamMeta.stream_id` for meta/frame correlation. |

*Note: All mmWave Beam checks validated against the provisional `sensing.rf_beam` profile (Appendix E). Types are subject to breaking changes.*

##### Semantics (4 checks)

| ID | Check | Description |
|---|---|---|
| DS-01 | 2D bounding boxes | `Detection2D.bbox` + `class_id` covers 8 DeepSense object classes. |
| DS-02 | Sequence index | `FrameHeader.frame_seq` for sample ordering. |
| DS-03 | Class ID | `Detection2D.class_id` (string) maps all DeepSense class labels. |
| DS-04 | Beam/blockage labels | `RfBeamFrame.best_beam_idx` and `.is_blocked`/`.blockage_confidence` carry ISAC-specific ground-truth labels. Covered by provisional `rf_beam` profile. |

#### Results

All 44 DeepSense 6G checks pass. GNSS diagnostics are covered by `NavSatStatus`, and mmWave Beam checks pass against the provisional `rf_beam` profile (Appendix E).

| Modality | Checks | Pass | Gap | Missing | Notes |
|---|---|---|---|---|---|
| Radar (tensor) | 8 | 8 | 0 | 0 | — |
| Vision | 7 | 7 | 0 | 0 | Includes 360° rig roles |
| Lidar | 7 | 7 | 0 | 0 | Includes sensor wavelength |
| IMU | 4 | 4 | 0 | 0 | — |
| GPS | 6 | 6 | 0 | 0 | NavSatStatus covers GNSS diagnostics |
| mmWave Beam | 8 | 8 | 0 | 0 | Provisional rf_beam profile (K-B1) |
| Semantics | 4 | 4 | 0 | 0 | Beam labels via rf_beam |
| **Total** | **44** | **44** | **0** | **0** | **100% coverage** |

#### Deferred Items

DeepSense 6G conformance has no remaining schema gaps. Future ISAC extensions (e.g., CSI/CIR profiles) remain under discussion; see Appendix K for the maturity promotion criteria.

---

### **I.3 S3E Conformance (Multi-Robot Collaborative SLAM)**

#### Reference Dataset

**S3E** (Sun Yat-sen University / HKUST) is a multi-robot multimodal dataset for collaborative SLAM containing:

| Dimension | Value |
|---|---|
| Robots | 3 UGVs (Alpha, Blob, Carol) operating simultaneously |
| LiDAR | 1 × 16-beam 3D scanner (Velodyne VLP-16) per robot, 10 Hz |
| Stereo cameras | 2 × high-resolution color cameras per robot |
| IMU | 9-axis, 100–200 Hz per robot |
| UWB | Inter-robot Ultra-Wideband ranging (pairwise distances at ~10 Hz) |
| GNSS | Dual-antenna RTK receiver per robot (ground truth) |
| Environments | 13 outdoor + 5 indoor sequences |
| Trajectory paradigms | 4 collaborative patterns (concentric circles, intersecting circles, intersection curve, rays) |
| Format | ROS 2 bag files; ground truth as TUM-format pose files |

The dataset was chosen because it is the first C-SLAM dataset to include UWB inter-robot ranging, exercises multi-agent map building with inter-robot loop closures, and represents a scenario class (heterogeneous multi-robot coordination) where SpatialDDS's Mapping extension, Discovery profile, and multi-source pose graph types provide capabilities absent from ROS 2's `nav_msgs` and `sensor_msgs`.

#### Checks Performed (38)

##### Per-Robot Sensing — LiDAR (5 checks)

| ID | Check | Description |
|---|---|---|
| SL-01 | LiDAR meta | `LidarMeta` with `sensor_type`, `rate_hz`, `point_layout` covers Velodyne VLP-16. |
| SL-02 | Point layout | `PointLayout.XYZ_I_R_T` carries x, y, z, intensity, ring, time — matches Velodyne binary format. |
| SL-03 | Per-robot topic isolation | Topic template `spatialdds/<scene>/lidar/<sensor_id>/frame/v1` with per-robot `sensor_id` (e.g., `alpha/vlp16`). |
| SL-04 | CloudEncoding | `BIN_INTERLEAVED` covers raw binary point cloud blobs. |
| SL-05 | RigRole | `RigRole.TOP` covers single roof-mounted LiDAR. |

##### Per-Robot Sensing — Vision (4 checks)

| ID | Check | Description |
|---|---|---|
| SV-01 | Stereo pair | Two `VisionFrame` streams per robot with `RigRole.LEFT` / `RigRole.RIGHT`. |
| SV-02 | Camera intrinsics | `CameraMeta` with `fx`, `fy`, `cx`, `cy`, `dist_model`, `dist_coeffs` covers calibrated stereo cameras. |
| SV-03 | Per-robot namespacing | Topic `spatialdds/<scene>/vision/<sensor_id>/frame/v1` isolates per-robot camera streams. |
| SV-04 | Timestamp sync | `VisionFrame.stamp` synchronized to common timebase via hardware PPS trigger. |

##### Per-Robot Sensing — IMU (3 checks)

| ID | Check | Description |
|---|---|---|
| SI-01 | 9-axis sample | `ImuSample` with accel (Vec3, m/s²) + gyro (Vec3, rad/s) covers 6-axis; `MagSample` covers magnetometer. |
| SI-02 | High-rate ordering | `ImuSample.seq` monotonic counter handles 100–200 Hz temporal ordering. |
| SI-03 | Extrinsic calibration | Sensor-to-body transform publishable as `FrameTransform` (LiDAR-IMU, camera-IMU extrinsics). |

##### Per-Robot Sensing — GNSS/RTK (3 checks)

| ID | Check | Description |
|---|---|---|
| SG-01 | RTK fix type | `GnssFixType.RTK_FIXED` covers dual-antenna RTK ground truth receiver. |
| SG-02 | GeoPose output | `GeoPose` with `lat_deg`, `lon_deg`, `alt_m`, quaternion covers RTK-derived global pose. |
| SG-03 | NavSatStatus | `NavSatStatus` with `fix_type`, `num_satellites`, `hdop`, `vdop` covers receiver diagnostics. |

##### Inter-Robot Ranging — UWB (4 checks)

| ID | Check | Description |
|---|---|---|
| SU-01 | Range edge type | `mapping::EdgeType.RANGE` explicitly models UWB range-only constraint (scalar distance, no orientation). |
| SU-02 | Range fields | `mapping::Edge.range_m` + `range_std_m` carry measured distance and uncertainty. |
| SU-03 | Cross-map provenance | `has_from_map_id` / `has_to_map_id` populated on RANGE edges because UWB connects nodes in different robots' maps. |
| SU-04 | Range-assisted alignment | `AlignmentMethod.RANGE_COARSE` covers initial inter-map alignment derived solely from UWB distances. |

##### Core Pose Graph (5 checks)

| ID | Check | Description |
|---|---|---|
| SC-01 | Per-robot nodes | `core::Node` with `map_id` per robot (e.g., `alpha-map`, `blob-map`, `carol-map`), `@key node_id` unique per keyframe. |
| SC-02 | Odometry edges | `core::Edge` with `type = ODOM` connects sequential keyframes within each robot's map. |
| SC-03 | Intra-robot loop closures | `core::Edge` with `type = LOOP` for within-map loop closures (e.g., concentric circle paradigm). |
| SC-04 | Versioning | `Node.seq` monotonic per source; `Node.graph_epoch` increments after global re-optimization. |
| SC-05 | Multi-source coexistence | Three simultaneous `source_id` values on `core::Node` and `core::Edge` topics — one per robot. |

##### Mapping Extension — Multi-Agent (8 checks)

| ID | Check | Description |
|---|---|---|
| SM-01 | Map lifecycle | `MapMeta` per robot with `state` progressing: BUILDING → OPTIMIZING → STABLE. |
| SM-02 | Map kind | `MapMeta.kind = POSE_GRAPH` for each robot's SLAM output. |
| SM-03 | Inter-robot loop closures | `mapping::Edge` with `type = INTER_MAP` and `has_from_map_id` / `has_to_map_id` populated. |
| SM-04 | MapAlignment | `MapAlignment` with `T_from_to` expressing the inter-map transform after cross-robot alignment. |
| SM-05 | Alignment revision | `MapAlignment.revision` increments as more inter-robot edges accumulate and the alignment refines. |
| SM-06 | Evidence trail | `MapAlignment.evidence_edge_ids[]` references the specific cross-map edges supporting the alignment. |
| SM-07 | MapEvent notifications | `MapEvent` with `MAP_ALIGNED` event when two robots' maps are first linked. |
| SM-08 | Concurrent map builds | Three `MapMeta` samples simultaneously active (keyed by `map_id`), demonstrating multi-map lifecycle. |

##### Discovery & Coordination (3 checks)

| ID | Check | Description |
|---|---|---|
| SD-01 | Service announcement | Each robot publishes `Announce` with `ServiceKind.SLAM` and sensor capabilities in `topics[]`. |
| SD-02 | Spatial coverage | `Announce.coverage` (Aabb3 or geo-bounds) advertises each robot's operational area. |
| SD-03 | Multi-frame NodeGeo | After inter-map alignment, `NodeGeo.poses[]` carries a node's pose in multiple robots' map frames simultaneously (FramedPose array). |

##### Cross-cutting (3 checks)

| ID | Check | Description |
|---|---|---|
| SX-01 | Quaternion convention | §2 table covers ROS 2 (x,y,z,w) to SpatialDDS (x,y,z,w) identity mapping for S3E's ROS 2 bag source. |
| SX-02 | Coordinate frame convention | Right-handed; S3E uses right-hand rule per documentation. |
| SX-03 | Time synchronization | Hardware PPS-synchronized timestamps map directly to `Time { sec, nanosec }`. |

#### Results

All 38 S3E checks pass.

| Modality | Checks | Pass | Remaining Gaps |
|---|---|---|---|
| LiDAR | 5 | 5 | 0 |
| Vision | 4 | 4 | 0 |
| IMU | 3 | 3 | 0 |
| GNSS/RTK | 3 | 3 | 0 |
| UWB (inter-robot range) | 4 | 4 | 0 |
| Core Pose Graph | 5 | 5 | 0 |
| Mapping (multi-agent) | 8 | 8 | 0 |
| Discovery & Coordination | 3 | 3 | 0 |
| Cross-cutting | 3 | 3 | 0 |
| **Total** | **38** | **38** | **0** |

#### S3E Scenario Narrative (Informative)

The S3E "teaching building" outdoor sequence illustrates the full multi-agent lifecycle:

1. **Bootstrap.** Three robots (Alpha, Blob, Carol) power on and each publishes an `Announce` with `ServiceKind.SLAM`, their sensor capabilities, and an initial coverage bounding box. Each begins publishing `core::Node` and `core::Edge` (ODOM) on the pose graph topics with distinct `source_id` and `map_id` values.

2. **Independent mapping.** Each robot runs visual-inertial-lidar SLAM independently. `MapMeta` per robot shows `state = BUILDING`. Keyframes stream as `core::Node`; odometry constraints as `core::Edge` (ODOM); intra-robot loop closures as `core::Edge` (LOOP). `ImuSample`, `VisionFrame`, and `LidarFrame` are published on per-robot sensor topics.

3. **UWB ranging begins.** As robots come within UWB range (~50 m), pairwise distance measurements are published as `mapping::Edge` with `type = RANGE`, `range_m` carrying the measured distance, `has_from_map_id` / `has_to_map_id` identifying which robots' maps the linked nodes belong to.

4. **Inter-robot loop closure.** When Alpha and Blob's LiDAR scans overlap, a cross-robot loop closure is detected. This is published as `mapping::Edge` with `type = INTER_MAP`, `match_score` carrying the ICP fitness, and `from_map_id = "alpha-map"`, `to_map_id = "blob-map"`.

5. **Map alignment.** A `MapAlignment` is published linking Alpha's and Blob's maps, with `method = LIDAR_ICP` (or `MULTI_METHOD` if UWB ranges were fused), `T_from_to` carrying the inter-map transform, and `evidence_edge_ids[]` referencing the supporting cross-map edges. `MapEvent` with `MAP_ALIGNED` notifies all subscribers.

6. **Multi-frame localization.** Once the alignment exists, a geo-referencing service can publish `NodeGeo` with `poses[]` containing FramedPoses in both Alpha's and Blob's map frames simultaneously. Consumers (e.g., a planning service) can pick the frame they need.

7. **Graph optimization.** After sufficient inter-robot constraints accumulate, a global optimizer runs. All robots' `MapMeta.state` transitions to `OPTIMIZING`, then `STABLE`. `graph_epoch` increments on all nodes and edges. `MapAlignment.revision` increments. Consumers watching `graph_epoch` know to re-fetch the entire graph.

This end-to-end scenario is precisely what ROS 2's `nav_msgs` and `sensor_msgs` cannot express: there is no ROS 2 standard for map lifecycle, inter-map alignment, range-only constraints, or multi-agent discovery with spatial coverage.

---

### **I.4 ScanNet Conformance (Indoor Scene Understanding)**

#### Reference Dataset

**ScanNet** (TU Munich / Princeton) is an RGB-D video dataset of indoor scenes containing:

| Dimension | Value |
|---|---|
| Scenes | 1,513 (707 unique spaces, multiple rescans) |
| RGB-D sensor | Structure.io depth + iPad color camera |
| Depth format | 16-bit unsigned integer, millimeters, 640×480 @ 30 Hz |
| Color format | JPEG-compressed RGB, 1296×968 @ 30 Hz |
| Camera poses | Per-frame 4×4 camera-to-world extrinsics via BundleFusion |
| IMU | Embedded IMU data in `.sens` stream |
| Surface reconstruction | Dense triangle mesh (PLY) via BundleFusion |
| Semantic annotations | Instance-level labels (NYU40 label set, 40 classes) |
| Instance annotations | Per-vertex segment IDs + aggregated object instances |
| Scene types | 20 categories (bathroom, bedroom, kitchen, living room, office, etc.) |
| Axis alignment | Per-scene 4×4 gravity-alignment matrix |
| Coordinate convention | Right-handed; +Z up in aligned frame |

ScanNet was chosen because it is the definitive indoor RGB-D scene understanding benchmark, exercises depth sensing absent from all three prior conformance datasets, and provides room-level semantic structure that naturally maps to the Spatial Events extension — the only SpatialDDS extension not yet tested by conformance.

#### Checks Performed (35)

##### RGB-D Sensing — Color (4 checks)

| ID | Check | Description |
|---|---|---|
| NC-01 | Color meta | `VisionMeta` with `pix = RGB8`, `codec = JPEG`, `CamIntrinsics` (fx, fy, cx, cy at 1296×968). |
| NC-02 | Color frame | `VisionFrame` per RGB image with `frame_seq`, `hdr.stamp`, blob reference to JPEG payload. |
| NC-03 | Per-scene stream isolation | Topic `spatialdds/<scene_id>/vision/<stream_id>/frame/v1` with unique `stream_id` per scan. |
| NC-04 | Rig linkage | `VisionMeta.rig_id` shared between color and depth streams for spatial association. |

##### RGB-D Sensing — Depth (5 checks)

| ID | Check | Description |
|---|---|---|
| ND-01 | Depth meta | `VisionMeta` with `pix = DEPTH16`, `codec = NONE` (raw 16-bit), `CamIntrinsics` for depth camera. |
| ND-02 | Depth pixel format | `PixFormat.DEPTH16` explicitly identifies 16-bit millimeter depth. **Requires SN-1.** |
| ND-03 | Depth frame | `VisionFrame` per depth image with `frame_seq` matching co-located color frame. |
| ND-04 | Invalid depth convention | Zero-valued pixels denote no measurement, consistent with `DEPTH16` normative note. |
| ND-05 | Depth unit | Default millimeter unit; no `depth_unit` attribute required for ScanNet's Structure.io sensor. |

##### IMU (2 checks)

| ID | Check | Description |
|---|---|---|
| NI-01 | IMU sample | `ImuSample` with accel (Vec3, m/s²) + gyro (Vec3, rad/s) covers 6-axis IMU embedded in `.sens` stream. |
| NI-02 | Temporal ordering | `ImuSample.seq` provides monotonic ordering within the scan. |

##### Camera Pose & Frames (4 checks)

| ID | Check | Description |
|---|---|---|
| NP-01 | Per-frame pose | Camera-to-world 4×4 matrix maps to `FrameHeader.sensor_pose` (PoseSE3: translation + quaternion). |
| NP-02 | Axis-alignment transform | Per-scene gravity-alignment matrix published as `FrameTransform` from sensor frame to aligned frame. |
| NP-03 | Frame hierarchy | Aligned frame FQN follows §2.2 pattern: `<scene_id>/aligned`. |
| NP-04 | Quaternion convention | ScanNet uses 4×4 rotation matrices; decomposition to (x,y,z,w) quaternion per §2 convention table. |

##### Mesh Reconstruction (4 checks)

| ID | Check | Description |
|---|---|---|
| NM-01 | Map kind | `MapMeta` with `kind = MESH` for BundleFusion surface reconstruction. |
| NM-02 | Map lifecycle | `MapMeta.state` = STABLE for completed reconstructions (offline dataset; no BUILDING phase observed). |
| NM-03 | Mesh payload | `BlobRef` referencing PLY mesh file. SpatialDDS carries mesh references, not inline mesh data. |
| NM-04 | Vertex count metadata | `MapMeta.attributes` carries vertex/face count as MetaKV for consumers to assess mesh complexity. |

##### 3D Instance Segmentation — Semantics (6 checks)

| ID | Check | Description |
|---|---|---|
| NS-01 | 3D detection | `Detection3D` per annotated object instance, with `class_id` from NYU40 label set (e.g., "chair", "table", "door"). |
| NS-02 | Instance ID | `Detection3D.det_id` unique per object instance within a scene (maps from ScanNet's `objectId`). |
| NS-03 | Oriented bounding box | `Detection3D.center` + `size` + `q` cover ScanNet's axis-aligned bounding boxes (identity quaternion in aligned frame). |
| NS-04 | Track ID | `Detection3D.track_id` groups the same physical object across multiple rescans of the same space. |
| NS-05 | Visibility | `Detection3D.visibility` (0–1) maps from ScanNet annotation coverage ratio. |
| NS-06 | Class vocabulary | `class_id` as free-form string covers all 40 NYU40 categories without a closed enum — consistent with SpatialDDS's ontology-agnostic design. |

##### Spatial Events — Indoor Zones (6 checks)

| ID | Check | Description |
|---|---|---|
| NZ-01 | Room as zone | `SpatialZone` per ScanNet scene, with `zone_id` = scene ID, `name` = human-readable scene name. |
| NZ-02 | Zone kind | `ZoneKind.MONITORING` for general-purpose room observation (no access restriction implied). |
| NZ-03 | Zone bounds | `SpatialZone.bounds` (Aabb3) enclosing the room extent, derived from mesh bounding box in aligned frame. |
| NZ-04 | Scene type as attribute | ScanNet `sceneType` (bathroom, bedroom, kitchen, etc.) carried as `MetaKV` in `SpatialZone.attributes` with `namespace = "scene_type"`, `json = {"type": "kitchen"}`. |
| NZ-05 | Class filter | `SpatialZone.class_filter` populated with object classes of interest (e.g., `["person", "chair", "table"]`) for selective event triggering. |
| NZ-06 | Zone frame | `SpatialZone.frame_ref` references the gravity-aligned frame established by the axis-alignment transform (NP-02). |

##### Spatial Events — Object Events (4 checks)

| ID | Check | Description |
|---|---|---|
| NE-01 | Zone entry | `SpatialEvent` with `event_type = ZONE_ENTRY` when a Detection3D instance is first observed within a SpatialZone's bounds. |
| NE-02 | Trigger linkage | `SpatialEvent.trigger_det_id` references the triggering `Detection3D.det_id`; `trigger_class_id` carries the NYU40 label. |
| NE-03 | Zone state | `ZoneState` with `zone_occupancy` count reflecting the number of annotated object instances within the room. |
| NE-04 | Class counts | `ZoneState.class_counts` (sequence of MetaKV) carries per-class occupancy (e.g., `{"count": 4}` for class "chair"). |

#### Results

All 35 ScanNet checks pass.

| Modality | Checks | Pass | Remaining Gaps |
|---|---|---|---|
| Color (RGB) | 4 | 4 | 0 |
| Depth (RGBD) | 5 | 5 | 0 |
| IMU | 2 | 2 | 0 |
| Camera Pose & Frames | 4 | 4 | 0 |
| Mesh Reconstruction | 4 | 4 | 0 |
| 3D Instance Segmentation | 6 | 6 | 0 |
| Spatial Events — Zones | 6 | 6 | 0 |
| Spatial Events — Object Events | 4 | 4 | 0 |
| **Total** | **35** | **35** | **0** |

#### ScanNet Scenario Narrative (Informative)

The ScanNet "apartment" scan sequence illustrates how SpatialDDS types map to a complete indoor scene understanding pipeline:

1. **Scan ingestion.** An operator walks through a kitchen with an iPad running the ScanNet capture app. Color frames are published as `VisionFrame` (pix=RGB8, codec=JPEG) and depth frames as `VisionFrame` (pix=DEPTH16, codec=NONE) on paired streams linked by `rig_id`. `ImuSample` streams concurrently from the embedded IMU.

2. **Pose estimation.** BundleFusion produces per-frame camera poses, published as `FrameHeader.sensor_pose` on each VisionFrame. The per-scene axis-alignment matrix is published as a `FrameTransform` from the sensor coordinate system to a gravity-aligned room frame.

3. **Mesh reconstruction.** The completed surface mesh is registered as `MapMeta` with `kind = MESH`, `state = STABLE`. The PLY file is referenced via `BlobRef`. Vertex/face counts are carried in `MapMeta.attributes`.

4. **Zone definition.** The kitchen is defined as a `SpatialZone` with `kind = MONITORING`, `bounds` enclosing the room extent, and `attributes` carrying `scene_type = "kitchen"`. The `frame_ref` points to the gravity-aligned frame.

5. **3D instance detection.** Crowdsourced annotations produce `Detection3D` instances for each labeled object: chairs with `class_id = "chair"`, tables with `class_id = "table"`, a refrigerator with `class_id = "refrigerator"` — each with an oriented bounding box in the aligned frame.

6. **Spatial events.** A zone monitoring service evaluates which Detection3D instances fall within the kitchen SpatialZone's bounds and publishes `SpatialEvent` (ZONE_ENTRY) for each. `ZoneState` is published periodically with `zone_occupancy = 12` (total instances) and `class_counts` listing per-class breakdowns.

This pipeline exercises the Spatial Events extension end-to-end — from zone definition through detection to event generation — a capability path untested by nuScenes (no zones), DeepSense 6G (no zones), or S3E (no zones or semantics).

#### Deferred Items

- **Per-vertex semantic labels.** ScanNet provides per-vertex class labels on the reconstructed mesh. SpatialDDS has no per-vertex label type; the labeled mesh PLY is carried as a `BlobRef`. A future per-vertex or per-point semantic annotation type could make this data first-class.
- **CAD model alignment.** ScanNet aligns ShapeNet CAD models to detected objects. The ShapeNet model ID can be carried in `Detection3D.attributes` as a MetaKV, but there is no first-class CAD reference type.
- **2D projected labels.** ScanNet provides per-frame 2D semantic/instance label images. These can be published as `VisionFrame` with a label-specific `stream_id` and `pix = RAW16` (16-bit label IDs), but a dedicated label pixel format is not defined.

---

### **Reproducing the Tests**

The nuScenes and DeepSense 6G conformance harnesses are self-contained Python 3 scripts with no external dependencies.

**nuScenes harness** (`scripts/nuscenes_harness_v2.py`):

```bash
python3 scripts/nuscenes_harness_v2.py
```

Mirrors the SpatialDDS 1.5 IDL structures as Python dictionaries and checks them against the nuScenes schema. Produces a plain-text report and a JSON results file.

**DeepSense 6G harness** (`scripts/deepsense6g_harness_v3.py`):

```bash
python3 scripts/deepsense6g_harness_v3.py
```

Validates 44 checks across 7 modalities (radar tensor, vision, lidar, IMU, GPS, mmWave beam, semantics). The mmWave beam checks validate against the provisional `rf_beam` profile (Appendix E). Produces a plain-text report and a JSON results file.

**S3E conformance**: The 38 S3E checks documented in §I.3 were performed as a manual schema-vs-schema analysis. A scripted harness (`scripts/s3e_harness_v1.py`) following the same pattern as the nuScenes and DeepSense 6G scripts is planned for a future revision.

**ScanNet conformance**: The 35 ScanNet checks documented in §I.4 were performed as a manual schema-vs-schema analysis. A scripted harness (`scripts/scannet_harness_v1.py`) is planned for a future revision.

No harness requires network access, a DDS runtime, or a dataset download. Implementers are encouraged to adapt the harnesses for additional reference datasets (e.g., Waymo Open, KITTI, Argoverse 2, RADIal, SubT-MRS, ScanNet) to validate coverage for sensor configurations or multi-agent scenarios not already covered.

### **Limitations**

This testing validates schema expressiveness -- whether every dataset field has a lossless SpatialDDS mapping. It does not validate:

- **Wire interoperability** -- actual DDS serialization/deserialization round-trips.
- **Performance** -- throughput, latency, or memory footprint under real sensor loads.
- **Semantic correctness** -- whether a particular producer's mapping preserves the intended meaning of each field.
- **Multi-dataset coverage** -- datasets with different sensor configurations (e.g., solid-state lidar, event cameras, ultrasonic sensors) or deployment patterns (e.g., multi-floor hierarchical spaces, aerial-ground cooperation, dense pedestrian tracking) may surface additional gaps. S3E covers three-robot outdoor coordination; ScanNet covers single-room indoor scenes. Larger fleet sizes, degraded-communication environments, multi-floor buildings, and heterogeneous robot types (ground + aerial) remain untested.

These areas are appropriate targets for future conformance work.
