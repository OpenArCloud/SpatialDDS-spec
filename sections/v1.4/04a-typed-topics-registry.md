## 4.7 Topic Identity (Normative)

SpatialDDS unifies topic naming, discovery metadata, and QoS registration so implementations can interoperate without reinterpreting payload bytes.

### Naming
Topics follow the canonical path:
```
spatialdds/<domain>/<stream>/<type>/<version>
```

* `<domain>` — logical application domain (for example `perception`, `mapping`, `ar`).
* `<stream>` — producer-defined stream identifier (for example `cam_front`, `radar_1`).
* `<type>` — registered topic type token.
* `<version>` — semantic guard such as `v1`.

Example: `spatialdds/perception/cam_front/video_frame/v1`.

### Metadata
Each advertised topic **MUST** include, in discovery messages and manifests:

* `type`
* `version`
* `qos_profile`

These keys allow consumers to evaluate compatibility without opening payloads.

### QoS
SpatialDDS defines a compact catalog of named QoS profiles aligned to typical sensor and mapping workloads (for example `VIDEO_LIVE`, `GEOM_TILE`, `RADAR_RT`).
Profiles describe **relative** latency/reliability trade-offs and are cataloged in Appendix B. Implementations map the names onto their transport or DDS configuration.

### Registered Types (Informative extract)

| Type token       | Typical payload                                  |
|------------------|---------------------------------------------------|
| `geometry_tile`  | 3D tiles, GLB, 3D Tiles content                   |
| `video_frame`    | Encoded frames (AV1/H.264/JPEG/etc.)              |
| `radar_tensor`   | N-D tensors, fixed/float layouts                  |
| `seg_mask`       | Binary/RLE/PNG segmentation masks                 |
| `desc_array`     | Feature descriptor batches (e.g., ORB, NetVLAD)   |

Extensions may register additional types using the same pattern.

### Conformance

* A topic advertises exactly one registered `type` token.
* Producers keep `type`, `version`, and `qos_profile` consistent across discovery, manifests, and live transport.
* Brokers and routers MAY use `(topic, qos_profile)` to segment traffic but no on-wire framing changes are introduced.
