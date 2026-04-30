## **Appendix G: Frame Identifiers (Informative Reference)**

SpatialDDS represents reference frames using the `FrameRef` structure:

The normative IDL for `FrameRef` resides in Appendix A (Core profile). This appendix is descriptive/informative and restates the usage guidance for reference frames.

```idl
struct FrameRef {
  string uuid;   // globally unique frame ID
  string fqn;    // normalized fully-qualified name, e.g. "earth-fixed/map/cam_front"
};
```

### UUID Rules
- `uuid` is authoritative for identity.
- `fqn` is an optional human-readable alias.
- Implementations MUST treat `uuid` uniqueness as the identity key.
- Deployments SHOULD establish well-known UUIDs for standard roots (e.g., `earth-fixed`, `map`, `body`) and document them for participants.

### Name and Hierarchy Rules
- `fqn` components are slash-delimited.
- Reserved roots include `earth-fixed`, `map`, `body`, `anchor`, `local`.
- A `FrameRef` DAG MUST be acyclic.

### Constructing FQNs from External Data (Informative)
Datasets and frameworks that use flat frame identifiers (e.g., nuScenes `calibrated_sensor.token`, ROS TF `frame_id`) must construct hierarchical FQNs when publishing to SpatialDDS.

Recommended approach:
1. Choose a root corresponding to the vehicle/robot body: `fqn = "ego"` or `fqn = "<vehicle_id>"`.
2. Append the sensor channel as a child: `fqn = "ego/cam_front"`, `fqn = "ego/lidar_top"`.
3. Use the original flat token as the `uuid` field.
4. For earth-fixed references, use the reserved root `fqn = "earth-fixed"`.

Example nuScenes mapping:
```
calibrated_sensor.token = "a1b2c3..."
sensor.channel = "CAM_FRONT"
-> FrameRef { uuid: "a1b2c3...", fqn: "ego/cam_front" }
```

### Manifest References
Manifest entries that refer to frames MUST use a `FrameRef` object rather than raw strings. Each manifest MAY define local frame aliases resolvable by `fqn`.

### Notes
Derived schemas (e.g. GeoPose, Anchors) SHALL refer to the Appendix A definition by reference and MUST NOT re-declare frame semantics. The conventions in §2.1 and the coverage/discovery rules in §3.3 reference this appendix for their frame requirements.
