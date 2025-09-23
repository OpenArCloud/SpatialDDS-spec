## **2. Profiles and Scope (Informative)**

SpatialDDS is delivered as a set of profiles. Profiles bundle message types, QoS expectations, and manifest capabilities that can
be implemented together to satisfy a use case. Deployments MAY implement only a subset of profiles, but every conforming
implementation SHALL support the Core profile as defined below.

### **2.1 Core profile (Normative)**

The Core profile defines the minimum interoperable baseline:

* Pose graph nodes and edges for streaming evolving localization graphs.
* Geometry tile metadata, patches, and blobs for exchanging spatial meshes or point clouds.
* Anchor primitives and transforms for connecting local frames to global references.
* Blob transfer utilities for moving large binary payloads alongside typed messages.

Implementations that claim support for the Core profile MUST publish and subscribe to these topics using the IDL defined in
`idl/v1.3/core.idl`, MUST negotiate QoS consistent with Section 6, and MUST be able to ingest manifests that reference the same
resource identifiers used on the bus.

### **2.2 Optional profile families (Normative + Informative)**

SpatialDDS 1.3 defines several optional capability families. Each family corresponds to a collection of IDL modules and manifest
capabilities. Implementations MAY adopt any combination provided they satisfy the Core requirements.

* **Anchors.** Adds durable anchor sets, incremental updates, and registry synchronization flows. Requires the messages defined in
  `idl/v1.3/anchors.idl` and the manifest sections in Section 4. Implementations that advertise the Anchors profile MUST be able
  to resolve `anchor` and `anchor-set` URIs and honor Anchor Registry delta semantics.
* **VPS (Visual Positioning Service).** Extends Core with the SLAM Frontend IDL (feature/keyframe exchange) and the discovery
  manifests needed to expose relocalization endpoints. VPS providers SHOULD also implement the Anchors profile so that fixes can
  be expressed in persistent frames.
* **World Stream.** Uses geometry tile streaming and content manifests to deliver large-scale world models or reality feeds.
  Providers SHOULD support HTTP/3 or QUIC transports for bulk tile transfer and MAY announce availability via the Discovery
  profile.
* **Twin Sync.** Couples Core pose/geometry data with Semantics profile detections to synchronize digital twins. Twin services
  SHOULD expose manifests describing ingestion endpoints and retention policies.
* **Telco APIs.** Integrates SpatialDDS discovery and manifest metadata with network-provided QoS, localization, or identity
  services. Providers adopting this profile MUST document any additional authentication prerequisites in their manifests and
  SHOULD publish resolver descriptors reachable over the public internet.

### **2.3 Combining profiles (Informative)**

Profiles are intentionally composable. Some common combinations include:

| Deployment goal | Mandatory profiles | Typical additions |
| --- | --- | --- |
| Head-worn AR client consuming a shared map | Core | Anchors, World Stream |
| VPS provider servicing mobile devices | Core, VPS | Anchors, Telco APIs |
| Digital twin ingest from a sensor fleet | Core, Twin Sync | World Stream |
| Multi-robot SLAM collaboration | Core | VPS, Anchors |

When multiple profiles are implemented, manifests MUST enumerate all capabilities and associated transports so that clients can
select compatible interactions (see Section 4). Discovery messages SHOULD advertise profile support using the
`profile_ids`/`capabilities` fields defined in the Discovery IDL.

### **2.4 Versioning and evolution (Informative)**

Each profile is versioned independently. A deployment MAY mix different profile versions provided that manifests, IDs, and QoS
settings remain compatible. Implementers SHOULD consult the change history in the appendices when planning upgrades and MAY use
the optional URI version parameter described in Section 3 to signal manifest revisions.
