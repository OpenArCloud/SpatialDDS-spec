## **Appendix I: Dataset Conformance Testing (Informative)**

*This appendix documents systematic conformance testing performed against a large-scale, multi-modal autonomous driving dataset. The results validated the completeness and expressiveness of the SpatialDDS 1.5 sensing and semantics profiles and directly informed several normative additions to this specification.*

### **Motivation**

Sensor-data specifications risk becoming disconnected from real-world workloads if they are designed in isolation. To guard against this, the SpatialDDS 1.5 extension profiles (Appendix D) were validated against a well-known public reference dataset -- the **nuScenes** autonomous driving corpus -- which exercises all five sensor modalities simultaneously: camera, lidar, radar, semantic annotations, and shared conventions (coordinate frames, quaternion order, timing).

The goal was not to certify a particular dataset but to answer a concrete question: *Can every field, enum, and convention in the nuScenes schema be losslessly mapped to SpatialDDS 1.5 IDL without workarounds or out-of-band agreements?*

### **Reference Dataset**

**nuScenes** (Motional / nuTonomy) is a multimodal dataset containing:

| Dimension | Value |
|---|---|
| Scenes | 1,000 (20 s each) |
| Cameras | 6 surround-view (FRONT, FRONT_LEFT, FRONT_RIGHT, BACK, BACK_LEFT, BACK_RIGHT) |
| Lidar | 1 x 32-beam spinning (Velodyne HDL-32E), ~34 k points/scan |
| Radar | 5 x Continental ARS 408 (FRONT, FRONT_LEFT, FRONT_RIGHT, BACK_LEFT, BACK_RIGHT) |
| 3D annotations | 1.4 M oriented bounding boxes, 23 object classes |
| Annotation metadata | visibility tokens, attribute tokens, per-box lidar/radar point counts |
| Coordinate convention | Right-handed; quaternions in (w, x, y, z) order |

The dataset was chosen because it stresses sensor diversity (six camera rigs, five radar units, one lidar), per-detection radar fields rarely found in other corpora (compensated velocity, dynamic property, RCS), and rich annotation metadata (visibility, attributes, evidence counts).

### **Methodology**

A conformance harness was constructed as a Python script that:

1. **Mirrors the SpatialDDS 1.5 IDL** as Python data structures (enum values, struct field lists, normative prose flags).
2. **Mirrors the nuScenes schema** as synthetic data (camera names, radar point fields, lidar layout, annotation fields).
3. **Runs 27 targeted checks** across five modalities, each producing a verdict:

| Verdict | Meaning |
|---|---|
| **PASS** | nuScenes field maps losslessly to an existing SpatialDDS type or enum value. |
| **GAP** | A mapping exists but requires additional prose, an enum value, or a convention note. |
| **MISSING** | No SpatialDDS construct exists for the nuScenes field; a new IDL member is needed. |

4. **Reports a per-modality scorecard** comparing current results against a baseline.

The harness does not require network access, a DDS runtime, or the actual nuScenes database. It operates as a static schema-vs-schema dry run, making it reproducible in any CI environment.

### **Checks Performed**

#### Radar (6 checks)

| ID | Check | Description |
|---|---|---|
| R-01 | Detection-centric profile | `RadDetection` struct exists with per-detection xyz, velocity, RCS, dyn_prop. |
| R-02 | Per-detection velocity | Cartesian `velocity_xyz` (preferred) + scalar `v_r_mps` (fallback), both with `has_*` guards. |
| R-03 | Ego-compensated velocity | `velocity_comp_xyz` field for ego-motion-compensated velocity. |
| R-04 | Dynamic property enum | `RadDynProp` covers all 7 nuScenes values (UNKNOWN through STOPPED). |
| R-05 | Per-detection RCS | `rcs_dbm2` field in dBm^2 with `has_rcs_dbm2` guard. |
| R-06 | Sensor type enum | `RadSensorType` differentiates SHORT_RANGE, LONG_RANGE, IMAGING_4D, etc. |

