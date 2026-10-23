## **Appendix I: Dataset Conformance Testing (Informative)**

*This appendix documents systematic conformance testing performed against five public reference datasets. Each validation was run against the SpatialDDS version noted in its section: nuScenes, DeepSense 6G, S3E, and ScanNet against **1.5**, and LaMAR against the **1.6-era** profiles. The results validated schema expressiveness and directly informed several normative additions carried forward into 1.8. These are schema-expressiveness analyses, not wire-interoperability tests, and the coverage figures below state their exceptions rather than claiming an unqualified 100%. A scripted re-validation against the 1.8 release — with each harness reading the IDL rather than mirroring it, so the record cannot drift silently — is planned (§6 Future Directions).*

### **Scope and Limitations**

The conformance tests in this appendix validate **schema expressiveness** — whether every field in a reference dataset has a lossless mapping to a SpatialDDS type. They are performed as static schema-vs-schema analyses and do NOT validate:

- **Wire-level interoperability** between DDS implementations (e.g., CycloneDDS ↔ Fast DDS ↔ RTI Connext).
- **Runtime correctness** of publish/subscribe delivery, QoS enforcement, or temporal ordering.
- **End-to-end data fidelity** of encode → transmit → decode round-trips.

Wire-level interop tests across at least two DDS vendors are planned for a future revision (see §6 Future Directions). Such a suite SHOULD, per QoS profile (§3.3.3), verify endpoint matching between two independently configured participants — a reader and a writer that each set the profile's normative policies from scratch. Deadline is request/offered and matches silently: a reader requesting a Deadline will not match a writer that offers none, so a per-profile matching check is the class of failure this catches.

Pass rates reported below reflect expressiveness coverage. A "pass" means the dataset field has a complete, lossless mapping to SpatialDDS types. A "gap" means no suitable type exists and an extension is needed. Deferred items are fields that can be carried (e.g., via `MetaKV`) but lack first-class typed support.

### **Motivation**

Sensor-data specifications risk becoming disconnected from real-world workloads if they are designed in isolation. To guard against this, the SpatialDDS profiles were validated — at the versions noted above — against five complementary datasets that together exercise the full signal-to-semantics pipeline and multi-agent coordination:

| Dataset | Focus | Modalities Stressed |
|---|---|---|
| **nuScenes** (Motional / nuTonomy) | Perception → semantics | Camera (6×), lidar, radar detections (5×), 3D annotations, coordinate conventions |
| **DeepSense 6G** (ASU Wireless Intelligence Lab) | Signal → perception | Raw radar I/Q tensors, 360° cameras, lidar, IMU, GPS-RTK, mmWave beam vectors |
| **S3E** (Sun Yat-sen University / HKUST) | Multi-agent coordination | 3 UGVs × (lidar, stereo, IMU), UWB inter-robot ranging, RTK-GNSS, collaborative SLAM |
| **ScanNet** (TU Munich / Princeton) | Indoor scene understanding | RGB-D depth frames, 3D surface mesh, instance segmentation (NYU40), room-level zones, 20 scene types |
| **LaMAR** (CVG ETH Zürich / Microsoft) | Multi-device AR localization & mapping | HoloLens 4-camera rig (GRAY8 + ToF depth + IR + IMU), iPad LiDAR, NavVis scanner mesh + 1080p panoramic cameras, WiFi/BT radio scans, year-long multi-session alignment, GeoAnchor reference frames |

nuScenes was chosen because it stresses sensor diversity, per-detection radar fields rarely found in other corpora (compensated velocity, dynamic property, RCS), and rich annotation metadata (visibility, attributes, evidence counts). DeepSense 6G was chosen because it stresses signal-level data (raw FMCW radar cubes, phased-array beam power vectors) and ISAC modalities absent from traditional perception datasets. S3E was chosen because it is the first collaborative SLAM dataset with UWB inter-robot ranging and exercises the multi-agent capabilities — map lifecycle, inter-map alignment, range-only constraints, and fleet discovery — that differentiate SpatialDDS from single-vehicle frameworks such as ROS 2. ScanNet was chosen because it is the definitive indoor RGB-D scene understanding benchmark, uniquely exercises depth sensing (`DEPTH16`) and the Spatial Events extension (room zones, object-in-room events, per-class occupancy counts), and validates the semantics profile's instance segmentation types against a rich 40-class indoor vocabulary. LaMAR was chosen because it is the first conformance dataset to exercise cross-device heterogeneity (HoloLens, iPhone/iPad, and NavVis scanner sharing a common reference frame), the Anchors profile (cross-session alignment, year-long persistence, geo-anchored reference frames), the Discovery profile in a multi-device context (heterogeneous device announcements with distinct sensor capabilities), and the `sensing.radio` profile in a production AR workflow (typed WiFi/BT scans replacing ad hoc JSON, driving +4.6–17.5% recall improvement in image retrieval).

The goal was not to certify particular datasets but to answer two concrete questions: *Can every field, enum, and convention in each dataset's schema be losslessly mapped to the SpatialDDS IDL of the version under test without workarounds or out-of-band agreements?* And for multi-agent scenarios: *Can the full coordination lifecycle — from independent mapping through inter-map alignment — be expressed using the standard types?*

### **Methodology**

For each dataset, a conformance harness was constructed as a self-contained Python 3 script that:

1. **Reads the SpatialDDS IDL** as the source of type truth. The nuScenes and DeepSense 6G harnesses parse `idl/v1.8/*.idl` directly through `scripts/idl_introspect.py` (enum values, struct field lists, const modules); the few normative facts not expressible in IDL (prose conventions) remain inline flags. Because the type shapes are read from the canonical tree at run time, they cannot drift from the spec — the hand-typed 1.5 mirrors that the audit of this appendix found drifting have been removed.
2. **Mirrors the dataset schema** as synthetic data (sensor names, field lists, data shapes).
3. **Runs targeted checks**, each producing a verdict:

| Verdict | Meaning |
|---|---|
| **PASS** | Dataset field maps losslessly to an existing SpatialDDS type or enum value. |
| **GAP** | A mapping exists conceptually but the required SpatialDDS type or field does not yet exist. |
| **MISSING** | No SpatialDDS construct exists for the dataset field; a new profile is needed. |

4. **Reports a per-modality scorecard.**

Neither nuScenes nor DeepSense 6G harness requires network access, a DDS runtime, or a dataset download. Both operate as static schema-vs-schema dry runs, reproducible in any CI environment. The S3E (§I.3), ScanNet (§I.4), and LaMAR (§I.5) conformance sections were performed as manual schema analyses following the same check structure; scripted harnesses are planned for a future revision. Every section below opens with a **validation record** in a fixed format — the SpatialDDS version validated against, the date, the method (scripted harness and its commit, or manual analysis), and the verbatim pass totals.

---

### **I.1 nuScenes Conformance**

