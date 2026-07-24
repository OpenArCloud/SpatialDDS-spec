## **Appendix K: IDL Package Layout (Informative)**

The canonical file layout for SpatialDDS IDL is as follows. Implementations distributing the IDL as a package SHOULD preserve this directory structure so that `#include` paths and module hierarchies stay portable across projects.

```
spatialdds-idl/
├── types.idl              # Common typedefs (Time, Vec3, Mat3x3, Mat6x6, Mat12x12, etc.)
├── core.idl               # Core profile (PoseSE3, FramedPose, GeoPose, GeoAnchor,
│                          #   PlannedTrajectory, EntityBinding, BlobRef, etc.)
├── common.idl             # Sensing common (StreamMeta, FrameHeader,
│                          #   FrameQuality, MetaKV, etc.)
├── discovery.idl          # Discovery profile (Announce, CoverageQuery,
│                          #   CoverageResponse, TopicMeta, etc.)
├── anchors.idl            # Anchor registry (AnchorSet, AnchorDelta,
│                          #   AnchorEntry, etc.)
├── argeo.idl              # AR + Geo (NodeGeo, FrameTransform, etc.)
├── sensing/
│   ├── vision.idl         # Vision profile
│   ├── lidar.idl          # LiDAR profile
│   ├── rad.idl            # Radar profile (detection + tensor)
│   ├── vio.idl            # IMU / VIO profile
│   └── radio.idl          # Radio fingerprint profile (1.5+)
├── semantics.idl          # 2D/3D detection, classification
├── slam_frontend.idl      # SLAM front-end primitives
├── mapping.idl            # Mapping profile (MapMeta, MapAlignment, etc.)
├── events.idl             # Spatial events (SpatialEvent, ZoneState, etc.)
└── provisional/
    ├── rf_beam.idl         # RF beam profile (Provisional)
    ├── radio.idl           # Radio fingerprint examples (Provisional)
    ├── neural.idl          # Neural field examples (Informative only in 1.7)
    └── agent.idl           # Agent task coordination (Informative only in 1.7)
```

This repository organizes the v1.7 IDL files in a flat layout under `idl/v1.7/` (with `examples/` for provisional and informative profiles); both organizations are valid as long as `#include` paths and module declarations match.

Module namespacing follows the IDL `module` declarations:

- `spatial::core` → `core.idl`
- `spatial::common` → `common.idl` and `types.idl`
- `spatial::disco` → `discovery.idl`
- `spatial::sensing::vision` → `sensing/vision.idl`
- `spatial::sensing::lidar` → `sensing/lidar.idl`
- `spatial::sensing::rad` → `sensing/rad.idl`
- `spatial::sensing::radio` → `sensing/radio.idl`
- `spatial::vio` → `vio.idl`
- `spatial::semantics` → `semantics.idl`
- `spatial::slam_frontend` → `slam_frontend.idl`
- `spatial::argeo` → `argeo.idl`
- `spatial::anchors` → `anchors.idl`
- `spatial::mapping` → `mapping.idl`
- `spatial::events` → `events.idl`

Generated language bindings SHOULD preserve this module hierarchy:

- C++: `spatial::core::PoseSE3`
- Python: `spatial.core.PoseSE3`
- Rust: `spatial::core::PoseSE3`
