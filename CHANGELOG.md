# Changelog

| Version | Date       | Key Changes |
|---------|------------|-------------|
| 1.6     | 2026-07-23 | Added PlannedTrajectory and EntityBinding to core; extended CovKind (POSE6_TWIST6, ROT3); coverage_window in CoverageElement; new conventions for enum serialization, time semantics, bbox ordering, schema stability, topic version stability, spatial privacy; expr deprecation sunset for 2.0; DNS authority lifecycle and resolution-failure fallback chain; demoted Neural and Agent to informative examples; reframed Appendix H as a world-model grounding narrative; new Appendix K (IDL package layout); selective per-profile minor bumps. |
| 1.5     | 2026-04-29 | Finalized 1.5: added FramedPose/NodeGeo redesign, Mapping and Spatial Events extensions, geospatial DNS-SD discovery, restored HTTP discovery binding, four-dataset conformance suite (nuScenes/DeepSense 6G/S3E/ScanNet), and provisional rf_beam profile. |
| 1.4     | 2026-02-07 | Finalized 1.4 draft text and examples; regenerated full spec. |
| 1.3     | 2025-10-03 | Documented SpatialDDS URIs and ABNF; added frame transforms (#30) and bounding volumes (#29); new HTTP-capable discovery model; general restructuring. |
| 1.2     | 2025-09-14 | Added anchor manifest example, refined schema, and standardized bounding-box arrays. |
| 1.1     | 2025-07-01 | Initial concept release of the SpatialDDS specification. |

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