**Validation record.** Validated against SpatialDDS **1.8** (`idl/v1.8/`) · 2026-10-22 · Method: scripted — `scripts/nuscenes_harness_v2.py` reads the IDL through `scripts/idl_introspect.py` (no hand-mirror), harness at spec commit `b557ea6` · Result: **27/27 reproducible checks PASS**. C-06 (coord-convention) is a manual-only check not implemented in the script, so the documented total is 28 and the reproducible total is 27.

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

#### Checks Performed (28)

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

##### Common / Core (6 checks)

| ID | Check | Description |
|---|---|---|
| C-01 | Quaternion table | §2 convention table covering GeoPose, ROS 2, nuScenes, Eigen, Unity, Unreal, OpenXR, glTF. |
| C-02 | FQN guidance | `FrameRef { uuid, fqn }` semantics documented; UUID is authoritative. |
| C-03 | Local-frame coverage | §3.3.4 covers local-only deployments. |
| C-04 | has_* pattern consistency | All new optional fields use the `has_*` guard pattern uniformly. |
| C-05 | Sequence bounds | Standard bounds table: SZ_MEDIUM (2048), SZ_SMALL (256), SZ_XL (32768), SZ_LARGE (8192). |
| C-06 | Coord convention (manual-only) | nuScenes ego frame is ENU; per-camera calibrated_sensor frames follow the OpenCV `CV` convention (X-right, Y-down, Z-forward). `FrameRef.coord_convention` (§2.12) captures the per-frame axis convention so cross-frame chains apply the correct axis-swap. **Manual-only: not implemented in `nuscenes_harness_v2.py`, which reproduces the other 27 checks.** |

#### Results

All 28 documented nuScenes checks pass, with no gaps and no deferrals. The harness reproduces 27 of them; C-06 (coord-convention) is a manual-only check.

| Modality | Checks | Pass | Gap | Deferred | Notes |
|---|---|---|---|---|---|
| Radar (detections) | 6 | 6 | 0 | 0 | — |
| Vision | 5 | 5 | 0 | 0 | — |
| Lidar | 6 | 6 | 0 | 0 | — |
| Semantics | 5 | 5 | 0 | 0 | — |
| Common / Core | 6 | 6 | 0 | 0 | Includes C-06, which is manual-only |
| **Total** | **28** | **28** | **0** | **0** | 27 reproduced by the harness; C-06 manual-only |

Deferred items are fields that CAN be carried (typically via `MetaKV`) but lack first-class typed support. They are tracked as future profile additions, not as conformance failures.

---

### **I.2 DeepSense 6G Conformance**

**Validation record.** Validated against SpatialDDS **1.8** (`idl/v1.8/`) · 2026-10-22 · Method: scripted — `scripts/deepsense6g_harness_v3.py` reads the IDL through `scripts/idl_introspect.py` (no hand-mirror), harness at spec commit `b557ea6` · Result: **48/48 checks PASS** (the GPS modality carries 10, DG-01 through DG-10). Earlier drafts of this section cited 41 and then 44 before the four additional GPS checks (DG-07 through DG-10) were documented here.

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

#### Checks Performed (48)

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

##### GPS (10 checks)

| ID | Check | Description |
|---|---|---|
| DG-01 | Position | `GeoPose.lat_deg`/`lon_deg`/`alt_m` for GPS-RTK coordinates. |
| DG-02 | Orientation | `GeoPose.q` (QuaternionXYZW) for heading-derived orientation. |
| DG-03 | Timestamp | `GeoPose.stamp` for 10 Hz GPS samples. |
| DG-04 | Covariance | `GeoPose.cov` for positional uncertainty (RTK ≤1 cm). |
| DG-05 | GNSS quality | `NavSatStatus` provides DOP, fix type, and satellite count with `has_dop` guard. |
| DG-06 | Speed over ground | `NavSatStatus.speed_mps` + `course_deg` with `has_velocity` guard. |
| DG-07 | GNSS constellation bitmask | `NavSatStatus` service field covers the GPS/GLONASS/BEIDOU/GALILEO/QZSS/IRNSS/SBAS constellations in use. |
| DG-08 | Differential correction age | `NavSatStatus` `diff_age` fields carry the RTK differential-correction age. |
| DG-09 | Stream linkage | `NavSatStatus` ↔ `GeoPose` correlation via the shared GNSS stream key. |
| DG-10 | RTK fix-type granularity | `GnssFixType` distinguishes RTK_FLOAT / RTK_FIXED (and DGPS, FIX_3D, etc.) for fix-quality granularity. |

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

All 48 DeepSense 6G checks pass, with no gaps and no deferrals. GNSS diagnostics are covered by `NavSatStatus`, and mmWave Beam checks pass against the provisional `rf_beam` profile (Appendix E).

| Modality | Checks | Pass | Gap | Deferred | Notes |
|---|---|---|---|---|---|
| Radar (tensor) | 8 | 8 | 0 | 0 | — |
| Vision | 7 | 7 | 0 | 0 | Includes 360° rig roles |
| Lidar | 7 | 7 | 0 | 0 | Includes sensor wavelength |
| IMU | 4 | 4 | 0 | 0 | — |
| GPS | 10 | 10 | 0 | 0 | NavSatStatus GNSS diagnostics (DG-01..10) |
| mmWave Beam | 8 | 8 | 0 | 0 | Provisional rf_beam profile (K-B1) |
| Semantics | 4 | 4 | 0 | 0 | Beam labels via rf_beam |
| **Total** | **48** | **48** | **0** | **0** | 48/48 pass, 0 gaps |

Deferred items are fields that CAN be carried (typically via `MetaKV`) but lack first-class typed support. They are tracked as future profile additions, not as conformance failures.

#### Deferred Items

DeepSense 6G conformance has no remaining schema gaps. Future ISAC extensions (e.g., CSI/CIR profiles) remain under discussion; see Appendix K for the maturity promotion criteria.

---

### **I.3 S3E Conformance (Multi-Robot Collaborative SLAM)**

**Validation record.** Validated against SpatialDDS **1.8** (`idl/v1.8/`) · 2026-10-22 · Method: manual schema analysis (no script), re-confirmed against 1.8 scoped by the audit diff — not re-run · Result: **38/38 checks PASS**. Type and field names below are the 1.8 spellings; the one substantive 1.5→1.8 change is `core::Node`'s compound key (SC-01).

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
| SL-01 | LiDAR meta | `LidarMeta` with `type` (`LidarType`), `base.nominal_rate_hz`, and `layout` (`PointLayout`) covers Velodyne VLP-16. |
| SL-02 | Point layout | `PointLayout.XYZ_I_R_T` carries x, y, z, intensity, ring, time — matches Velodyne binary format. |
| SL-03 | Per-robot topic isolation | Topic template `spatialdds/<scene>/lidar/<sensor_id>/frame/v1` with per-robot `sensor_id` (e.g., `alpha/vlp16`). |
| SL-04 | CloudEncoding | `BIN_INTERLEAVED` covers raw binary point cloud blobs. |
| SL-05 | Sensor identity | A single roof-mounted LiDAR needs no rig role — `RigRole` is a Vision-rig enum and is not carried on `LidarMeta`; the sensor is identified by its per-robot `sensor_id` (SL-03). |

