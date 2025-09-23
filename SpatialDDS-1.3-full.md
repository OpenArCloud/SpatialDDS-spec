## **SpatialDDS: A Protocol for Real-World Spatial Computing**

*An open invitation to build a shared bus for spatial data, AI world models, and digital twins.*

**Version**: 1.3 (Draft)
**Date**: TBD
**Author**: James Jackson [Open AR Cloud, Metaverse Standards Forum - Real/Virtual World Integration WG Co-chair]

## Contents
1. [Introduction](sections/v1.3/01-introduction.md)
2. [Profiles and Scope](sections/v1.3/02-profiles-and-scope.md)
3. [Identifiers and URIs](sections/v1.3/03-identifiers-and-uris.md)
4. [Manifests](sections/v1.3/04-manifests.md)
5. [Discovery](sections/v1.3/05-discovery.md)
6. [Data Transport](sections/v1.3/06-data-transport.md)
7. [Security and Privacy](sections/v1.3/07-security-and-privacy.md)
8. [Conformance](sections/v1.3/08-conformance.md)
9. [Appendices](sections/v1.3/09-appendices.md)

### Supporting material
- [Operational Scenarios](sections/v1.3/04-operational-scenarios.md)
- [Conclusion](sections/v1.3/conclusion.md)
- [Future Directions](sections/v1.3/future-directions.md)
- [Glossary of Acronyms](sections/v1.3/glossary.md)
- [References](sections/v1.3/references.md)
- [Appendix A: Core Profile 1.0](sections/v1.3/appendix-a.md)
- [Appendix B: Discovery Profile 1.0](sections/v1.3/appendix-b.md)
- [Appendix C: Anchor Registry Profile 1.0](sections/v1.3/appendix-c.md)
- [Appendix D: Extension Profiles](sections/v1.3/appendix-d.md)
- [Appendix E: Provisional Extension Examples](sections/v1.3/appendix-e.md)

## **1. Introduction (Informative)**

SpatialDDS is a protocol framework for exchanging live spatial data between devices, edge services, and digital twin backends. It
provides a common publish/subscribe fabric so that localization, mapping, perception, and content systems can cooperate while
remaining independently deployed.

### **1.1 Purpose**

SpatialDDS exists to make real-world spatial computing interoperable. It defines:

* **A shared data plane** based on the Object Management Group (OMG) Data Distribution Service (DDS) that applications can use to
  publish and subscribe to typed spatial data with deterministic Quality of Service (QoS).
* **A catalog of profiles** that bundle schema definitions for specific capabilities such as pose graphs, anchors, discovery
  manifests, and domain extensions.
* **A resolver-friendly identifier scheme** so that anchors, services, and content packs can be referenced consistently across
  transports and organizations.

These building blocks enable robotics fleets, AR clients, twin simulators, perception services, and AI agents to communicate using
well-defined semantics rather than bespoke integrations.

### **1.2 Scope**

The SpatialDDS 1.3 specification covers:

* Core schemas for pose graphs, geometry tiles, anchor definitions, discovery announcements, and manifest metadata.
* Identifier formats, resolver endpoints, and manifest requirements that allow resources to be located reliably.
* Normative behavior for discovery exchanges, baseline transports, and conformance profiles.
* Security, privacy, and authentication considerations for deployments spanning devices, enterprise networks, and public cloud
  services.

The specification does **not** prescribe rendering engines, proprietary content formats, commercial service SLAs, or internal
implementations of localization, mapping, or semantic understanding algorithms. Such components can interoperate through the
standardized interfaces defined here while remaining implementation-specific.

### **1.3 Key principles**

* **Interoperability first.** SpatialDDS is modular so that independently built systems can exchange world-state data without
  custom adapters. Wherever possible it aligns with adjacent standards such as OGC GeoPose, 3D Tiles, and Khronos OpenXR.
* **Modularity through profiles.** Implementers adopt only the profile sets that match their use case. Core functionality is
  separated from discovery, anchors, and optional extensions to avoid unnecessary coupling.
