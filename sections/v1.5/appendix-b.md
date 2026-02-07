## **Appendix B: Discovery Profile**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*

SpatialDDS Discovery is a bus-level mechanism: it describes nodes, topics,
coverage, capabilities, and URIs that exist on the DDS fabric itself.
Higher-level service catalogues (such as OSCP's Spatial Service Discovery
Systems) are expected to run on top of SpatialDDS. They may store, index,
or federate SpatialDDS manifests and URIs, but they are application-layer
services and do not replace the on-bus discovery topics defined here.

See **Appendix F.X (Discovery Query Expression)** for the normative grammar used by `CoverageQuery.expr` filters.

```idl
{{include:idl/v1.5/discovery.idl}}
```

