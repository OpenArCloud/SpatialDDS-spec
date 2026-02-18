## **Appendix B: Discovery Profile**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*

SpatialDDS Discovery operates at two levels. The **DDS binding** (defined by the IDL types below) provides on-bus announce, query, and response topics for low-latency discovery within a DDS domain. The **HTTP binding** (§3.3.0, HTTP Discovery Search Binding) provides an equivalent spatial query interface over HTTPS for clients that have not yet joined a DDS domain. Both bindings share the same coverage semantics (§3.3.4) and return compatible result types — the DDS binding returns `Announce` samples in `CoverageResponse`, while the HTTP binding returns service manifests (§8.2.3) that carry the same information plus DDS connection hints. Higher-level service catalogues (such as OSCP's Spatial Service Discovery Systems) may store, index, or federate SpatialDDS manifests and URIs on top of either binding.

See **Appendix F.X (Discovery Query Expression)** for the normative grammar used by `CoverageQuery.expr` filters.

```idl
{{include:idl/v1.5/discovery.idl}}
```