* **Global identity.** Stable identifiers expressed as `spatialdds://` URIs allow anchors, services, and content to be referenced
  across transports and over time, while resolver manifests provide rich metadata when needed.
* **Wire efficiency.** Schemas are compact and typed. Heavy payloads—geometry, feature blobs, neural assets—are transmitted out of
  band and referenced by identifier, keeping the data plane lean.
* **AI-ready, domain-neutral.** SpatialDDS is motivated by AR, robotics, and digital twins but does not privilege any one domain.
  AI agents, sensors, and enterprise systems can all publish and subscribe using the same vocabulary.

### **1.4 Document roadmap**

*Section 2* introduces the normative profiles that scope SpatialDDS deployments and how optional capabilities can be combined.
*Section 3* specifies identifiers and the URI scheme used throughout the protocol. *Section 4* describes manifest structures and
validation requirements, while *Section 5* formalizes discovery exchanges and resolver behavior. *Section 6* captures transport
expectations and QoS classes, *Section 7* outlines security and privacy considerations, and *Section 8* defines conformance
criteria. *Section 9* aggregates informative appendices, example schemas, and background material.


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


## **3. Identifiers and URIs (Normative unless noted)**

SpatialDDS assigns globally unique resource identifiers so that anchors, services, content bundles, and registries can be shared
across deployments. Identifiers appear in DDS messages, manifests, and resolver responses. This section defines the URI scheme,
versioning rules, and required manifest fields.

### **3.1 Identifier model (Informative)**

Every SpatialDDS resource is identified by a **persistent identifier (PID)** that remains stable for the logical entity (for
example, a specific anchor or service). A PID MAY point to multiple **revision identifiers (RIDs)** over time; each RID represents
an immutable manifest revision or payload snapshot. PIDs are serialized as `spatialdds://` URIs without a version parameter.
RIDs append a `;v=<revision>` parameter so that clients can request a specific manifest instance while leaving the PID unchanged.

### **3.2 URI scheme syntax (Normative)**

SpatialDDS URIs SHALL conform to the following URI template and Augmented Backus–Naur Form (ABNF):

```
spatialdds://<authority>/<zone>/<type>/<rid>[;v=<version> *(;<key>=<value>)]
```

```
spatialdds-uri  = "spatialdds://" authority "/" zone "/" type "/" rid [ parameters ]
authority       = host              ; as defined by RFC 3986 section 3.2.2
zone            = 1*64(zone-char)
zone-char       = ALPHA / DIGIT / "-" / "_"
type            = "anchor" / "anchor-set" / "content" / "service"
rid             = 26ulid
26ulid          = 26(ULID-char)
ULID-char       = DIGIT / %x41-5A        ; uppercase A-Z excluding I, L, O, U
parameters      = *( ";" param-name "=" param-value )
param-name      = 1*16( ALPHA / DIGIT / "-" / "_" )
param-value     = 1*32( ALPHA / DIGIT / "." / "-" / "_" )
version         = param-value
```

* `authority` SHALL be a fully qualified DNS hostname under the issuer's control. Comparison is case-insensitive but issuers
  SHOULD publish lowercase.
* `zone` scopes identifiers beneath the authority. Authorities MUST guarantee uniqueness of `<type>/<rid>` pairs within each
  zone. Zone comparisons are case-sensitive.
* `type` selects the resource class and SHALL match one of the enumerated values above. New values require a future revision of
  this specification.
* `rid` SHALL be a 26-character Crockford Base32 ULID rendered in uppercase (digits `0-9`, letters `A-Z` excluding `I`, `L`,
  `O`, `U`). RIDs are case-sensitive.
* Additional parameters MAY be appended. Unknown parameter names SHALL be ignored by clients unless otherwise negotiated. The
  `v` parameter, when present, identifies a manifest revision and SHALL be treated as a RID differentiator.

Authorities SHALL publish identifiers only within domains they control and SHALL ensure that ULIDs are not reused for distinct
resources.

