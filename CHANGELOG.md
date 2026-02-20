# Changelog

| Version | Date       | Key Changes |
|---------|------------|-------------|
| 1.5     | TBD        | Initialized work-in-progress 1.5 specification structure. |
| 1.4     | 2026-02-07 | Finalized 1.4 draft text and examples; regenerated full spec. |
| 1.3     | 2025-10-03 | Documented SpatialDDS URIs and ABNF; added frame transforms (#30) and bounding volumes (#29); new HTTP-capable discovery model; general restructuring. |
| 1.2     | 2025-09-14 | Added anchor manifest example, refined schema, and standardized bounding-box arrays. |
| 1.1     | 2025-07-01 | Initial concept release of the SpatialDDS specification. |

## Version 1.5 - TBD

- Core and IDL: added `FramedPose`, redesigned `NodeGeo`, expanded pose-graph/mapping/event types, and clarified core patterns (covariance, ordering, optionality).
- Discovery/URIs/Manifests: structured CoverageQuery, defined pagination and topic/QoS conventions, added security + resolver rules, and formalized manifest schema and resolution.
- Extensions: major updates across sensing (vision/lidar/radar, including tensor + detection paths), plus new Mapping and Spatial Events extensions; provisional Neural/Agent/rf_beam expanded.
- Conformance and examples: added nuScenes + DeepSense harnesses, refreshed Appendix I, and updated examples/consistency across appendices.
- Documentation polish: new conceptual overview, improved profiles/footnotes/tables, and broad cleanup of formatting and consistency issues.
- Mapping extension updates: added RANGE constraints in `mapping::EdgeType`, RANGE_COARSE alignment method, and S3E conformance coverage in Appendix I.
- Appendix I framing: updated to a three-dataset conformance suite (nuScenes, DeepSense 6G, S3E), moved the reproducing section to follow I.3, and clarified the manual S3E analysis and updated limitations.
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