##### Per-Robot Sensing — Vision (4 checks)

| ID | Check | Description |
|---|---|---|
| SV-01 | Stereo pair | Two `VisionFrame` streams per robot with `RigRole.LEFT` / `RigRole.RIGHT`. |
| SV-02 | Camera intrinsics | `VisionMeta.K` (`CamIntrinsics`) with `fx`, `fy`, `cx`, `cy`, `dist` (`Distortion`), and `dist_params` covers calibrated stereo cameras. |
| SV-03 | Per-robot namespacing | Topic `spatialdds/<scene>/vision/<sensor_id>/frame/v1` isolates per-robot camera streams. |
| SV-04 | Timestamp sync | `VisionFrame.stamp` synchronized to common timebase via hardware PPS trigger. |

##### Per-Robot Sensing — IMU (3 checks)

| ID | Check | Description |
|---|---|---|
| SI-01 | 9-axis sample | `ImuSample` with accel (Vec3, m/s²) + gyro (Vec3, rad/s) covers 6-axis; `MagnetometerSample` covers magnetometer. |
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
| SC-01 | Per-robot nodes | `core::Node` with `map_id` per robot (e.g., `alpha-map`, `blob-map`, `carol-map`); node identity is the **compound key `(map_id, node_id)`** — the 1.7 change that made both members `@key` — so the same `node_id` in two robots' maps is two distinct instances. |
| SC-02 | Odometry edges | `core::Edge` with `type = ODOM` connects sequential keyframes within each robot's map. |
| SC-03 | Intra-robot loop closures | `core::Edge` with `type = LOOP` for within-map loop closures (e.g., concentric circle paradigm). |
| SC-04 | Versioning | `Node.seq` monotonic per source; `Node.graph_epoch` increments after global re-optimization. |
| SC-05 | Multi-source coexistence | Three simultaneous `source_id` values on `core::Node` and `core::Edge` topics — one per robot. |

##### Mapping Extension — Multi-Agent (8 checks)

| ID | Check | Description |
|---|---|---|
| SM-01 | Map lifecycle | `MapMeta` per robot with `status` (`MapStatus`) progressing: BUILDING → OPTIMIZING → STABLE. |
| SM-02 | Map kind | `MapMeta.kind = POSE_GRAPH` for each robot's SLAM output. |
| SM-03 | Inter-robot loop closures | `mapping::Edge` with `type = INTER_MAP` and `has_from_map_id` / `has_to_map_id` populated. |
| SM-04 | MapAlignment | `MapAlignment` with `T_from_to` expressing the inter-map transform after cross-robot alignment. |
| SM-05 | Alignment revision | `MapAlignment.revision` increments as more inter-robot edges accumulate and the alignment refines. |
| SM-06 | Evidence trail | `MapAlignment.evidence_edge_ids[]` references the specific cross-map edges supporting the alignment. |
| SM-07 | MapEvent notifications | `MapEvent` with `event = ALIGNMENT_NEW` (`MapEventKind`) when two robots' maps are first linked. |
| SM-08 | Concurrent map builds | Three `MapMeta` samples simultaneously active (keyed by the compound `(map_id, source_id)`), demonstrating multi-map lifecycle. |

##### Discovery & Coordination (3 checks)

| ID | Check | Description |
|---|---|---|
| SD-01 | Service announcement | Each robot publishes `Announce` with `ServiceKind.MAPPING` and sensor capabilities in `topics[]`. |
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

| Modality | Checks | Pass | Gap | Deferred | Notes |
|---|---|---|---|---|---|
| LiDAR | 5 | 5 | 0 | 0 | — |
| Vision | 4 | 4 | 0 | 0 | — |
| IMU | 3 | 3 | 0 | 0 | — |
| GNSS/RTK | 3 | 3 | 0 | 0 | — |
| UWB (inter-robot range) | 4 | 4 | 0 | 0 | — |
| Core Pose Graph | 5 | 5 | 0 | 0 | — |
| Mapping (multi-agent) | 8 | 8 | 0 | 0 | — |
| Discovery & Coordination | 3 | 3 | 0 | 0 | — |
| Cross-cutting | 3 | 3 | 0 | 0 | — |
| **Total** | **38** | **38** | **0** | **0** | — |

Deferred items are fields that CAN be carried (typically via `MetaKV`) but lack first-class typed support. They are tracked as future profile additions, not as conformance failures.

#### S3E Scenario Narrative (Informative)

The S3E "teaching building" outdoor sequence illustrates the full multi-agent lifecycle:

1. **Bootstrap.** Three robots (Alpha, Blob, Carol) power on and each publishes an `Announce` with `ServiceKind.MAPPING`, their sensor capabilities, and an initial coverage bounding box. Each begins publishing `core::Node` and `core::Edge` (ODOM) on the pose graph topics with distinct `source_id` and `map_id` values.

2. **Independent mapping.** Each robot runs visual-inertial-lidar SLAM independently. `MapMeta` per robot shows `status = BUILDING`. Keyframes stream as `core::Node`; odometry constraints as `core::Edge` (ODOM); intra-robot loop closures as `core::Edge` (LOOP). `ImuSample`, `VisionFrame`, and `LidarFrame` are published on per-robot sensor topics.

3. **UWB ranging begins.** As robots come within UWB range (~50 m), pairwise distance measurements are published as `mapping::Edge` with `type = RANGE`, `range_m` carrying the measured distance, `has_from_map_id` / `has_to_map_id` identifying which robots' maps the linked nodes belong to.

4. **Inter-robot loop closure.** When Alpha and Blob's LiDAR scans overlap, a cross-robot loop closure is detected. This is published as `mapping::Edge` with `type = INTER_MAP`, `match_score` carrying the ICP fitness, and `from_map_id = "alpha-map"`, `to_map_id = "blob-map"`.

5. **Map alignment.** A `MapAlignment` is published linking Alpha's and Blob's maps, with `method = LIDAR_ICP` (or `MULTI_METHOD` if UWB ranges were fused), `T_from_to` carrying the inter-map transform, and `evidence_edge_ids[]` referencing the supporting cross-map edges. `MapEvent` with `event = ALIGNMENT_NEW` notifies all subscribers.

6. **Multi-frame localization.** Once the alignment exists, a geo-referencing service can publish `NodeGeo` with `poses[]` containing FramedPoses in both Alpha's and Blob's map frames simultaneously. Consumers (e.g., a planning service) can pick the frame they need.

7. **Graph optimization.** After sufficient inter-robot constraints accumulate, a global optimizer runs. All robots' `MapMeta.status` transitions to `OPTIMIZING`, then `STABLE`. `graph_epoch` increments on all nodes and edges. `MapAlignment.revision` increments. Consumers watching `graph_epoch` know to re-fetch the entire graph.

This end-to-end scenario is precisely what ROS 2's `nav_msgs` and `sensor_msgs` cannot express: there is no ROS 2 standard for map lifecycle, inter-map alignment, range-only constraints, or multi-agent discovery with spatial coverage.