### **3.3 Resolver requirements (Normative)**

Authorities that issue SpatialDDS URIs SHALL host an HTTPS resolver endpoint. Clients resolve URIs using these rules:

1. Fetch `https://<authority>/.well-known/spatialdds` (JSON) to obtain a resolver descriptor. The descriptor SHALL contain a
   `resolver` property whose value is an absolute HTTPS URL prefix.
2. Construct the manifest lookup URL as `<resolver>/<zone>/<type>/<rid>`. If the URI includes `;v=<revision>`, clients SHALL
   append `?v=<revision>` to the lookup URL.
3. Issue an HTTPS `GET` with `Accept: application/spatialdds+json, application/json;q=0.8`. Servers SHALL present certificates
   valid for `<authority>`.
4. Successful responses SHALL be UTF-8 JSON payloads with `Content-Type: application/spatialdds+json`. Responses SHOULD include
   either an `ETag` or `Last-Modified` header and appropriate caching directives. Clients SHALL honor `Cache-Control` directives
   and SHALL revalidate cached entries at least once every 24 hours. When a version parameter is provided, authorities MAY mark
   the response as immutable for up to one year.
5. Failure responses SHALL follow conventional HTTP semantics. `404 Not Found` indicates the PID or RID is unknown. `410 Gone`
   indicates permanent retirement. `451` responses SHOULD surface a human-readable explanation to the operator.

Resolver descriptors MAY advertise alternative transports (for example, DDS-native manifest topics or content-addressed storage)
via an `alt_transports` array. Clients MAY use those transports according to local policy, but HTTPS resolution SHALL remain
available for every published PID.

### **3.4 Manifest linkage (Normative)**

Every manifest retrieved via a SpatialDDS URI SHALL contain a top-level `self_uri` member whose value exactly matches the PID or
RID used for retrieval (including any `;v=` parameter). Manifests describing resources that can appear in DDS messages SHALL also
include:

* `resource_id`: the identifier transmitted on the bus (for example, `anchor_id`, `service_id`). This SHALL equal the ULID
  component of the URI.
* `profile_ids` or equivalent capability declarations indicating which profiles the resource implements.
* `created_at`/`updated_at` timestamps in ISO 8601 format so that clients can reason about staleness.

If a manifest references other SpatialDDS resources (e.g., dependencies), those references SHALL be expressed using
`spatialdds://` URIs. Relative or opaque references SHALL NOT be used.

### **3.5 Rationale and alternatives (Informative)**

SpatialDDS uses HTTPS-resolvable URIs rather than opaque UUIDs so that identifiers double as dereferenceable documentation. The
ULID component provides monotonically sortable identifiers that remain URL-safe. Organizations that already maintain UUID-based
systems MAY map them to ULIDs internally before issuing a SpatialDDS PID. For moving objects whose state changes rapidly, the PID
remains stable while manifests capture the latest metadata; high-frequency updates continue to flow across DDS topics.

### **3.6 Examples (Informative)**

* Anchor PID: `spatialdds://museum.example/hall-a/anchor/01J8QDFQX3W9X4CEX39M9ZP6TQ`
* Anchor RID: `spatialdds://museum.example/hall-a/anchor/01J8QDFQX3W9X4CEX39M9ZP6TQ;v=2024-05-12`
* Service PID: `spatialdds://acme.svc/sf/service/vps-main`
* Content PID referencing dependent assets: `spatialdds://acme.svc/sf/content/market-stroll`

Each example dereferences through the resolver workflow above and returns a manifest containing the same `self_uri`.


## **4. Manifests (Normative)**

SpatialDDS manifests are JSON documents that provide descriptive metadata for resources referenced on the DDS bus. Manifests are
dereferenced through `spatialdds://` URIs (Section 3) and inform clients about coverage, capabilities, transports, security
requirements, and dependencies.

### **4.1 Common structure (Normative)**

Every manifest SHALL:

* Conform to UTF-8 encoded JSON.
* Include the members listed in Table 4-1.

