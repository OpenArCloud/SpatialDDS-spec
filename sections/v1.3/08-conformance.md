## **8. Conformance (Normative)**

This section defines what it means to conform to SpatialDDS 1.3.

### **8.1 Profile claims**

* Every implementation claiming SpatialDDS conformance SHALL implement the Core profile.
* Optional profile claims (Anchors, VPS, World Stream, Twin Sync, Telco APIs) SHALL be listed explicitly in documentation and
  manifests.
* Implementations SHALL satisfy all MUST/SHALL statements in Sections 2–7 that correspond to the profiles they claim.
* When multiple profile versions are supported simultaneously, the implementation SHALL negotiate or advertise the active version
  via discovery manifests or capability descriptors.

### **8.2 Manifest validation**

* Providers SHALL validate manifests against the normative JSON Schemas published with this specification prior to distribution.
* Implementations SHALL reject manifests missing REQUIRED members defined in Section 4 or containing malformed identifiers.
* Manifests containing unknown optional members MAY be accepted, but consumers SHALL ignore members they do not understand unless
  explicitly negotiated via extensions.

### **8.3 Runtime interoperability**

* Discovery participants SHALL successfully publish and subscribe to the announce topics defined in Section 5.
* Core data-plane participants SHALL demonstrate exchange of pose graphs, anchors, and geometry tiles using the QoS policies in
  Section 6.
* Anchor Registry participants SHALL demonstrate handling of full snapshots (`AnchorSet`) and incremental updates (`AnchorDelta`).

### **8.4 Test cases (Informative)**

Implementers are encouraged to validate deployments using the following scenarios:

1. **Manifest round-trip.** Publish a `ServiceAnnounce`, resolve the manifest URI, and verify `self_uri` matches the request.
2. **Late joiner recovery.** Start a new DDS participant and confirm it receives cached anchor sets and geometry tiles without
   resending full history.
3. **Credential enforcement.** Request a protected service manifest without credentials (expect denial), then with valid OAuth 2.0
   tokens or mTLS certificates (expect success).
4. **Anchor revocation.** Publish an `AnchorAnnounce` with `ttl_ms = 0` and confirm subscribers discard cached data within the TTL.

A deployment MAY publish additional industry-specific conformance suites in the appendices.