---

### **I.4 ScanNet Conformance (Indoor Scene Understanding)**

**Validation record.** Validated against SpatialDDS **1.8** (`idl/v1.8/`) · 2026-10-22 · Method: manual schema analysis (no script), re-confirmed against 1.8 scoped by the audit diff — not re-run · Result: **35/35 checks PASS** (3 deferred items). Type and field names below are the 1.8 spellings.

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
| NC-02 | Color frame | `VisionFrame` per RGB image with `frame_seq`, `hdr.t_start`/`hdr.t_end` (`FrameHeader` carries `t_start`/`t_end`, not a single `stamp`), blob reference to JPEG payload. |
| NC-03 | Per-scene stream isolation | Topic `spatialdds/<scene_id>/vision/<stream_id>/frame/v1` with unique `stream_id` per scan. |
| NC-04 | Rig linkage | `VisionMeta.rig_id` shared between color and depth streams for spatial association. |

##### RGB-D Sensing — Depth (5 checks)

| ID | Check | Description |
|---|---|---|
| ND-01 | Depth meta | `VisionMeta` with `pix = DEPTH16`, `codec = CODEC_NONE` (raw 16-bit), `CamIntrinsics` for depth camera. |
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
| NM-02 | Map lifecycle | `MapMeta.status` (`MapStatus`) = STABLE for completed reconstructions (offline dataset; no BUILDING phase observed). |
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
| NE-01 | Zone entry | `SpatialEvent` with `type = ZONE_ENTRY` (`EventType`) when a Detection3D instance is first observed within a SpatialZone's bounds. |
| NE-02 | Trigger linkage | `SpatialEvent.trigger_det_id` references the triggering `Detection3D.det_id`; `trigger_class_id` carries the NYU40 label. |
| NE-03 | Zone state | `ZoneState` with `current_occupancy` count reflecting the number of annotated object instances within the room. (`zone_occupancy` is a `SpatialEvent` field, for `CAPACITY_BREACH`, not a `ZoneState` field.) |
| NE-04 | Class counts | `ZoneState.class_counts` (sequence of MetaKV) carries per-class occupancy (e.g., `{"count": 4}` for class "chair"). |

#### Results

All 35 ScanNet checks pass.

| Modality | Checks | Pass | Gap | Deferred | Notes |
|---|---|---|---|---|---|
| Color (RGB) | 4 | 4 | 0 | 1 | 2D label image format deferred |
| Depth (RGBD) | 5 | 5 | 0 | 0 | — |
| IMU | 2 | 2 | 0 | 0 | — |
| Camera Pose & Frames | 4 | 4 | 0 | 0 | — |
| Mesh Reconstruction | 4 | 4 | 0 | 1 | Per-vertex semantic labels deferred |
| 3D Instance Segmentation | 6 | 6 | 0 | 1 | First-class CAD reference deferred |
| Spatial Events — Zones | 6 | 6 | 0 | 0 | — |
| Spatial Events — Object Events | 4 | 4 | 0 | 0 | — |
| **Total** | **35** | **35** | **0** | **3** | — |

Deferred items are fields that CAN be carried (typically via `MetaKV` or `BlobRef`) but lack first-class typed support. They are tracked as future profile additions, not as conformance failures.

#### ScanNet Scenario Narrative (Informative)

The ScanNet "apartment" scan sequence illustrates how SpatialDDS types map to a complete indoor scene understanding pipeline:

1. **Scan ingestion.** An operator walks through a kitchen with an iPad running the ScanNet capture app. Color frames are published as `VisionFrame` (pix=RGB8, codec=JPEG) and depth frames as `VisionFrame` (pix=DEPTH16, codec=NONE) on paired streams linked by `rig_id`. `ImuSample` streams concurrently from the embedded IMU.

2. **Pose estimation.** BundleFusion produces per-frame camera poses, published as `FrameHeader.sensor_pose` on each VisionFrame. The per-scene axis-alignment matrix is published as a `FrameTransform` from the sensor coordinate system to a gravity-aligned room frame.

3. **Mesh reconstruction.** The completed surface mesh is registered as `MapMeta` with `kind = MESH`, `status = STABLE`. The PLY file is referenced via `BlobRef`. Vertex/face counts are carried in `MapMeta.attributes`.

4. **Zone definition.** The kitchen is defined as a `SpatialZone` with `kind = MONITORING`, `bounds` enclosing the room extent, and `attributes` carrying `scene_type = "kitchen"`. The `frame_ref` points to the gravity-aligned frame.

5. **3D instance detection.** Crowdsourced annotations produce `Detection3D` instances for each labeled object: chairs with `class_id = "chair"`, tables with `class_id = "table"`, a refrigerator with `class_id = "refrigerator"` — each with an oriented bounding box in the aligned frame.

6. **Spatial events.** A zone monitoring service evaluates which Detection3D instances fall within the kitchen SpatialZone's bounds and publishes `SpatialEvent` (ZONE_ENTRY) for each. `ZoneState` is published periodically with `current_occupancy = 12` (total instances) and `class_counts` listing per-class breakdowns.

This pipeline exercises the Spatial Events extension end-to-end — from zone definition through detection to event generation — a capability path untested by nuScenes (no zones), DeepSense 6G (no zones), or S3E (no zones or semantics).

#### Deferred Items

- **Per-vertex semantic labels.** ScanNet provides per-vertex class labels on the reconstructed mesh. SpatialDDS has no per-vertex label type; the labeled mesh PLY is carried as a `BlobRef`. A future per-vertex or per-point semantic annotation type could make this data first-class.
- **CAD model alignment.** ScanNet aligns ShapeNet CAD models to detected objects. The ShapeNet model ID can be carried in `Detection3D.attributes` as a MetaKV, but there is no first-class CAD reference type.
- **2D projected labels.** ScanNet provides per-frame 2D semantic/instance label images. These can be published as `VisionFrame` with a label-specific `stream_id` and `pix = RAW16` (16-bit label IDs), but a dedicated label pixel format is not defined.

---

### **I.5 LaMAR Conformance (Multi-Device AR Localization & Mapping)**

**Validation record.** Validated against SpatialDDS **1.8** (`idl/v1.8/`) · 2026-10-22 · Method: manual schema analysis (no script), re-confirmed against 1.8 scoped by the audit diff — not re-run · Result: **69/71 checks PASS, 2 gaps** (LH-05, LP-02 — no typed shutter-type field on `VisionMeta`). The pass relies on the `FrameRef.coord_convention` field (added 1.6) and the provisional `sensing.radio` profile, both carried in 1.8; 22 of the 71 checks are the radio subset. Type and field names below are the 1.8 spellings. Two checks that leaned on a non-existent `VisionMeta.attributes` field are reclassified from PASS to GAP (LH-05, LP-02); the 8-bit grayscale pixel format LH-02 relied on was added to the IDL as `PixFormat.GRAY8`, so LH-02 is now a true PASS.

#### Reference Dataset

