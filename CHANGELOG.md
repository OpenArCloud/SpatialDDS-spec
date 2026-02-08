# Changelog

| Version | Date       | Key Changes |
|---------|------------|-------------|
| 1.5     | TBD        | Initialized work-in-progress 1.5 specification structure. |
| 1.4     | 2026-02-07 | Finalized 1.4 draft text and examples; regenerated full spec. |
| 1.3     | 2025-10-03 | Documented SpatialDDS URIs and ABNF; added frame transforms (#30) and bounding volumes (#29); new HTTP-capable discovery model; general restructuring. |
| 1.2     | 2025-09-14 | Added anchor manifest example, refined schema, and standardized bounding-box arrays. |
| 1.1     | 2025-07-01 | Initial concept release of the SpatialDDS specification. |

## Version 1.5 - TBD

- Initialized directories and stub documents for the 1.5 drafting cycle.
- Added structured `CoverageFilter` and deprecated freeform `expr` for discovery queries.
- Defined pagination, announce lifecycle, and well-known discovery topic names/QoS.
- Added bootstrap manifest and DNS-SD / `.well-known` bindings for Layer 1 discovery.
- Added normative `spatial.manifest@1.5` schema with type-specific blocks and JSON Schema.
- Added normative blob reassembly guidance for `BlobChunk` delivery.
- Replaced the radar extension with a detection-centric profile (`RadSensorMeta`, expanded `RadDetection`, `RadDetectionSet`) and removed tensor-centric structs.
- Updated vision, lidar, and semantics profiles with detection-centric and dataset-aligned fields (RigRole expansion, BIN_INTERLEAVED, per-point timestamps, Detection3D attributes/visibility/evidence) plus supporting normative guidance.
- Added Appendix I documenting dataset conformance testing and the resulting profile changes.

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
