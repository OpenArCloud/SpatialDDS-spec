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
* **On-bus content catalog query**  
  `ContentAnnounce` plus manifests and HTTP search cover content discovery today. Whether an on-bus, area-scoped catalog query/response joins them is an open design question; evidence from federation prototypes will inform it. Deliberately not added in 1.7.
* **Open World Model (`spatial.owm`)**  
  The provisional `spatial.owm/0.1` module (Appendix E) adds an identity-and-lifecycle layer over the discovery catalogue — entities with pose, type, and state that point back at catalogue content. It is independently versioned and exempt from the 1.x additive guarantee precisely so its shape can change while implementers exercise it. It leaves provisional status on two conditions, stated in its preamble: a second independent implementation, and relationship/identity semantics (per-edge basis, confidence, and retraction) landing as a resolved design rather than the reserved gap 0.1 deliberately leaves open.

### Queryable Coverage Response

Discovery today answers *who is here* through `Announce` and the Coverage Model, and `CoverageQuery` lets a consumer ask which providers cover a region. What a working federation prototype adds on top is a direct, area-scoped **coverage answer**: a responder returns per-provider coverage summaries for the queried region, merged with its local announce cache so that providers known only from their earlier announces — not merely those answering the query live — stay discoverable in the same response. A future coverage-response type must meet that requirement: from a single area-scoped query a consumer MUST be able to learn the coverage of every provider the responder knows about, queried and cached alike, with announce-only providers never silently dropped. This is recorded as a problem statement from that prototype; the on-bus message shape is deliberately deferred to a later batch and is explicitly not added as IDL in 1.8.

### Content Withdrawal (Typed Dispose)

Discovery can say a **service** has departed: `Depart` is `{service_id, stamp}`,
the right record for exactly one of the two publishable kinds. Nothing says a
**content** record has been withdrawn. `ContentAnnounce` carries no lifecycle
member, so the §2.14 terminal-sample-then-dispose convention has no typed
message to hang on for content, and a dispose cannot be journalled as a typed
message the way a publish can. A publishing endpoint in the SpatialDDS-web
prototype, needing to record a withdrawal with nothing typed to carry it,
resorts to an out-of-band MCAP metadata record it names `spatialdds-web:dispose`
— a convention of that one endpoint, not of the binding — which is evidence that
implementers are already forced to invent something here. A future revision
could add a withdrawal record that covers content as `Depart` covers services,
or a lifecycle member on the content record itself; the message shape is
deliberately deferred and is explicitly not added as IDL in 1.8. (Recorded from
the SpatialDDS-web publish work; the service-side reading gap it travelled with
— addressing the four-segment `spatialdds/discovery/depart/v1` well-known topic
over the web binding — is already resolved by N.3's short-topic rule and is not
part of this item.)

### Anchor Integrity Digest (`GeoAnchor.checksum`)

`GeoAnchor.checksum` is REQUIRED on the wire and its comment reads
`integrity/versioning`, but 1.8 defines **what it digests or in what form**
nowhere — not the IDL, not Appendix C, not the conformance suite. So no receiver
can verify it and no two publishers agree: a digest over the canonical JSON or
the XCDR2 bytes, including the checksum member or excluding it, before or after
the revision's appended members, are all equally "the checksum of the anchor
data". Two conventions already exist in deployed code — SpatialDDS-web's
authoring tool digests its input entry (recorded anchors), its record builders
digest the record's own canonical form with `checksum` emptied (published
anchors) — both correct, mutually incompatible, which is the evidence that the
field as specified cannot interoperate. The §7.5.2 erratum (this revision) stops
an undefined `checksum` from counting as an integrity signal until a digest is
defined.

A future revision should define the digest. The **proposed semantics**: the
`sha256:` digest of the **canonical N.1 JSON form of the record with the
`checksum` member itself omitted** — the record-builder convention above. It is
recomputable by any receiver from exactly what was served, and it is the only
non-self-referential, APPENDABLE-stable choice: a digest over XCDR2 bytes shifts
when the type appends a member, and one that includes `checksum` cannot be
checked without already knowing it. This is not landed in 1.8 — assigning the
field a meaning it never had would retroactively make every record computed
under any other convention nonconformant, which is a feature decision, not an
erratum.

### Wire-Level Interop Testing

Appendix I validates schema expressiveness through static conformance checks. Future revisions will add wire-level interoperability tests across at least two DDS implementations (CycloneDDS and Fast DDS minimum) to validate end-to-end publish/subscribe fidelity, QoS enforcement, and CDR encoding compatibility.

### Transport-Agnostic Semantic Layer

The spatial semantics defined by SpatialDDS — `FrameRef`-by-UUID, the Coverage Model, manifests, the URI scheme, and the dataset conformance methodology — are conceptually separable from the DDS transport binding. Future work will explore canonical bindings to additional transports (gRPC, MCAP files, Arrow Flight) while preserving the semantic layer unchanged. This would position SpatialDDS as an open semantic standard for spatial data, with DDS as the primary real-time binding and additional bindings for offline recording, cloud integration, and ML pipeline ingestion.

### Factor Graph Interchange

SpatialDDS's pose-graph types (`Node`, `Edge`, `MapMeta`) carry SLAM factor graph results. A dedicated factor graph interchange format — analogous to ONNX for neural networks — would enable portable exchange of arbitrary factor graph structures between solvers. SpatialDDS would reference such graphs via `BlobRef`, with `MapMeta` carrying optimization state metadata. This is a complementary effort, not a SpatialDDS extension.

### Bridges to External Ecosystems

Priority bridges for connecting SpatialDDS to robotics, IoT, ML, and visualization ecosystems. These are implementation artifacts maintained in the SpatialDDS-demo repository, not spec extensions.

Implemented:

- SpatialDDS ↔ MCAP recorder/replayer (offline recording, Foxglove visualization, ML pipeline ingestion).
- SpatialDDS ↔ ROS 2 bridge (`sensor_msgs`, `geometry_msgs`, `vision_msgs` translation with tf2 frame mapping).
- SpatialDDS ↔ MQTT bridge (edge-to-cloud via Mosquitto or AWS IoT Core, with QoS mapping and per-operator topic policies).
- SpatialDDS ↔ WebSocket bridge (browser dashboards, digital twin UIs, topic discovery, client-side subscriptions).

Planned:

- SpatialDDS ↔ Gymnasium observation space adapter (RL agent training on live spatial streams).

Together, these directions point toward a future where SpatialDDS is not just a protocol but a foundation for an open, interoperable ecosystem of real-time world models.

We invite implementers, researchers, and standards bodies to explore SpatialDDS, contribute extensions, and help shape it into a shared backbone for real-time spatial computing and AI world models.