**LaMAR** (ETH Zürich / Microsoft Mixed Reality & AI Lab) is a large-scale multi-device localization and mapping benchmark for augmented reality containing:

| Dimension | Value |
|---|---|
| Locations | 3 (historical building 18,000 m², office building 12,000 m², old town 15,000 m²) |
| Total area | 45,000 m² indoor + outdoor |
| HoloLens 2 | 4 cameras, 83° FOV, 30 Hz, VGA grayscale, global shutter; ToF depth/IR 1 Hz; IMU; Bluetooth + WiFi |
| iPhone / iPad | 1 camera, 64° FOV, 10 Hz, 1080p RGB, rolling shutter, auto-focus; LiDAR depth 10 Hz; IMU; WiFi (partial BT) |
| NavVis M6 / VLX | 4–6 cameras, 90–113° FOV, 1–3 m interval, 1080p RGB; lidar point cloud + dense mesh |
| Trajectories | 100+ sessions per location, 10 participants, over 1 year |
| Capture duration | 100+ hours, 40+ km of trajectories |
| Radio signals | WiFi RSSI fingerprints + Bluetooth beacon scans, per-timestamp |
| Ground truth | Laser scan alignment, cm-level pose accuracy, automated pipeline |
| Pose convention | sensor-to-world transforms; camera-to-rig extrinsics (Kapture format, inverted convention) |
| Data format | Custom "Capture" format: `sessions/`, `sensors.txt`, `rigs.txt`, `trajectories.txt`, `images.txt`, `depths.txt`, `wifi.txt`, `bt.txt` |

LaMAR was chosen because it is the first conformance dataset to exercise **cross-device heterogeneity** (HoloLens headset, iPhone/iPad handheld, NavVis scanner rig — three fundamentally different device classes sharing a common spatial reference), the **Anchors profile** (geo-anchored reference frames, cross-session alignment, persistent spatial landmarks), the **Discovery profile** in a multi-device context (heterogeneous service announcements with different sensor capabilities and coverage), **multi-session map alignment** (laser scans registered across year-long intervals with structural changes), and the **`sensing.radio` profile** in production AR workflows (WiFi/BT fingerprint streams driving +4.6–17.5% recall improvement). No prior conformance dataset tests these capabilities: nuScenes is single-vehicle, DeepSense 6G is single-platform, S3E has homogeneous robots, and ScanNet is single-device single-session.

#### Checks Performed (71)

##### HoloLens 2 — Vision (6 checks)

| ID | Check | Description |
|---|---|---|
| LH-01 | Multi-camera rig | `VisionMeta` per camera with distinct `stream_id`; 4 cameras per HoloLens rig linked by shared `rig_id`. |
| LH-02 | Grayscale pixel format | `PixFormat.GRAY8` covers HoloLens VGA grayscale global-shutter cameras. |
| LH-03 | Frame rate | `StreamMeta.nominal_rate_hz` = 30 for HoloLens camera streams. |
| LH-04 | Rig extrinsics | Camera-to-rig transforms publishable as `FrameTransform` with `T_parent_child` (rig body → camera). |
| LH-05 | Global shutter flag | **GAP.** This check assumed shutter type could ride as `MetaKV` on `VisionMeta.attributes`, but `VisionMeta` (and its `base`) has **no `attributes` field** — there is no typed landing spot for shutter type in the Vision profile. Whether the metadata escape should be a typed `attributes` member, a dedicated shutter-type enum field, or a typed extension mechanism is a 1.9 design question (see Future Directions). |
| LH-06 | Camera intrinsics | `CamIntrinsics` with `fx`, `fy`, `cx`, `cy` per camera. HoloLens provides per-frame calibration from on-device tracker — `CamModel.PINHOLE` for undistorted images. |

##### HoloLens 2 — Depth (4 checks)

| ID | Check | Description |
|---|---|---|
| LD-01 | ToF depth stream | `VisionMeta` with `pix = DEPTH16` for HoloLens Time-of-Flight depth sensor. |
| LD-02 | Depth frame rate | `StreamMeta.nominal_rate_hz` = 1 for HoloLens ToF sensor (low-rate depth). |
| LD-03 | Depth rig linkage | `VisionMeta.rig_id` shared between depth and grayscale streams for spatial association. |
| LD-04 | IR stream | HoloLens infrared frames publishable as `VisionFrame` with separate `stream_id` and `pix = GRAY8` or `RAW16`. |

##### iPhone / iPad — Vision (5 checks)

| ID | Check | Description |
|---|---|---|
| LP-01 | Single camera | `VisionMeta` with `pix = RGB8`, single `stream_id` per phone session. |
| LP-02 | Rolling shutter | **GAP.** Same as LH-05: rolling-shutter metadata has no landing spot — `VisionMeta` has no `attributes` field. Reclassified from PASS to GAP; the typed-metadata design question is deferred to 1.9 (see Future Directions). |
| LP-03 | Auto-focus intrinsics | `CamIntrinsics` per frame accommodates changing focal length from auto-focus. HoloLens provides fixed calibration; phone provides per-frame — both map to same `CamIntrinsics` struct. |
| LP-04 | Frame rate | `StreamMeta.nominal_rate_hz` = 10 for iPhone/iPad capture rate. |
| LP-05 | JPEG compression | `Codec.JPEG` for phone image compression. |

##### iPhone / iPad — Depth (3 checks)

| ID | Check | Description |
|---|---|---|
| LPD-01 | LiDAR depth | `VisionMeta` with `pix = DEPTH16` for iPad LiDAR Scanner depth frames. |
| LPD-02 | Depth frame rate | `StreamMeta.nominal_rate_hz` = 10 for iPad LiDAR (matches color frame rate). |
| LPD-03 | Depth rig linkage | `VisionMeta.rig_id` links LiDAR depth and color streams for factory-aligned iPad sensor pair. |

##### NavVis Scanner — Vision + LiDAR (5 checks)

| ID | Check | Description |
|---|---|---|
| LN-01 | Multi-camera rig | `VisionMeta` per panoramic camera (4–6 cameras); `RigRole` values cover top-mounted and side-mounted configurations. |
| LN-02 | HD resolution | `CamIntrinsics.width` / `height` at 1080p for NavVis synchronized cameras. |
| LN-03 | LiDAR point cloud | `MapMeta` with `kind = MESH` for processed NavVis dense mesh; `BlobRef` for PLY payload. Point cloud with 1 cm grid resolution. |
| LN-04 | LiDAR mesh | Dense triangle mesh (Advancing Front algorithm) publishable as `MapMeta` with `kind = MESH`, `state = STABLE`. Vertex/face counts in `MapMeta.attributes`. |
| LN-05 | Scan interval images | NavVis images captured at 1–3 m intervals (not continuous video); `VisionFrame` per capture with `frame_seq` for ordering. |

##### IMU (3 checks)

