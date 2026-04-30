## **6. Future Directions**

While SpatialDDS establishes a practical baseline for real-time spatial computing, several areas invite further exploration:

* **Reference Implementations**  
  Open-source libraries and bridges to existing ecosystems (e.g., ROS 2, OpenXR, OGC APIs) would make it easier for developers to adopt SpatialDDS in robotics, AR, and twin platforms.  
* **Semantic Enrichment**  
  Extending beyond 2D/3D detections and spatial events, future work could align with ontologies, scene graphs, and complex event processing patterns to enable richer machine-readable semantics for AI world models and analytics.  
* **Neural Integration**  
  Provisional support for neural fields (NeRFs, Gaussian splats) could mature into a stable profile, ensuring consistent ways to stream and query neural representations across devices and services.  
* **Agent Interoperability**  
  The Agent extension's fleet coordination types (AgentStatus, TaskOffer, TaskAssignment, TaskHandoff) provide the typed data layer for multi-agent allocation. Future work could formalize common allocation patterns (auction-based, priority-queue, spatial-nearest) as reference implementations while keeping the protocol algorithm-agnostic.  
* **Collaborative Mapping**  
  The Mapping extension enables multi-agent map discovery, alignment, and lifecycle coordination. Future work could formalize map merge protocols, distributed optimization coordination, and standardized map quality benchmarks for fleet-scale deployments.  
* **Standards Alignment**  
  Ongoing coordination with OGC, Khronos, W3C, and GSMA initiatives will help ensure SpatialDDS complements existing geospatial, XR, and telecom standards rather than duplicating them.

### Wire-Level Interop Testing

Appendix I validates schema expressiveness through static conformance checks. Future revisions will add wire-level interoperability tests across at least two DDS implementations (CycloneDDS and Fast DDS minimum) to validate end-to-end publish/subscribe fidelity, QoS enforcement, and CDR encoding compatibility.

### Transport-Agnostic Semantic Layer

The spatial semantics defined by SpatialDDS — `FrameRef`-by-UUID, the Coverage Model, manifests, the URI scheme, and the dataset conformance methodology — are conceptually separable from the DDS transport binding. Future work will explore canonical bindings to additional transports (gRPC, MCAP files, Arrow Flight) while preserving the semantic layer unchanged. This would position SpatialDDS as an open semantic standard for spatial data, with DDS as the primary real-time binding and additional bindings for offline recording, cloud integration, and ML pipeline ingestion.

### Factor Graph Interchange

SpatialDDS's pose-graph types (`Node`, `Edge`, `MapMeta`) carry SLAM factor graph results. A dedicated factor graph interchange format — analogous to ONNX for neural networks — would enable portable exchange of arbitrary factor graph structures between solvers. SpatialDDS would reference such graphs via `BlobRef`, with `MapMeta` carrying optimization state metadata. This is a complementary effort, not a SpatialDDS extension.

### Bridges to AI/ML Ecosystems

Priority bridges for connecting SpatialDDS to ML training and inference pipelines:

- SpatialDDS ↔ MCAP recorder/replayer
- SpatialDDS ↔ Gymnasium observation space adapter
- SpatialDDS ↔ ROS 2 bridge (reference implementation)

These bridges are implementation artifacts, not spec extensions. They will be maintained in the SpatialDDS-demo repository.

Together, these directions point toward a future where SpatialDDS is not just a protocol but a foundation for an open, interoperable ecosystem of real-time world models.

We invite implementers, researchers, and standards bodies to explore SpatialDDS, contribute extensions, and help shape it into a shared backbone for real-time spatial computing and AI world models.