| Member | Requirement | Description |
| --- | --- | --- |
| `self_uri` | REQUIRED | Canonical PID or RID for this manifest (Section 3.4). |
| `resource_id` | REQUIRED | ULID portion of the identifier matching the DDS field (e.g., `service_id`). |
| `resource_kind` | REQUIRED | One of `anchor`, `anchor-set`, `service`, or `content`. |
| `profile_ids` | REQUIRED | Array of profile identifiers implemented by this resource. At minimum `core:1.0`. |
| `version` | REQUIRED | Provider-defined semantic or numeric version string. |
| `zone` | REQUIRED | Zone label corresponding to the URI path. |
| `authority` | REQUIRED | Domain name that issued the identifier. |
| `created_at` | REQUIRED | RFC 3339 timestamp of initial publication. |
| `updated_at` | REQUIRED | RFC 3339 timestamp of the latest revision. |
| `description` | OPTIONAL | Human-readable summary. SHOULD be ≤ 512 characters. |
| `capabilities` | REQUIRED for services/content | Array describing supported operations (see Section 4.2). |
| `coverage` | REQUIRED when applicable | Spatial coverage geometry or bounding volume describing availability. |
| `transports` | REQUIRED when endpoints exist | List of endpoint descriptors, each specifying scheme, host, port, and QoS hints. |
| `auth` | OPTIONAL | Authentication requirements (Section 7). |
| `dependencies` | OPTIONAL | Array of `spatialdds://` URIs that this resource depends on. |

If a resource has no physical coverage (for example, a global anchor registry), the `coverage` member SHALL be present with
`"kind": "global"`.

### **4.2 Resource-specific requirements (Normative)**

* **Anchors and Anchor Sets** SHALL include a `anchors` array or `anchor_sets` array. Each entry SHALL provide a GeoPose using the
  `frame_kind`, `lat_deg`, `lon_deg`, `alt_m`, and quaternion members defined in `idl/v1.3/anchors.idl`. Anchor manifests SHALL
  also provide a `stamp` indicating the most recent update and MAY reference supporting assets through the `assets` array.
* **Services** SHALL describe callable endpoints in `transports`. For DDS-based interactions the entry SHALL specify the topic
  names, QoS class (Section 6), and any required discovery parameters. HTTP or gRPC endpoints SHALL include the HTTP method and
  base path. Services SHALL declare supported request/response encodings via `capabilities[*].formats`.
* **Content** manifests SHALL list anchors or frames that the content binds to using the `bindings` array. Each binding SHALL
  reference a SpatialDDS anchor URI and MAY include placement offsets. Content manifests MAY include asset descriptors for large
  media; those descriptors MAY use HTTPS URLs or content-addressed URIs.

### **4.3 Validation and publication (Normative)**

Authorities SHALL validate manifests against the JSON Schemas published with this specification (see Appendix references). A
manifest revision SHALL be published whenever any REQUIRED member changes. Providers MAY publish additional metadata, but custom
members SHALL be namespaced using reverse-DNS keys (e.g., `"com.example:retention_days"`).

Manifests SHALL be made available via HTTPS as described in Section 3.3. When manifests include references to large artifacts or
non-public transports, the manifest SHALL state any authentication or licensing prerequisites in the `auth` section. Providers
SHOULD include sample request flows or OpenAPI references in `documentation` members when complex interactions are expected.

### **4.4 Examples (Informative)**

Representative manifests are provided for reference:

#### **4.4.1 Visual Positioning Service (VPS)**

```json
{{include:manifests/v1.3/vps_manifest.json}}
```

#### **4.4.2 Mapping Service**

```json
{{include:manifests/v1.3/mapping_service_manifest.json}}
```

#### **4.4.3 Content/Experience Package**

```json
{{include:manifests/v1.3/content_experience_manifest.json}}
```

#### **4.4.4 Anchor Set**

```json
{{include:manifests/v1.3/anchors_manifest.json}}
```


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