| ID | Check | Description |
|---|---|---|
| LI-01 | Multi-device IMU | `ImuSample` with accel + gyro covers HoloLens embedded IMU and iPhone CoreMotion IMU. Both publish on per-device sensor topics. |
| LI-02 | High-rate IMU | HoloLens accelerometer/gyroscope/magnetometer at device-native rates. `ImuSample.seq` monotonic per source. |
| LI-03 | Per-device namespace | Topic `spatialdds/<location>/imu/<device_id>/sample/v1` isolates per-device IMU streams. |

##### Poses & Trajectories (5 checks)

| ID | Check | Description |
|---|---|---|
| LT-01 | Sensor-to-world pose | `FrameHeader.sensor_pose` (`PoseSE3`) carries per-frame sensor-to-world transform. LaMAR's `trajectories.txt` convention (sensor-to-world) maps directly. |
| LT-02 | VIO tracking poses | On-device tracker poses (ARKit for iPhone, HoloLens tracker) publishable as `PoseSE3` with source-specific `frame_ref`. These are relative to session start — local odometry frame. |
| LT-03 | GT poses | Ground-truth poses from the LaMAR alignment pipeline (laser scan registration + bundle adjustment) publishable as `PoseSE3` in the GT reference world frame. |
| LT-04 | Pose uncertainty | LaMAR provides per-frame covariance from Hessian inversion of refinement. Maps to `CovMatrix` on `FramedPose`. |
| LT-05 | Quaternion convention | LaMAR uses 4×4 rotation matrices; decomposition to `(x,y,z,w)` quaternion per §2 convention table. Same pattern as ScanNet (NP-04). |

##### Multi-Session Alignment — Anchors Profile (7 checks)

| ID | Check | Description |
|---|---|---|
| LA-01 | Scan-to-scan alignment | Rigid transform aligning NavVis scan sessions publishable as `FrameTransform` with `T_parent_child` mapping one scan's origin to the GT world frame. |
| LA-02 | Sequence-to-scan alignment | Per-AR-sequence rigid alignment (`wT_init_0` from voting) publishable as `FrameTransform` linking session-local tracking frame to GT reference frame. |
| LA-03 | GeoAnchor for reference frame | The GT world frame origin publishable as `GeoAnchor` with `method = "Surveyed"` (laser scan derived), `confidence` from alignment error statistics. Bridges local map coordinates to global position. |
| LA-04 | AnchorSet for scan landmarks | NavVis scan landmarks (e.g., QR codes detected by `run_qrcode_detection`) publishable as `AnchorSet` with per-anchor `AnchorEntry` carrying a `GeoPose` (`AnchorEntry.geopose`). `set_id` identifies the scan session's anchor collection. |
| LA-05 | Cross-session alignment revision | `alignment_global.txt` records inter-session transforms with error statistics. Maps to `FrameTransform` with `CovMatrix` carrying alignment uncertainty. Multiple NavVis sessions → multiple `FrameTransform` instances with `transform_id` keyed per session pair. |
| LA-06 | Alignment refinement lifecycle | LaMAR's GT pipeline progresses: initial localization → rigid alignment → pose graph optimization → bundle adjustment. Each stage improves accuracy. The final `FrameTransform` carries the refined transform; `CovMatrix` reflects reduced uncertainty at each stage. |
| LA-07 | Year-long structural change | Scans captured over 1+ year with structural changes (construction, furniture rearrangement). Cross-session alignment still succeeds. Demonstrates `FrameTransform` stability across temporal changes — the anchor/reference frame persists even as scene content changes. |

##### Discovery — Multi-Device (5 checks)

| ID | Check | Description |
|---|---|---|
| LDI-01 | Heterogeneous device announcements | Each device class (HoloLens, iPhone/iPad, NavVis) publishes `Announce` with `ServiceKind.MAPPING` and distinct sensor capabilities in `topics[]`. HoloLens advertises 4-camera rig + ToF + IMU + BT + WiFi; phone advertises 1 camera + LiDAR + IMU + WiFi; NavVis advertises multi-camera rig + lidar. |
| LDI-02 | Coverage geometry | `Announce.coverage` (Aabb3 or sphere) advertises each device's operational area within the location. NavVis covers entire building; AR sessions cover trajectory corridors. |
| LDI-03 | Sensor capability advertisement | `Announce.topics[]` lists typed topics per device with `TopicMeta` entries: vision, depth, IMU topics for AR devices; vision + pointcloud + mesh topics for NavVis. Consumers can discover which modalities are available from each device. |
| LDI-04 | Cross-device map reference | After alignment, all devices reference a common GT world frame. `Announce.coverage_frame_ref` references this shared `FrameRef`, enabling consumers to evaluate coverage in a common coordinate system. |
| LDI-05 | Service manifest | `Announce.manifest_uri` references a `spatialdds://` URI resolvable to a manifest describing the mapping service's capabilities, coverage area, and data assets (mesh, point cloud, image database). |

##### Radio Profile Coverage (12 checks)

The 22 radio checks in this and the next two sub-sections validate `sensing.radio` against LaMAR's `wifi.txt` / `bt.txt` data path. They subsume the four high-level "Radio Signals" checks (WiFi fingerprint, BT scan, radio-assisted retrieval, temporal aggregation) by exercising the typed transport directly.