#### DeepSense 6G Radar Tensor (6 checks)

| ID | Check | Description |
|---|---|---|
| T-01 | Tensor meta struct | `RadTensorMeta` exists with `axes`, `voxel_type`, `layout`, `physical_meaning`. |
| T-02 | Complex sample type | `SampleType.CF32` covers complex I/Q data. |
| T-03 | Channel axis | `RadTensorLayout.CH_FAST_SLOW` maps raw FMCW [Rx, samples, chirps]. |
| T-04 | MIMO antenna config | `num_tx`, `num_rx`, `num_virtual_channels` with `has_antenna_config` guard. |
| T-05 | Waveform params | `bandwidth_hz`, `center_freq_hz`, `samples_per_chirp`, `chirps_per_frame` with guard. |
| T-06 | Frame blob transport | `RadTensorFrame.hdr.blobs[]` carries the raw cube; size computable from axes and sample size. |

#### DeepSense 6G Vision (3 checks)

| ID | Check | Description |
|---|---|---|
| DV-05 | 360° rig roles | `RigRole` enum includes PANORAMIC and EQUIRECTANGULAR for 360° cameras. |
| DV-06 | Keyframe flag | `VisionFrame.is_key_frame` boolean (shared with nuScenes V-04). |
| DV-07 | Compression codec | `Codec` enum covers JPEG/H264/H265/AV1 for image transport. |

#### DeepSense 6G Lidar (2 checks)

| ID | Check | Description |
|---|---|---|
| DL-06 | Sensor wavelength | `LidarMeta.wavelength_nm` with `has_wavelength` guard (e.g., 865 nm for Ouster OS1). |
| DL-07 | Frame rate | `StreamMeta.nominal_rate_hz` covers 10–20 Hz lidar cadence. |

#### DeepSense 6G IMU (2 checks)

| ID | Check | Description |
|---|---|---|
| DI-01 | 6-axis sample | `ImuSample` with accel (Vec3) + gyro (Vec3) at 100 Hz. |
| DI-04 | Timestamp + sequence | `ImuSample.stamp` + `.seq` for fine-grained temporal ordering. |

#### DeepSense 6G GPS (2 checks, 2 deferred)

| ID | Check | Description |
|---|---|---|
| DG-01 | Position | `GeoPose.lat_deg/lon_deg/alt_m` for GPS-RTK coordinates. |
| DG-04 | Covariance | `GeoPose.cov` for positional uncertainty (RTK <=1 cm). |
| DG-05 | GNSS quality | ⚠️ **Deferred.** DOP, fix type, satellite count require new `GnssQuality` struct. |
| DG-06 | Speed over ground | ⚠️ **Deferred.** No field on GeoPose for ground velocity. |

#### DeepSense 6G mmWave Beam (0/5, all deferred)

| ID | Check | Description |
|---|---|---|
| DB-01–05 | RF beam sensing | ❌ **Deferred.** Beam power vectors, codebook metadata, blockage state require new `rf_beam` profile (K-B1). |

#### Vision (5 checks)

| ID | Check | Description |
|---|---|---|
| V-01 | RigRole coverage | `RigRole` enum includes FRONT, FRONT_LEFT, FRONT_RIGHT, BACK, BACK_LEFT, BACK_RIGHT. |
| V-02 | Pre-rectified images | Normative prose documents `dist = NONE` with `model = PINHOLE` semantics. |
| V-03 | Image dimensions | `CamIntrinsics.width` / `height` are REQUIRED; zero values are malformed. |
| V-04 | Keyframe flag | `VisionFrame.is_key_frame` boolean. |
| V-05 | Quaternion reorder | §2 table maps nuScenes `(w,x,y,z)` to SpatialDDS `(x,y,z,w)`. |

#### Lidar (6 checks)

