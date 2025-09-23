## **5. Discovery (Normative)**

Discovery allows SpatialDDS participants to publish capabilities, locate services, and negotiate the transports necessary for
runtime cooperation. The Discovery profile extends the Core profile with lightweight announce topics and manifest references.

### **5.1 Discovery topics**

Implementations supporting the Discovery profile SHALL implement the following DDS topics using the IDL in
`idl/v1.3/discovery.idl`:

* `spatial::disco::ServiceAnnounce`
* `spatial::disco::ContentAnnounce`
* `spatial::disco::AnchorAnnounce`
* `spatial::disco::CoverageAnnounce`

Participants SHALL publish announcement samples when a resource becomes available or materially changes. Announcement samples
SHALL include:

* The canonical resource identifier (`service_id`, `content_id`, etc.).
* A `manifest_uri` referencing a manifest that satisfies Section 4.
* Optional `profile_ids`, `capabilities`, and `coverage` hints so that consumers can perform coarse filtering without fetching
  the manifest.

Announcements SHOULD be repeated periodically (default 30 seconds) to support late joiners. A participant MAY withdraw a resource
by publishing an announcement with `ttl_ms = 0`.

### **5.2 Subscriptions and filtering**

Consumers SHALL filter discovery topics using the DDS ContentFilteredTopic mechanism or equivalent to limit traffic to relevant
zones, resource kinds, or capabilities. Implementations SHOULD provide filters for geohash ranges, profile identifiers, and
service kinds. When filters cannot express the desired selection, clients MAY fetch manifests and evaluate additional metadata
before initiating data-plane subscriptions.

### **5.3 Resolver integration**

Announcement messages SHALL use `spatialdds://` URIs in `manifest_uri`. Receivers SHALL resolve those URIs using the workflow in
Section 3 before initiating further interaction. When a manifest cannot be retrieved, consumers SHOULD treat the resource as
unavailable and MAY continue retrying based on local policy. Authorities SHOULD ensure that manifest resolvers return coherent
error responses (Section 3.3) so that discovery clients can surface failures to operators.

### **5.4 Service selection**

When multiple services satisfy a capability, clients SHOULD evaluate:

* Manifest-declared coverage and QoS classes.
* Authentication requirements and token lifetimes.
* Supported transports and encodings.

Clients MAY maintain local preference lists or selection policies (e.g., prefer local-zone authorities). Services SHOULD expose
load or availability hints via optional manifest fields (`status`, `capacity`) to aid selection. When a service advertises a
`ttl_ms`, consumers SHALL stop using the service once the TTL expires unless a fresh announcement is received.

### **5.5 Informative examples**

A VPS deployment might publish `ServiceAnnounce` messages with:

* `service_id = 01HXYV3JDXQ6F6NP6CPS2Z4TMT`
* `manifest_uri = spatialdds://acme.svc/sf/service/vps-main`
* `capabilities = ["vps:pose-fix", "anchors:lookup"]`

An AR content provider might publish `ContentAnnounce` messages referencing manifests that list anchors, asset packs, and
preferred transports. Consumers subscribe to both service and content announcements to assemble an end-to-end experience.
