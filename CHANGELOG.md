# Changelog

| Version | Date       | Key Changes |
|---------|------------|-------------|
| 1.7     | 2026-08-23 | **Breaking** (pre-adoption instability clause, §3.1): `Time.sec` widened to int64; compound `@key` on `Node`/`Edge` and `mapping::Edge`; `GeoPose` orientation fixed to the local ENU tangent frame (removed `frame_kind`/`frame_ref`, `GeoFrameKind`); `TileMeta` uses a single `Aabb3 aabb` (removed `min_xyz`/`max_xyz`/`lod`); removed `BlobChunk.last`; `CoverageResponse` returns compact `ServiceSummary` rows; `caps.features` is now `sequence<string>` (removed `FeatureFlag`); removed `ProfileSupport.preferred`, `CoverageElement.type`, `CoverageQuery.expr` (and Appendix F.X). Policy: single-identifier syntax `spatial.<profile>/MAJOR.MINOR`; all modules unified to `/1.7`; consolidated `/.well-known/spatialdds/{bootstrap,resolver,search}` namespace; bootstrap auth via `auth_hint`; Appendix G promoted to Normative. Findings batch 2 (draft rev): breaking sequence-bound reductions (`BlobChunk.data`, `KeyframeFeatures.descriptors` → 65535); additive fields across discovery/semantics/vision/vio/events/common; new QoS profiles and registry rows. |
| 1.6     | 2026-07-23 | Added PlannedTrajectory and EntityBinding to core; extended CovKind (POSE6_TWIST6, ROT3); coverage_window in CoverageElement; new conventions for enum serialization, time semantics, bbox ordering, schema stability, topic version stability, spatial privacy; expr deprecation sunset for 2.0; DNS authority lifecycle and resolution-failure fallback chain; demoted Neural and Agent to informative examples; reframed Appendix H as a world-model grounding narrative; new Appendix K (IDL package layout); selective per-profile minor bumps. |
| 1.5     | 2026-04-29 | Finalized 1.5: added FramedPose/NodeGeo redesign, Mapping and Spatial Events extensions, geospatial DNS-SD discovery, restored HTTP discovery binding, four-dataset conformance suite (nuScenes/DeepSense 6G/S3E/ScanNet), and provisional rf_beam profile. |
| 1.4     | 2026-02-07 | Finalized 1.4 draft text and examples; regenerated full spec. |
| 1.3     | 2025-10-03 | Documented SpatialDDS URIs and ABNF; added frame transforms (#30) and bounding volumes (#29); new HTTP-capable discovery model; general restructuring. |
| 1.2     | 2025-09-14 | Added anchor manifest example, refined schema, and standardized bounding-box arrays. |
| 1.1     | 2025-07-01 | Initial concept release of the SpatialDDS specification. |

## Version 1.7 - 2026-08-23

Backward compatibility with 1.6 is **not** preserved. Per the pre-adoption
instability clause (§3.1), MINOR revisions in the 1.x series MAY include
breaking schema or wire changes. Topic names retain the `/v1` segment.

### Breaking (wire)
- `builtin::Time.sec`: `int32` → `int64` (no year-2038 limit).
- `core::Node` / `core::Edge`: instance key is now compound (`map_id`, id).
- `mapping::Edge`: instance key is now compound (`map_id`, `edge_id`),
  aligning with `core::Node`/`Edge`.
- `core::GeoPose`: removed `frame_kind` and `frame_ref`; the quaternion is
  fixed to the local ENU tangent frame at the encoded position (OGC GeoPose).
  Removed `enum GeoFrameKind`.
- `core::TileMeta`: replaced `min_xyz`/`max_xyz` with a single `Aabb3 aabb`;
  removed `lod` (redundant with `key.level`).
- `core::BlobChunk`: removed `last`.
- `disco::CoverageResponse`: returns `sequence<ServiceSummary>` (new compact
  row type) instead of `sequence<Announce>`.
- `disco::Capabilities.features`: `sequence<FeatureFlag>` → `sequence<string>`;
  removed `struct FeatureFlag`.
- `disco::ProfileSupport`: removed `preferred`; `name` now carries the module
  family (e.g., `"spatial.core"`).
- `disco::CoverageElement`: removed `type` (derivable from `has_bbox`/`has_aabb`).
- `disco::CoverageQuery`: removed `expr`; deleted Appendix F.X (query
  expression grammar). Use `filter` exclusively.

### Policy
- Single identifier syntax: `spatial.<profile>/MAJOR.MINOR` everywhere; the
  dual `name@MAJOR.MINOR` form is retired.
- All modules version together with the spec; every `MODULE_ID` and
  `schema_version` in 1.7 is `spatial.<profile>/1.7`.
- Added the pre-adoption instability clause (§3.1).
- Consolidated the well-known namespace to a single RFC 8615 registration:
  `/.well-known/spatialdds/{bootstrap,resolver,search}`.
- Bootstrap authentication unified with `auth_hint` (removed the `auth.method`
  enum).
- Appendix G (Frame Identifiers) promoted from Informative to Normative.
- Manifest `profile` MUST match `spatial.manifest/1.<minor>` with `<minor>` ≥ 7.

### Findings batch 2 (draft rev)

Implementation findings from the demo repo (`spatialdds-1.7-findings-update-plan.md`).

Breaking (wire):
- `core::BlobChunk.data`: sequence bound `262144` → `65535` (binding-compatible;
  §3.2). Sweep confirms no other sequence bound in Appendices A–D or provisional
  IDL exceeds 65535.
- `slam_frontend::KeyframeFeatures.descriptors`: bound `1048576` → `65535`;
  larger descriptor sets ride blob transfer (`BlobRef` + `BlobChunk`).

Additive (IDL):
- `common::MetaKV`: added `sequence<KV, 64> entries` (typed extension rows) and a
  new `common::KV` struct. Typed-first extension rule added (Appendix A).
- `semantics::Detection3D`: added `has_velocity` + `Vec3 velocity`.
- Finding 5 (2D detections) resolved by *registration*, not addition: the existing
  labelled, scored, image-space `semantics::Detection2DSet` is now registered as
  topic type `detection2d`. No new type was added.
- `disco::ServiceKind`: appended `SENSING`, `INFRASTRUCTURE`, `FUSION`.
- `events::EventType`: appended `PREDICTED_CONFLICT`; `SpatialEvent` added
  `participant_ids`. Prediction semantics normative note added.
- `vio::ImuSample`: added `has_accel_cov`/`accel_cov` + `has_gyro_cov`/`gyro_cov`
  (`core::CovMatrix`).
- `disco::CoverageElement`: added `has_circle` / `circle_center[3]` /
  `circle_radius_m`. Circle coverage semantics added (§3.3.4).
- `disco::Announce`: added `coverage_source_ids` (empty = self-asserted). Derived
  coverage semantics added (§3.3.4).
- `sensing.common::Codec`: appended `PNG`.

Non-IDL:
- §3.3.3 QoS table: renamed "Typical Deadline" → "Deadline"; Deadline now normative
  and specified only on periodic stream profiles (sporadic/latched/request-reply =
  "—"); `RADAR_RT` reliability "Partial" → "Best-effort" (no partial-reliability
  kind in DDS); added normative QoS-surface and request/offered notes; added five
  profiles: `DET_RT`, `LIDAR_RT`, `IMU_RT`, `SENSOR_META`, `ANCHOR_DELTA`.
- §3.3.2 registry: added ten rows (`framed_pose`, `detection3d`, `detection2d`,
  `lidar_frame`, `lidar_meta`, `radar_tensor_meta`, `video_meta`, `rf_beam_meta`,
  `imu_sample`, `anchor_delta`) and a registry-completeness rule; new registry
  gate.
- Provisional IDL relocated: `examples/rf_beam_example.idl` →
  `provisional/rf_beam.idl`; `examples/radio_example.idl` → `provisional/radio.idl`
  (Appendix E, Appendix K, validator globs updated).
- Appendix I: wire-level conformance suite SHOULD verify per-profile endpoint
  matching between two independently configured participants.

### Batch 2 follow-up (draft rev)

Decision resolutions from `spatialdds-1.7-batch2-followup.md`.

- §3.3.3 QoS table completed to the full normative surface: added **Durability**
  and **History** columns, populated for every profile row (no policy is
  specified only in prose). `RADAR_RT` deadline widened to admit 10–20 Hz radar
  (deadline is now normative; values must admit the profile's class):
  20 ms → 100 ms. `RADIO_SCAN_RT` deadline → "—" (scan cycles are seconds-scale;
  sporadic). `EVENT_RT` History is `KeepLast(64)` (existing events prose wins over
  the table default).
- §3.3.2 registry: added `tile_meta` (`core::TileMeta`), `rad_sensor_meta`
  (`sensing::rad::RadSensorMeta`), and `radio_sensor_meta` (provisional
  `sensing::radio::RadioSensorMeta`) — all QoS `SENSOR_META`. Registry gate
  coverage is now **fatal** (underscore/case-insensitive matching; Appendix E
  examples excluded).
- Topic-construction gate added as a CI job (advisory; requires the CycloneDDS
  IDL Python backend to run, otherwise skips).
- Informative fixes: `examples/agent_example.idl` `TaskType.MAP` → `MAPPING`
  (reserved word); `examples/` re-added to IDL validation scope. Appendix I S3E
  `ServiceKind.SLAM` → `MAPPING` (the enum is unchanged).

### Inventory-driven type additions (batch 3, draft rev)

Resolves `spatialdds-1.7-batch3-brief.md` — spec homes for two demo-owned type
families (`OpenArCloud/SpatialDDS-demo`), hardened to spec conventions. All
**Additive** (new structs; no existing declaration touched).

- `spatial.argeo`: added the VPS request/response pair — `VpsRequest`,
  `VpsResponse`, `QualityRequirements`, and enum `VpsStatus`. Query imagery
  travels by `BlobRef` (never inline bytes); request/response correlate by
  `query_id`; the response's pose rides in a `NodeGeo`.
- `spatial.semantics`: added `FusedTrack` / `FusedTrackSet` for cross-source
  fused tracks with per-source provenance (`source_operators`,
  `source_modalities`, `source_count`).
- §3.3.2 registry: `vps_query` now names `argeo::VpsRequest`; added
  `vps_response` (`argeo::VpsResponse`) and `fused_track`
  (`semantics::FusedTrackSet`, QoS `DET_RT`). Every existing registry row was
  annotated with its IDL type, and the registry gate now **fatally** requires
  every row to name a resolvable IDL type (a typeless row is a spec defect).
- §3.3 bootstrap: on-bus bootstrap exchanges noted as deployment-specific, not
  standardized. Future Directions: on-bus content catalog query parked as an
  open design question (deliberately not added in 1.7).

### Batch 3 follow-up (draft rev)

- `argeo::VpsRequest`: `quality_requirements` is now presence-guarded
  (`has_quality_requirements`); absence means the service's default accuracy
  requirements apply (§2.2 — no sentinel-zero requirements).
- §3.3.2 registry: dropped the `tile_meta` row — `core::TileMeta` is registered
  canonically as `geometry_tile`; `tile_meta` existed only within the 1.7 draft
  window. The registry gate now enforces one normative row per IDL type (alias
  rows excepted; `seg_mask` is marked an alias of `video_frame`'s
  `VisionFrame`).
- §3.3.2: agent-family rows (`agent_status`, `task_offer`, `task_assignment`)
  moved out of the normative registry into an "Informative Example
  Registrations" sub-table — they name types defined only in Appendix E
  examples and are outside the conformance surface; the gate checks only that
  they resolve.
- Added `gaps/2.0-considerations.md`: unify covariance representation
  (`CovMatrix` vs `Mat3x3`) — surveyed before 2.0, not patched in 1.7.

## Version 1.6 - 2026-07-23

### Core profile (spatial.core/1.6)
- Added `PlannedTrajectory` and `PlannedWaypoint` for cooperative planning and intent sharing (registered type `planned_trajectory`).
- Added `EntityBinding` and `ComponentRef` for cross-topic entity correlation (registered type `entity_binding`).

### Sensing common (spatial.sensing.common/1.6)
- Extended `CovarianceType` with `COV_ROT3` (orientation-only) and `COV_POSE6_TWIST6` (12×12 pose + velocity) cases.
- Added `Mat12x12` typedef and corresponding `CovMatrix` union cases.

### Discovery (spatial.discovery/1.6)
- Added `CoverageElement.has_coverage_window` / `coverage_window_start` / `coverage_window_end` for time-varying coverage.

### FrameRef axis convention (coord_convention patch)
- Added `CoordConvention` enum (`ENU`, `CV`, `GRAPHICS`, `UNITY_LH`, `NED`, `OTHER`) and extended `FrameRef` with optional `has_coord_convention` / `coord_convention` fields (APPENDABLE — backward compatible).
- New §2.12 Coordinate Axis Convention (Normative): convention table, default-ENU assumption when absent, chaining rule (no cross-convention chains without axis swap), producer guidance for CV / GRAPHICS / Unity / NED / ENU bridges, MetaKV escape hatch for `OTHER`.
- Motivated by the OpenVPS (CV) ↔ spARcl WebXR (GRAPHICS) ↔ GeoPose (ENU) integration debugging episode.
- Appendix I gains C-06 (nuScenes ego-ENU + camera-CV) and LC-06 (LaMAR hloc-CV + HoloLens-GRAPHICS + GT-ENU) coord-convention conformance checks; totals update to nuScenes 28, LaMAR 71, 5-dataset total 216.

### New normative conventions (§2)
- §2.7.6 Spatial Privacy (Normative Guidance) — pose quantization, trajectory truncation, pseudonymization, consent.
- §2.8 Enum Serialization — JSON identifier strings; CDR uses integer `@value`.
- §2.9 Time Semantics — UTC POSIX time; clock-source `MetaKV` keys.
- §2.10 Bounding Box Ordering — GeoJSON `[lon, lat, ...]` for geographic, `Aabb3 {min_xyz, max_xyz}` for local.
- §2.11 Schema Stability Signaling — `provisional` flag in `MetaKV` and `caps.features`.
- §3.3.1 Topic Version Stability — `/v1` follows profile MAJOR, not MINOR.

### Other normative changes
- §2.7.5 DDS Security wording clarified to allow OAuth2/OIDC, SPIFFE/SPIRE, mutual TLS via `auth_hint`.
- §7.5.6 Authority Expiry / Resolution Failure — cache → content-addressed → graceful-degradation fallback chain.
- `CoverageQuery.expr` deprecation now scheduled for **removal in 2.0**; new implementations MUST use `filter` exclusively.
- `NavSatStatus` registered as type `navsat_status` in §3.3.2; producers SHOULD include a `TopicMeta` entry.

### Conformance — Appendix I.5 LaMAR expansion
- Replaced the 22-check radio-only LaMAR section with a 70-check multi-device version covering HoloLens 2 (vision + ToF depth + IR), iPhone/iPad (vision + LiDAR depth), NavVis scanner (multi-camera + lidar mesh), IMU, poses & trajectories, multi-session Anchors alignment (7 checks: GeoAnchor, AnchorSet, scan-to-scan, sequence-to-scan, year-long stability, refinement lifecycle), Discovery in multi-device context (5 checks: heterogeneous announcements, coverage, manifests), Cross-Device Localization (5 checks).
- The original 22 radio checks (Radio Profile Coverage / Discovery + QoS / Interop + Privacy) are retained verbatim with prefix renames (`LD-*` → `LRD-*`, `LP-*` → `LRP-*`) to avoid ID collisions with the new HoloLens-Depth and Phone-Vision sections.
- Reaffirmed that the original LM-1 gap (no first-class radio fingerprint type) is closed by the provisional `sensing.radio` profile in Appendix E.
- Surfaced 6 deferred items (rolling-shutter timing model, per-frame gravity vector, visual-overlap score, CSI/CIR first-class transport, multi-band coexistence metadata, plus rolling-shutter readout direction) in the results scorecard.

### Strategic / informative changes
- Neural extension demoted to **Informative Example** (Appendix E); removed from Profile Matrix.
- Agent extension demoted to **Informative Example** (Appendix E); removed from Profile Matrix.
- Appendix H replaced with **"SpatialDDS as a Grounding Layer for World Models"** — H.1 Grounding Problem, H.2 Integration Patterns (MCAP/Gymnasium/inference bridges), H.3 What SpatialDDS Does Not Do, H.4 Factor Graphs and Scene Graphs.
- §4 Operational Scenarios reframed; long-form examples remain in Appendix D and Appendix I dataset walkthroughs.
- Appendix I gains a Scope and Limitations preface and a Deferred column on every results table.
- New **Appendix K: IDL Package Layout (Informative)**.
- §6 Future Directions adds wire-level interop testing, transport-agnostic semantic layer, factor-graph interchange, and "Bridges to External Ecosystems" (implemented: MCAP, ROS 2, MQTT, WebSocket; planned: Gymnasium). Appendix H.2 mirrors the bridge list with a corresponding IoT/edge MQTT integration pattern.

### Versioning model
- Selective per-profile minor bumps: only profiles whose IDL changed (`core`, `sensing.common`, `discovery`, `manifest`) move to `/1.6`. All others retain `/1.5`. Topic names remain `/v1` per §3.3.1.

## Version 1.5 - 2026-04-29

- Core and IDL: added `FramedPose`, redesigned `NodeGeo`, expanded pose-graph/mapping/event types, and clarified core patterns (covariance, ordering, optionality).
- Discovery/URIs/Manifests: structured CoverageQuery, defined pagination and topic/QoS conventions, added security + resolver rules, and formalized manifest schema and resolution.
- Extensions: major updates across sensing (vision/lidar/radar, including tensor + detection paths), plus new Mapping and Spatial Events extensions; provisional Neural/Agent/rf_beam expanded.
- Conformance and examples: added nuScenes + DeepSense harnesses, refreshed Appendix I, and updated examples/consistency across appendices.
- Documentation polish: new conceptual overview, improved profiles/footnotes/tables, and broad cleanup of formatting and consistency issues.
- Mapping extension updates: added RANGE constraints in `mapping::EdgeType`, RANGE_COARSE alignment method, and S3E conformance coverage in Appendix I.
- Appendix I framing: updated to a four-dataset conformance suite (nuScenes, DeepSense 6G, S3E, ScanNet), moved the reproducing section to follow I.4, and clarified the manual S3E/ScanNet analysis and updated limitations.
- Vision + conformance: added `PixFormat.DEPTH16` with normative depth semantics and introduced ScanNet indoor RGB-D conformance (Spatial Events, mesh, instance segmentation, depth).
- Discovery bootstrap: added geospatial DNS-SD binding with geohash subdomains, updated bootstrap flow diagram, and referenced DNS-SD/SRV RFCs.
- Discovery HTTP binding: restored `/.well-known/spatialdds/search` with CoverageQuery-equivalent semantics, GET geohash convenience, and updated discovery layering and Appendix B preamble.
- Mapping/Events IDLs: added `mapping.idl` and `events.idl` files and isolated mapping/events enums in submodules to avoid IDL literal collisions.

## Version 1.4 - 2026-02-07

- Finalized 1.4 draft text and examples; regenerated full spec.

## Version 1.3 - 2025-10-03

- Created isolated directories for 1.3 documentation, IDL files, and manifests to enable parallel iteration and cleanup legacy content.
- Documented SpatialDDS URIs for stable identification and manifest discovery, including ABNF definitions for parser interoperability.
- Added optional `coverage.frame` metadata, manifest `transforms[]`, and support for both local and global frames to improve mobility scenarios (issue #30).
- Added optional 3D coverage volumes in manifests plus matching Discovery hints/queries for active volumetric filtering (issue #29).
- Introduced a revamped active Discovery model that now supports HTTP in addition to DDS-based transport.

## Version 1.2 - 2025-09-14

- Added anchor manifest example.
- Refined schema: aligned geopose fields, renamed `id` to `anchor_id`, moved timestamps to `stamp`.
- Standardized bounding-box arrays for geometry data.

## Version 1.1 - 2025-07-01

- Initial concept release of the SpatialDDS specification.