| ID | Check | Description |
|---|---|---|
| L-01 | BIN_INTERLEAVED encoding | `CloudEncoding` value for raw interleaved binary with normative record layout table. |
| L-02 | Per-point timestamps | `PointLayout.XYZ_I_R_T` and `XYZ_I_R_T_N` with normative prose for the `t` field. |
| L-03 | Metadata guards | `LidarMeta` uses `has_range_limits`, `has_horiz_fov`, `has_vert_fov` guards. |
| L-04 | Timestamp presence flag | `LidarFrame.has_per_point_timestamps` signals per-point timing in the blob. |
| L-05 | t_end computation | Normative guidance for computing `t_end` from `t_start + 1/rate_hz` or `max(point.t)`. |
| L-06 | Ring field | `PointLayout.XYZ_I_R` carries ring as `uint16`. |

#### Semantics (5 checks)

| ID | Check | Description |
|---|---|---|
| S-01 | Size convention | Normative: `size[0]` = width (X), `size[1]` = height (Z), `size[2]` = depth (Y). nuScenes `(w,l,h)` -> `(w,h,l)` mapping documented. |
| S-02 | Attributes | `Detection3D.attributes` as `sequence<MetaKV, 8>` with `has_attributes` guard. |
| S-03 | Visibility | `Detection3D.visibility` float [0..1] with `has_visibility` guard. |
| S-04 | Evidence counts | `num_lidar_pts` + `num_radar_pts` with `has_num_pts` guard. |
| S-05 | Quaternion reorder | §2 table covers annotation quaternion conversion. |

#### Common / Core (5 checks)

| ID | Check | Description |
|---|---|---|
| C-01 | Quaternion table | §2 convention table covering GeoPose, ROS 2, nuScenes, Eigen, Unity, Unreal, OpenXR, glTF. |
| C-02 | FQN guidance | `FrameRef { uuid, fqn }` semantics documented; UUID is authoritative. |
| C-03 | Local-frame coverage | §3.3.4 covers local-only deployments. |
| C-04 | has_* pattern consistency | All new optional fields use the `has_*` guard pattern uniformly. |
| C-05 | Sequence bounds | Standard bounds table: SZ_MEDIUM (2048), SZ_SMALL (256), SZ_XL (32768), SZ_LARGE (8192). |

### **Results**

All 33 nuScenes checks and all non-deferred DeepSense 6G checks pass against the SpatialDDS 1.5 specification as published. DeepSense 6G mmWave beam and GNSS quality checks are deferred pending new profile design.

**nuScenes Conformance (perception-to-semantics pipeline):**

| Modality | Checks | Pass | Remaining Gaps |
|---|---|---|---|
| Radar (detections) | 6 | 6 | 0 |
| Radar (tensor) | 6 | 6 | 0 |
| Vision | 5 | 5 | 0 |
| Lidar | 6 | 6 | 0 |
| Semantics | 5 | 5 | 0 |
| Common / Core | 5 | 5 | 0 |
| **Total** | **33** | **33** | **0** |

**DeepSense 6G Conformance (signal-to-perception pipeline):**

| Modality | Checks | Pass | Gap | Missing | Notes |
|---|---|---|---|---|---|
| Radar (tensor) | 8 | 8 | 0 | 0 | Shared with nuScenes T-01–T-06 + extras |
| Vision | 7 | 7 | 0 | 0 | Includes 360° rig roles (K-V1) |
| Lidar | 7 | 7 | 0 | 0 | Includes wavelength (K-L1) |
| IMU | 4 | 4 | 0 | 0 | — |
| GPS | 6 | 4 | 2 | 0 | GNSS quality deferred (K-G1) |
| mmWave Beam | 5 | 0 | 0 | 5 | RF beam profile deferred (K-B1) |
| Semantics | 4 | 3 | 1 | 0 | Beam labels deferred |
| **Total** | **41** | **33** | **3** | **5** | **80% coverage** |

### **Spec Changes Informed by Testing**

The conformance harness was first run against an early draft of SpatialDDS 1.5, which produced 29 gaps. The following normative changes were made in response:

| Change | Profile | Origin |
|---|---|---|
| Complete radar profile replacement: tensor-based -> detection-centric (`RadDetection`, `RadDetectionSet`, `RadSensorMeta`) | Radar | R-01 through R-06 |
| Radar tensor path restored: `RadTensorMeta` / `RadTensorFrame` and `RadTensorLayout` | Radar | T-01 through T-06 |
| `RigRole` enum expanded with FRONT, FRONT_LEFT, FRONT_RIGHT, BACK, BACK_LEFT, BACK_RIGHT | Vision | V-01 |
| Normative prose for `dist = NONE` pre-rectified image semantics | Vision | V-02 |
| `CamIntrinsics.width` / `height` made REQUIRED with malformed-sample guidance | Vision | V-03 |
| `VisionFrame.is_key_frame` boolean added | Vision | V-04 |
| `CloudEncoding.BIN_INTERLEAVED` added with normative record layout table | Lidar | L-01 |
| `PointLayout.XYZ_I_R_T` and `XYZ_I_R_T_N` added with per-point timestamp prose | Lidar | L-02, L-04 |
| `has_range_limits`, `has_horiz_fov`, `has_vert_fov` guards added to `LidarMeta` | Lidar | L-03 |
| `t_end` computation guidance for spinning lidars | Lidar | L-05 |
| Size convention normative prose with nuScenes mapping | Semantics | S-01 |
| `Detection3D.attributes`, `.visibility`, `.num_lidar_pts`, `.num_radar_pts` added | Semantics | S-02, S-03, S-04 |
| §2 quaternion convention table with ecosystem mappings | Common | C-01, V-05, S-05 |
| `FrameRef` FQN guidance and local-frame coverage section | Common | C-02, C-03 |
| `RigRole.PANORAMIC` and `EQUIRECTANGULAR` added for 360° cameras | Vision | DV-05 |
| `LidarMeta.has_wavelength` / `wavelength_nm` added | Lidar | DL-06 |

### **Reproducing the Test**

The conformance harness is a single self-contained Python 3 script (`scripts/nuscenes_harness_v2.py`) with no external dependencies. To run:

```bash
python3 scripts/nuscenes_harness_v2.py
```

The script mirrors the IDL structures from this specification as Python dictionaries and checks them against the nuScenes schema. It produces a plain-text report and a JSON results file. No DDS runtime, network access, or nuScenes database download is required.

Implementers are encouraged to adapt the harness for additional reference datasets (e.g., Waymo Open, KITTI, Argoverse 2) to validate coverage for sensor configurations and annotation conventions not present in nuScenes.

A companion conformance harness (`scripts/deepsense6g_harness_v1.py`) validates SpatialDDS 1.5 against the DeepSense 6G multi-modal sensing and communication dataset. It covers 41 checks across 7 modalities (radar tensor, vision, lidar, IMU, GPS, mmWave beam, semantics). To run:

```bash
python3 scripts/deepsense6g_harness_v1.py
```

The DeepSense harness is complementary to the nuScenes harness: nuScenes validates the perception-to-semantics pipeline; DeepSense validates signal-to-perception coverage and identifies ISAC-specific modalities (mmWave beam power vectors, GNSS quality metadata) that are under separate discussion for future SpatialDDS extensions. See Appendix K for the full DeepSense 6G conformance analysis.

### **Limitations**

This testing validates schema expressiveness -- whether every nuScenes field has a lossless SpatialDDS mapping. It does not validate:

- **Wire interoperability** -- actual DDS serialization/deserialization round-trips.
- **Performance** -- throughput, latency, or memory footprint under real sensor loads.
- **Semantic correctness** -- whether a particular producer's mapping preserves the intended meaning of each field.
- **Multi-dataset coverage** -- datasets with different sensor configurations (e.g., solid-state lidar, event cameras, ultrasonic sensors) may surface additional gaps.

These areas are appropriate targets for future conformance work.