## **6. Data Transport (Normative)**

SpatialDDS separates logical schemas from transport bindings. Implementations SHALL observe the transport requirements in this
section when exchanging data referenced by discovery manifests.

### **6.1 Baseline transports**

* **DDS/RTPS.** All Core profile data SHALL be available via DDS using the Real-Time Publish-Subscribe (RTPS) protocol. Vendors
  MAY use proprietary DDS implementations provided they interoperate on the wire.
* **HTTP/2 or HTTP/3.** Manifests, large geometry blobs, and asset downloads SHALL be retrievable over HTTPS. Providers SHOULD
  offer HTTP/3/QUIC where available to reduce latency and improve congestion control.
* **gRPC/Web services.** Service manifests MAY expose RPC interfaces. When doing so they SHALL specify the protocol (`grpc`,
  `https`, `webrtc`) and version in the manifest `transports` array.

### **6.2 Optional transports**

The following transports MAY be offered in addition to the baseline:

* **DDS over QUIC or TCP.** Providers MAY expose DDS participants over QUIC or TCP tunnels for constrained networks. Such
  transports SHALL be documented in the manifest `transports` array with connection parameters.
* **WebRTC data channels.** Real-time client applications MAY negotiate WebRTC for low-latency streams. WebRTC endpoints SHALL be
  described with ICE server configuration and STUN/TURN requirements.
* **Content-addressed networks (e.g., IPFS).** Large static assets MAY be replicated via content-addressed URIs advertised in the
  manifest.

### **6.3 QoS classes**

SpatialDDS defines QoS recommendations per topic class. Providers SHALL document the QoS policy in manifests and configure DDS
publishers/subscribers accordingly.

| Topic class | Reliability | Durability | Liveliness | Deadline | Notes |
| --- | --- | --- | --- | --- | --- |
| Pose updates (`pg.node`, `geo.fix`) | Best-effort, KEEP_LAST(5) | VOLATILE | AUTOMATIC | ≤ 33 ms | Prioritize latency. |
| Anchor updates (`anchors.delta`) | RELIABLE, KEEP_ALL | TRANSIENT_LOCAL | AUTOMATIC | 1 s | Ensure eventual consistency. |
| Geometry tiles (`geom.tile.*`) | RELIABLE, KEEP_LAST(1) | TRANSIENT_LOCAL | AUTOMATIC | Provider-defined | Tiles may be large; use flow control. |
| Semantics detections (`semantics.det.*`) | RELIABLE, KEEP_LAST(10) | VOLATILE | AUTOMATIC | 100 ms | Maintain recent context. |
| Discovery topics | RELIABLE, KEEP_LAST(1) | VOLATILE | MANUAL_BY_PARTICIPANT | 5 s | Match announce repetition interval. |

Implementations MAY deviate from these defaults when justified by environment constraints but SHALL document deviations in the
manifest `capabilities` or `transports` metadata.

### **6.4 Error handling and health**

* Publishers SHALL set the `ttl_ms` field on discovery messages and SHALL refresh announcements before expiry.
* Subscribers SHALL monitor liveliness. Missing heartbeats for more than 3× the advertised deadline SHOULD trigger reconnection
  or service reselection.
* Providers SHOULD expose health endpoints (HTTP `GET /healthz`) or DDS heartbeat topics so that clients can detect partial
  failures.
* TTL and heartbeat policies SHALL be documented in manifests so that clients can adapt reconnection behavior.


## **7. Security and Privacy (Normative + Informative)**

SpatialDDS deployments SHALL protect identifiers, manifests, and data-plane exchanges commensurate with the sensitivity of the
information being shared. This section defines baseline security requirements and provides guidance for privacy-preserving
implementations.

### **7.1 Authentication and authorization (Normative)**

* HTTPS resolver endpoints SHALL use TLS 1.2 or later with modern cipher suites. Client authentication MAY use OAuth 2.0 Bearer
  tokens, mutual TLS (mTLS), or other enterprise mechanisms advertised in manifests.