| ID | Check | Description |
|---|---|---|
| LM-01 | Typed per-scan container | `RadioScan` carries one scan event with `sensor_id`, `radio_type`, `scan_seq`, and `stamp`. |
| LM-02 | Typed per-observation container | `RadioObservation` carries one transmitter measurement (`identifier`, `measurement_kind`, `value`). |
| LM-03 | WiFi identifier format | BSSID maps to lowercase colon-separated `identifier`. |
| LM-04 | BLE identifier format | Beacon UUID/MAC maps to canonical `identifier`. |
| LM-05 | RSSI representation | RSSI maps to `measurement_kind = RSSI`, `value` in dBm. |
| LM-06 | WiFi frequency/channel | `frequency_mhz`, `band`, and `channel` map with `has_*` guards. |
| LM-07 | BLE major/minor | iBeacon major/minor maps with `has_major_minor`. |
| LM-08 | BLE Tx power | Advertised Tx power maps with `has_tx_power`. |
| LM-09 | Scan duration | Variable scan-window duration maps to `scan_duration_s`. |
| LM-10 | Aggregation window | ±window aggregation (LaMAR's ±2s pattern) maps to `aggregation_window_s`. |
| LM-11 | Sensor metadata | `RadioSensorMeta` captures capability flags and adapter metadata. |
| LM-12 | Schema tag | `schema_version` set to `spatial.sensing.radio/1.8`. |

##### Radio — Discovery and QoS Integration (5 checks)

| ID | Check | Description |
|---|---|---|
| LRD-01 | Registered type | Discovery type registry includes `radio_scan`. |
| LRD-02 | QoS profile | `RADIO_SCAN_RT` available for radio scan topics. |
| LRD-03 | Topic naming | Topic pattern `spatialdds/<scene>/radio/<sensor_id>/scan/v1` is valid under §3.3.1. |
| LRD-04 | Meta durability | `RadioSensorMeta` uses RELIABLE + TRANSIENT_LOCAL semantics. |
| LRD-05 | Optional fields | Radio optional values consistently follow the `has_*` guard pattern. |

##### Radio — Interop and Privacy (5 checks)

| ID | Check | Description |
|---|---|---|
| LRP-01 | Multi-technology support | A device can publish separate WiFi and BLE scan streams with shared timebase. |
| LRP-02 | Fingerprint matching readiness | Canonical identifier formats support stable join keys across sessions. |
| LRP-03 | Pose association | Optional `sensor_pose` + `pose_frame_ref` supports radio-visual alignment for retrieval pipelines. |
| LRP-04 | Privacy guidance | Identifier anonymization guidance documented for sensitive deployments (§2.7.6 + Appendix E radio profile). |
| LRP-05 | No algorithm coupling | Profile transports observations only; no positioning algorithm mandated. |

##### Cross-Device Localization (6 checks)

| ID | Check | Description |
|---|---|---|
| LC-01 | Phone-to-scan localization | Phone images matched against NavVis scan-derived SfM map. 2D-3D correspondences → PnP pose. The localization result publishable as `PoseSE3` with `method` attribute indicating visual localization source. |
| LC-02 | HoloLens-to-scan localization | HoloLens rig (4 cameras) localized using generalized GP3P solver. Rig-level pose publishable as `PoseSE3` on rig frame; per-camera poses derived from rig extrinsics. |
| LC-03 | Cross-device map building | Maps built from HoloLens data can localize phone queries and vice versa. SpatialDDS types (`VisionMeta`, `CamIntrinsics`, `PoseSE3`) are device-agnostic — the same types serve HoloLens grayscale rigs and phone RGB frames. |
| LC-04 | Visual overlap score | LaMAR defines per-image-pair visual overlap O ∈ [0,1] using ray-traced mesh visibility. Publishable as `MetaKV` on correspondence edges or as an attribute in a mapping `Edge` with `match_score`. |
| LC-05 | Multi-FOV handling | HoloLens (83° × 4 cameras = ~280° rig FOV) vs phone (64° single camera). `CamIntrinsics` per sensor correctly parameterizes each; `rig_id` groups HoloLens cameras. FOV difference is captured in calibration, not in type hierarchy. |
| LC-06 | Coord convention mismatch | hloc / colmap poses use `CV` (X-right, Y-down, Z-forward); HoloLens reports `GRAPHICS` (X-right, Y-up, Z-backward); GT world frame is `ENU`. `FrameRef.coord_convention` (§2.12) labels each frame so consumers detect and resolve mismatches automatically — the integration scenario that originally motivated the 1.6 patch. |

#### Results

Of the 71 LaMAR checks, **69 pass and 2 are gaps** (LH-05 and LP-02 — shutter-type metadata has no typed landing spot in the Vision profile, since `VisionMeta` has no `attributes` field; see Future Directions).

| Modality | Checks | Pass | Gap | Deferred | Notes |
|---|---|---|---|---|---|
| HoloLens Vision | 6 | 5 | 1 | 0 | LH-05 (global shutter) GAP: no `VisionMeta.attributes` |
| HoloLens Depth | 4 | 4 | 0 | 0 | ToF depth, IR stream |
| Phone Vision | 5 | 4 | 1 | 0 | LP-02 (rolling shutter) GAP: no `VisionMeta.attributes` |
| Phone Depth | 3 | 3 | 0 | 0 | iPad LiDAR depth |
| NavVis Scanner | 5 | 5 | 0 | 0 | Multi-camera rig, lidar mesh, point cloud |
| IMU | 3 | 3 | 0 | 1 | Per-frame gravity vector deferred |
| Poses & Trajectories | 5 | 5 | 0 | 0 | VIO, GT, uncertainty, quaternion convention |
| Multi-Session Alignment (Anchors) | 7 | 7 | 0 | 0 | Scan-to-scan, sequence-to-scan, year-long stability |
| Discovery (Multi-Device) | 5 | 5 | 0 | 0 | Heterogeneous announcements, coverage, manifests |
| Radio Profile Coverage | 12 | 12 | 0 | 1 | CSI/CIR first-class transport deferred |
| Radio Discovery + QoS | 5 | 5 | 0 | 0 | `radio_scan` + `RADIO_SCAN_RT` integrated |
| Radio Interop + Privacy | 5 | 5 | 0 | 1 | Multi-band coexistence metadata deferred |
| Cross-Device Localization | 6 | 6 | 0 | 1 | Includes LC-06 coord-convention check; visual-overlap edge attribute deferred |
| **Total** | **71** | **69** | **2** | **4** | 69/71 pass, 2 gaps (LH-05, LP-02) |

Deferred items are fields that CAN be carried (typically via `MetaKV` or `BlobRef`) but lack first-class typed support. They are tracked as future profile additions, not as conformance failures.

#### Gap Analysis

The original LaMAR conformance pass identified **LM-1: no first-class radio fingerprint type** as a gap, with WiFi and Bluetooth scans falling back to ad hoc `MetaKV` JSON payloads. **LM-1 is closed in 1.5+** by the provisional `sensing.radio` profile (Appendix E). The 22 radio checks (Radio Profile Coverage / Discovery + QoS / Interop + Privacy — 12 + 5 + 5) validate the closure; they are a subset of the 71 LaMAR checks, not the LaMAR total.

Two gaps remain open after this re-audit. **LH-05 / LP-02 — shutter-type metadata has no typed landing spot:** both checks assumed camera shutter type (global vs rolling) could ride as `MetaKV` on `VisionMeta.attributes`, but `VisionMeta` has no `attributes` field. This is left as a GAP rather than closed by adding a generic key-value bag, because a metadata escape is a one-way door; the real design question — typed extension mechanism, a dedicated shutter-type enum field, or a ruled `attributes` member — is captured as a 1.9 candidate (Future Directions, "Typed metadata on sensor meta").

#### LaMAR Scenario Narrative (Informative)

The LaMAR "CAB" office building sequence illustrates the full multi-device AR alignment lifecycle — the scenario class that no prior conformance dataset exercises:

1. **Reference scan.** A NavVis VLX backpack scans the CAB building twice over 6 months. Each scan produces a dense lidar point cloud (1 cm grid), a triangle mesh, and panoramic images at 1–3 m intervals. Each scan session publishes an `Announce` with `ServiceKind.MAPPING`, `topics[]` listing vision + pointcloud + mesh streams, and `coverage` enclosing the scanned area. The two scan sessions are aligned by ICP on the point clouds; the rigid transform is published as `FrameTransform` linking scan-B's origin to scan-A's world frame.

2. **GeoAnchor establishment.** The aligned scan pair defines the GT reference frame. A `GeoAnchor` is published anchoring the world frame origin to a WGS84 position derived from the building's surveyed coordinates. QR codes detected during scanning are published as an `AnchorSet` with per-QR `AnchorEntry` entries — persistent visual landmarks that future AR devices can recognize.

3. **HoloLens session.** A participant wearing HoloLens 2 walks through the building. The headset's 4-camera tracking rig publishes `VisionFrame` (`GRAY8`, 30 Hz) on 4 parallel streams linked by `rig_id`. ToF depth publishes `VisionFrame` (`DEPTH16`, 1 Hz) on a separate stream sharing the same `rig_id`. IMU publishes `ImuSample` at device-native rate. WiFi and Bluetooth scans publish as `RadioScan` with `radio_type = WIFI` and `BLE` respectively, advertised via `RadioSensorMeta`. The on-device head tracker publishes relative poses as `PoseSE3` in the session-local tracking frame.

4. **Phone session.** Another participant carries an iPad Pro through the same space at a different time. The single camera publishes `VisionFrame` (`RGB8`, JPEG, 10 Hz) with per-frame `CamIntrinsics` (varying `fx` from auto-focus). The iPad LiDAR publishes `VisionFrame` (`DEPTH16`, 10 Hz) on a paired stream linked by `rig_id`. ARKit publishes tracking poses as `PoseSE3` in the ARKit session frame. WiFi scans publish as `RadioScan` with sparse BT coverage.

5. **Sequence-to-scan alignment.** For each AR session, the alignment pipeline localizes frames against the reference scan's SfM model using feature matching and PnP (phone) or GP3P (HoloLens rig). The rigid alignment from tracking frame to GT world frame is published as `FrameTransform`. Pose graph optimization refines all per-frame poses jointly — the refined poses carry `CovMatrix` uncertainty from the Hessian.

6. **Cross-device localization.** A phone query image is matched against a map built from HoloLens data — or vice versa. Both devices' data flows through identical SpatialDDS types (`VisionMeta`, `CamIntrinsics`, `PoseSE3`); the types are device-agnostic. Radio fingerprints from the WiFi/BT `RadioScan` streams constrain image retrieval to spatially plausible candidates, improving recall by the +4.6–17.5% the LaMAR paper documents.

7. **Global refinement.** All sessions — multiple NavVis scans, dozens of HoloLens sequences, dozens of phone sequences captured over a year — are jointly optimized. Sequence-to-sequence visual correspondences augment the scan-based constraints. The final GT poses achieve cm-level accuracy with calibrated uncertainty. The entire aligned dataset is accessible through `FrameTransform` chains rooting all device frames in the common GT world frame, which is itself geo-anchored via `GeoAnchor`.

This end-to-end pipeline exercises the **Anchors profile** (`GeoAnchor`, `FrameTransform`, `AnchorSet` for QR landmarks), the **Discovery profile** (heterogeneous device announcements with different sensor capabilities), the **`sensing.radio` profile** (typed WiFi/BT transport replacing ad hoc `MetaKV`), **cross-device frame alignment** (headset, phone, and scanner all registered into a common frame through transform chains), and **multi-session temporal persistence** (year-long alignment stability) — capabilities untested by any prior conformance dataset.

#### Deferred Items

- **Rolling-shutter timing model.** SpatialDDS has no first-class rolling-shutter timing model (readout direction, row exposure time, line delay). LaMAR's phone images use rolling shutter; the shutter type is carriable as `MetaKV` but not typed.
- **Per-frame gravity vector.** HoloLens raw data includes per-frame gravity estimates. SpatialDDS's `ImuSample` carries raw accel/gyro but not processed gravity direction. Gravity is carriable as `MetaKV` or derived downstream.
- **Visual overlap score.** LaMAR's mesh-based visual overlap metric `O(i→j)` is a novel quantity with no SpatialDDS equivalent. A future matchability or visibility score on observation edges could make this first-class.
- **CSI/CIR first-class payloads.** `CSI_REF` currently points to external payloads via `BlobRef`. A future radio extension may define typed CSI/CIR transport.
- **Multi-band coexistence metadata.** Additional fields for scan policy and dwell-time scheduling may be needed for dense AP environments.

---

### **Reproducing the Tests**

The nuScenes and DeepSense 6G conformance harnesses are self-contained Python 3 scripts with no external dependencies; both read the SpatialDDS 1.8 type shapes from `idl/v1.8/` through `scripts/idl_introspect.py`, so neither carries a hand-typed copy of the IDL.

**nuScenes harness** (`scripts/nuscenes_harness_v2.py`):

```bash
python3 scripts/nuscenes_harness_v2.py
```

Reads the SpatialDDS 1.8 IDL type shapes directly from `idl/v1.8/` (via `scripts/idl_introspect.py`) and checks them against the nuScenes schema — no hand-mirror, so the harness cannot drift from the spec. Produces a plain-text report and a JSON results file.

**DeepSense 6G harness** (`scripts/deepsense6g_harness_v3.py`):

```bash
python3 scripts/deepsense6g_harness_v3.py
```

Validates 48 checks across 7 modalities (radar tensor, vision, lidar, IMU, GPS, mmWave beam, semantics); GPS carries 10 checks (DG-01 through DG-10). The mmWave beam checks validate against the provisional `rf_beam` profile (Appendix E). Produces a plain-text report and a JSON results file (written to the current directory).

**S3E conformance**: The 38 S3E checks documented in §I.3 were performed as a manual schema-vs-schema analysis. A scripted harness (`scripts/s3e_harness_v1.py`) following the same pattern as the nuScenes and DeepSense 6G scripts is planned for a future revision.

**ScanNet conformance**: The 35 ScanNet checks documented in §I.4 were performed as a manual schema-vs-schema analysis. A scripted harness (`scripts/scannet_harness_v1.py`) is planned for a future revision.

**LaMAR conformance**: The 71 LaMAR checks documented in §I.5 — of which 22 are the `sensing.radio` checks validated against the published `wifi.txt` / `bt.txt` field layouts and the radio-assisted retrieval workflow described by the benchmark — were performed as a manual schema-vs-schema analysis. A scripted harness (`scripts/lamar_harness_v1.py`) is planned for a future revision.

No harness requires network access, a DDS runtime, or a dataset download. Implementers are encouraged to adapt the harnesses for additional reference datasets (e.g., Waymo Open, KITTI, Argoverse 2, RADIal, SubT-MRS, ScanNet, LaMAR) to validate coverage for sensor configurations or multi-agent scenarios not already covered.

### **Limitations**

This testing validates schema expressiveness -- whether every dataset field has a lossless SpatialDDS mapping. It does not validate:

- **Wire interoperability** -- actual DDS serialization/deserialization round-trips.
- **Performance** -- throughput, latency, or memory footprint under real sensor loads.
- **Semantic correctness** -- whether a particular producer's mapping preserves the intended meaning of each field.
- **Multi-dataset coverage** -- datasets with different sensor configurations (e.g., solid-state lidar, event cameras, ultrasonic sensors) or deployment patterns (e.g., multi-floor hierarchical spaces, aerial-ground cooperation, dense pedestrian tracking) may surface additional gaps. S3E covers three-robot outdoor coordination; ScanNet covers single-room indoor scenes. Larger fleet sizes, degraded-communication environments, multi-floor buildings, and heterogeneous robot types (ground + aerial) remain untested.

These areas are appropriate targets for future conformance work.
