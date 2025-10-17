## **Appendix B: Discovery Profile**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*

```idl
{{include:idl/v1.4/discovery.idl}}
```

### Quaternion field deprecation

Legacy manifest fields named `q_wxyz` and scalar quaternion members (`qw`, `qx`, `qy`, `qz`) are deprecated as of SpatialDDS 1.4. Producers must emit orientations using the canonical GeoPose order `(x, y, z, w)` in a single `q_xyzw` array. Consumers shall continue to accept legacy encodings for the 1.4.x cycle, but they must convert them to canonical order, prefer `q_xyzw` when both are present, and issue a warning once per data stream.