* Services that require authenticated access SHALL describe accepted mechanisms in the manifest `auth` block. Supported keys
  include `"scheme": "oauth2"`, `"scheme": "mtls"`, or `"scheme": "api-key"`. When OAuth 2.0 / OIDC is used, manifests SHALL
  provide the issuer URL and scopes needed to obtain tokens.
* DDS transport security SHOULD employ DDS Security (OMG DDS Security specification) with mutual authentication. Keys SHALL be
  rotated according to organizational policy and SHOULD be scoped per zone when feasible.
* Authorization decisions SHOULD be enforced as close to the resource as possible (e.g., at the resolver or DDS participant). The
  manifest MAY include capability-based access hints (e.g., `"allowed_roles": ["anchor-admin"]`).

### **7.2 Integrity and signing (Normative)**

* Manifests SHALL include integrity metadata. Providers MAY use JSON Web Signatures (JWS) or CBOR Object Signing and Encryption
  (COSE). When signing is applied, a `signature` object SHALL be present containing the algorithm, key identifier, and detached or
  embedded signature.
* Anchor sets or other critical data MAY be signed at the payload level. When provided, the manifest SHALL specify the signing
  method so consumers can validate updates before acceptance.

### **7.3 Privacy considerations (Informative)**

Spatial data can reveal personal or sensitive information. Implementers SHOULD:

* Minimize inclusion of personally identifiable information in manifests and announcements.
* Respect jurisdictional requirements for location sharing and consent. Manifest `auth` blocks MAY reference policy documents or
  data-retention statements.
* Clearly state retention periods for stored anchors, pose histories, and perception data. The manifest MAY include custom fields
  such as `"com.example:retention_days"` to communicate policy.
* Provide mechanisms to revoke anchors or content rapidly (e.g., publish `ttl_ms = 0` announcements and serve `410 Gone`).

### **7.4 Transport security (Normative)**

* All HTTPS endpoints SHALL enforce TLS certificate validation and SHALL prefer HTTP Strict Transport Security (HSTS).
* WebRTC transports SHALL require DTLS-SRTP encryption.
* DDS transports SHALL enable encryption-at-rest when the deployment infrastructure supports it (e.g., encrypted DDS shared
  memory segments).

### **7.5 Operational guidance (Informative)**

Operators SHOULD monitor for resolver misuse, repeated authentication failures, and stale manifests. Security incidents SHOULD
trigger manifest revocation (`410 Gone`) and publication of updated identifiers. Privacy impact assessments are RECOMMENDED for
deployments involving public spaces or user-generated anchors.


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


## **9. Appendices (Informative)**

Supplemental material is organized into separate documents referenced below. These appendices provide detailed schemas, extended
examples, and rationale that complement the normative sections of this specification.

### **9.1 Example IDLs**

* [Appendix A: Core Profile 1.0](appendix-a.md)
* [Appendix B: Discovery Profile 1.0](appendix-b.md)
* [Appendix C: Anchor Registry Profile 1.0](appendix-c.md)
* [Appendix D: Extension Profiles](appendix-d.md)
* [Appendix E: Provisional Extension Examples](appendix-e.md)

### **9.2 Extended manifests and samples**

* [Operational scenarios and deployment patterns](04-operational-scenarios.md)
* Additional JSON manifest samples are available in the `manifests/v1.3` directory referenced throughout Section 4.

### **9.3 Schema references**

JSON Schemas for manifests, discovery messages, and capability descriptors are distributed alongside this specification in the
`scripts/schema` directory. Providers SHOULD incorporate these schemas into their CI pipelines to ensure manifests remain
conformant.

### **9.4 Rationale and future work**

* [Conclusion](conclusion.md)
* [Future directions](future-directions.md)
* [Glossary of acronyms](glossary.md)
* [References](references.md)

These documents capture background context and design decisions, including why SpatialDDS adopts resolver-friendly URIs and how
it aligns with adjacent standards. They are informative and do not introduce new conformance requirements.

