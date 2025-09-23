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
{
  "service_id": "svc:vps:acme/sf-downtown",
  "profiles": ["Core", "SLAM Frontend", "AR+Geo"],
  "request": {
    "features_topic": "feat.keyframe",
    "image_blob_role": "image/jpeg",
    "prior_topic": "geo.fix"
  },
  "response": {
    "rich": "pg.nodegeo",
    "minimal": "geo.fix"
  },
  "limits": { "max_fps": 10, "max_image_px": 1920 },
  "auth": { "scheme": "oauth2", "issuer": "https://auth.acme.com" },
  "coverage": { "geohash": ["9q8y","9q8z"] }
}

```

#### **4.4.2 Mapping Service**

```json
{
  "service_id": "svc:mapping:acme/sf-downtown",
  "version": "1.0.0",
  "provider": { "id": "acme-maps", "org": "Acme Maps Inc." },
  "title": "Acme Downtown Map Service",
  "summary": "Tiled 3D meshes for SF downtown area",
  "profiles": ["Core"],
  "topics": {
    "meta": "geom.tile.meta",
    "patch": "geom.tile.patch",
    "blob": "geom.tile.blob"
  },
  "tile_scheme": "quadtree",
  "encodings": ["glTF+Draco", "LASzip"],
  "lod_range": [12, 18],
  "coverage": {
    "geohash": ["9q8y","9q8z"],
    "polygon_uri": "https://cdn.acme.example/downtown_poly.geojson"
  },
  "auth": { "scheme": "none" },
  "terms": { "license": "CC-BY-4.0" }
}

```

#### **4.4.3 Content/Experience Package**

```json
{
  "content_id": "xp:sculpture-walk:met-foyer",
  "version": "1.0.2",
  "provider": { "id": "svc:content:museum-inc", "org": "Museum Inc." },
  "title": "AR Sculpture Walk",
  "summary": "Guided AR overlays for five sculptures in the main foyer.",
  "tags": ["ar", "museum", "tour"],
  "profiles_required": ["Core", "AR+Geo"],
  "availability": {
    "from": "2025-09-01T09:00:00Z",
    "until": "2025-12-31T23:59:59Z",
    "local_tz": "America/New_York"
  },
  "coverage": { "geohash": ["dr5ru9","dr5rua"], "polygon_uri": "https://cdn.museum.example/foyer_poly.geojson" },
  "entrypoints": {
    "anchors": [
      { "anchor_id": "anchor/met-foyer/north-plinth", "hint": "Start here" },
      { "anchor_id": "anchor/met-foyer/central", "hint": "Checkpoint 2" }
    ]
  },
  "runtime_topics": {
    "subscribe": ["geo.tf", "geo.anchor", "geom.tile.meta", "geom.tile.patch"],
    "optional": ["semantics.det.3d.set"]
  },
  "assets": [
    { "type": "image", "role": "poster", "uri": "https://cdn.museum.example/img/poster.jpg" },
    { "type": "audio", "role": "narration", "uri": "https://cdn.museum.example/audio/room_intro.mp3", "lang": "en" }
  ]
}

```

#### **4.4.4 Anchor Set**

```json
{
  "schema": "https://example.org/spatialdds/anchor-manifest.schema.json#v1",
  "zone_id": "knossos:palace",
  "zone_title": "Knossos Palace Archaeological Site",
  "coverage": {
    "geohash": ["sv8wkf", "sv8wkg"],
    "bbox": [
      25.1608,
      35.2965,
      25.1665,
      35.3002
    ]
  },
  "anchors": [
    {
      "anchor_id": "square:statue-east",
      "geopose": {
        "lat_deg": 35.29802,
        "lon_deg": 25.16305,
        "alt_m": 110.2,
        "qw": 1,
        "qx": 0,
        "qy": 0,
        "qz": 0
      },
      "assets": [
        {
          "kind": "features:ORB:v1",
          "uri": "https://registry.example/anchors/statue-east/orb_v1.bin",
          "count": 2048,
          "descriptor_bytes": 32,
          "patch_frame": "anchor-local",
          "hash": "sha256:placeholder...",
          "bytes": 65536
        },
        {
          "kind": "geom:pcd:lod1",
          "uri": "https://registry.example/anchors/statue-east/patch_lod1.las",
          "points": 12000,
          "hash": "sha256:placeholder...",
          "bytes": 480000
        }
      ],
      "stamp": "2025-09-07T15:45:00Z"
    },
    {
      "anchor_id": "central-court:north",
      "geopose": {
        "lat_deg": 35.29761,
        "lon_deg": 25.16391,
        "alt_m": 109.8,
        "qw": 0.707,
        "qx": 0,
        "qy": 0,
        "qz": 0.707
      },
      "assets": [
        {
          "kind": "features:SuperPoint:v1",
          "uri": "https://registry.example/anchors/central-court-n/superpoint_v1.npz",
          "count": 1500,
          "descriptor_bytes": 256,
          "hash": "sha256:placeholder...",
          "bytes": 220000
        },
        {
          "kind": "geom:mesh:lod0",
          "uri": "https://registry.example/anchors/central-court-n/patch_lod0.glb",
          "triangles": 8000,
          "hash": "sha256:placeholder...",
          "bytes": 350000
        }
      ],
      "stamp": "2025-09-08T11:12:13Z"
    }
  ],
  "stamp": "2025-09-12T22:55:00Z"
}

```

## **5\. Operational Scenarios: From SLAM to AI World Models**

SpatialDDS is designed to be practical and flexible across real-world deployments. The following scenarios illustrate how the Core, Discovery, Anchors, and Extension profiles can be combined in different ways to support robotics, AR/XR, smart city, IoT, and AI-driven applications. Each scenario lists the profiles involved and the key DDS topics flowing in and out, showing how the schema maps onto actual use cases. Optional profiles such as Neural and Agent are marked clearly, allowing implementers to see future directions without requiring them in the baseline.

### **Core SLAM/SfM Scenarios**

These scenarios cover the foundational use cases for spatial mapping and localization. They show how devices and services exchange features, images, pose graphs, and geometry tiles to support SLAM and structure-from-motion pipelines, either on-device, at the edge, or in multi-agent systems.

1. **On-device Visual(-Inertial) SLAM**  
   A single device runs its own SLAM, fusing camera and IMU, publishing nodes/edges.  
* **Profiles:** Core (Pose Graph, VIO)  
* **Topics In:** raw IMU/camera  
* **Topics Out:** pg.node, pg.edge, geo.tf

2. **Device → Edge Distributed SLAM**  
   A mobile device streams features/images to an edge server for map building.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe, BlobChunk (images)  
* **Topics Out:** pg.node, pg.edge, geom.tile.\*

3. **Multi-Agent SLAM with Global Alignment**  
   Multiple devices contribute to a shared map, aligning through anchors.  
* **Profiles:** Core, Anchors  
* **Topics In:** pg.node/edge from peers  
* **Topics Out:** pg.edge (loop closures), geo.tf (frame alignment)

4. **Offline SfM / Batch Reconstruction**  
   A service reconstructs geometry from stored images/features.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** BlobChunk (image sets), feat.keyframe  
* **Topics Out:** geom.tile.meta/patch/blob

### **Service Scenarios**

These scenarios describe how SpatialDDS supports services that go beyond local SLAM, such as Visual Positioning Services (VPS), cooperative relocalization, map delivery, and anchor registries. Discovery messages and manifests play a key role here, allowing clients to find and interact with services dynamically.

5. **Relocalization / Place Recognition**  
   A service matches incoming features against a prior map for relocalization.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe  
* **Topics Out:** geo.fix, pg.nodegeo


6. **VPS — Features-only Query**  
   Client sends features; service returns a pose or node with geo anchor.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe  
* **Topics Out:** geo.fix or pg.nodegeo


7. **VPS — Image-only Query**  
   Client sends an image; service extracts features and returns pose.  
* **Profiles:** Core  
* **Topics In:** BlobChunk (role=“image/jpeg”)  
* **Topics Out:** geo.fix or pg.nodegeo


8. **Cooperative VPS / Crowd Relocalization**  
   Devices share queries and matches to improve coverage.  
* **Profiles:** Core, Discovery  
* **Topics In:** feat.keyframe, geo.fix  
* **Topics Out:** shared pg.edge or consensus geo.fix


9. **Mapping Service Consumption (Discovery)**  
   Clients discover and fetch map tiles for their area of interest.  
* **Profiles:** Core, Discovery  
* **Topics In:** disco.service, geom.tile.meta/patch/blob  
* **Topics Out:** local cache of geometry


10. **Anchor Registry Subscription (Discovery)**  
    Clients subscribe to a registry of persistent anchors.  
* **Profiles:** Core, Anchors, Discovery  
* **Topics In:** anchors.set, anchors.delta  
* **Topics Out:** geo.tf (local → anchor/world alignment)

### **Consumer Scenarios**

These scenarios focus on AR clients and applications that consume maps, anchors, and semantics. They show how SpatialDDS delivers persistent content alignment, semantic overlays, and shared localization for end-user experiences.

11. **AR Client Map Consumption**  
    An AR headset consumes geometry and anchors to render content.  
* **Profiles:** Core, Anchors  
* **Topics In:** geom.tile.\*, geo.anchor, geo.tf  
* **Topics Out:** none


12. **Semantics-Assisted Mapping**  
    A client enriches tiles with object detections for smarter AR overlays.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob  
* **Topics Out:** semantics.det.3d.set


13. **AR Client with VPS \+ Anchor Registry**  
    A client uses VPS fixes plus anchors for persistent localization.  
* **Profiles:** Core, Anchors, Discovery  
* **Topics In:** feat.keyframe or image blobs, anchors.set  
* **Topics Out:** geo.tf

### **Lifecycle / Recovery Scenario**

This scenario illustrates how a device or client can quickly catch up with the current state of the world after joining late or recovering from a failure. By fetching cached tiles and anchors, clients can synchronize efficiently without disrupting live streams.

14. **Catch-Up & Recovery (Reality Feed Style)**  
    A late joiner fetches cached tiles/anchors to sync quickly.  
* **Profiles:** Core, Anchors  
* **Topics In:** geom.tile.meta/patch/blob, anchors.set  
* **Topics Out:** resumed pg.node/edge

### **AI & World-Model Extensions**

These scenarios extend SpatialDDS beyond SLAM and AR into the realm of AI agents, neural maps, and digital twins. They demonstrate how AI perception services, planning agents, and predictive twin backends can plug into the same bus, consuming and enriching the shared world model. Neural and Agent profiles are optional extensions, and scenarios that use them are marked accordingly.

15. **VLM/Detector as a Perception Service**  
    An AI model consumes images and publishes 2D/3D detections.  
* **Profiles:** Core, Semantics (+ SLAM Frontend if features in)  
* **Topics In:** geom.tile.blob, optionally feat.keyframe  
* **Topics Out:** semantics.det.2d.set, semantics.det.3d.set


16. **Captioning / Visual QA Agent**  
    A vision-language model provides captions/labels tied to anchors or tiles.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob, geo.anchor  
* **Topics Out:** semantics.det.2d.set (with captions), agent.answer (optional)


17. **Neural Map — Remote View Synthesis** *(optional Neural extension)*  
    Thin clients request rendered views from a neural map service.  
* **Profiles:** Core (+ Neural if adopted)  
* **Topics In:** neural.view.req  
* **Topics Out:** neural.view.resp with images


18. **Neural Map — Asset Streaming** *(optional Neural extension)*  
    Neural assets (e.g., Gaussian splats) are streamed as blobs for local rendering.  
* **Profiles:** Core (+ Neural if adopted)  
* **Topics In:** geom.tile.meta/patch (encoding=“nerf”/“gaussians”)  
* **Topics Out:** none


19. **Digital Twin Ingest (Realtime → Twin Backend)**  
    A digital twin backend ingests SpatialDDS streams for persistent modeling.  
* **Profiles:** Core, Semantics, Anchors  
* **Topics In:** pg.node/edge, geom.tile.\*, geo.anchor, semantics.det.3d.set  
* **Topics Out:** none


20. **Digital Twin → SpatialDDS (Predictive Overlays)**  
    A twin service publishes predictions or overlays back to clients.  
* **Profiles:** Core, Semantics  
* **Topics In:** none (internal twin logic)  
* **Topics Out:** semantics.det.3d.set, geom.tile.\*


21. **Route/Task Planning Agent** *(optional Agent extension)*  
    An AI agent consumes world state and publishes goals or routes.  
* **Profiles:** Core (+ Agent if adopted)  
* **Topics In:** pg.node, geo.tf, semantics.det.3d.set, geo.anchor  
* **Topics Out:** task.route, task.goal, or agent.task/status


22. **Human-in-the-Loop Labeling & Training Data Capture**  
    Detections are corrected by humans and fed back for model improvement.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob, semantics.det.\* (proposals)  
* **Topics Out:** semantics.det.\* (corrected), data.capture.meta

Taken together, these scenarios show how SpatialDDS functions as a real-time bus for spatial world models. From raw sensing and SLAM pipelines to AR content, digital twins, and AI-driven perception and planning, the protocol provides a common substrate that lets diverse systems interoperate without heavy gateways or custom formats. This positions SpatialDDS as a practical foundation for AI world models that are grounded in the physical world.


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

## **6. Conclusion**

SpatialDDS provides a lightweight, standards-based framework for exchanging real-world spatial data over DDS. By organizing schemas into modular profiles — with Core, Discovery, and Anchors as the foundation and Extensions adding domain-specific capabilities — it supports everything from SLAM pipelines and AR clients to digital twins, smart city infrastructure, and AI-driven world models. Core elements such as pose graphs, geometry tiles, anchors, and discovery give devices and services a shared language for building and aligning live models of the world, while provisional extensions like Neural and Agent point toward richer semantics and autonomous agents. Taken together, SpatialDDS positions itself as a practical foundation for real-time spatial computing—interoperable, codec-agnostic, and ready to serve as the data bus for AI and human experiences grounded in the physical world.


## **7. Future Directions**

While SpatialDDS establishes a practical baseline for real-time spatial computing, several areas invite further exploration:

* **Reference Implementations**  
  Open-source libraries and bridges to existing ecosystems (e.g., ROS 2, OpenXR, OGC APIs) would make it easier for developers to adopt SpatialDDS in robotics, AR, and twin platforms.  
* **Semantic Enrichment**  
  Extending beyond 2D/3D detections, future work could align with ontologies and scene graphs to enable richer machine-readable semantics for AI world models and analytics.  
* **Neural Integration**  
  Provisional support for neural fields (NeRFs, Gaussian splats) could mature into a stable profile, ensuring consistent ways to stream and query neural representations across devices and services.  
* **Agent Interoperability**  
  Lightweight tasking and coordination schemas could evolve into a standard Agent profile, supporting multi-agent planning and human-AI collaboration at scale.  
* **Standards Alignment**  
  Ongoing coordination with OGC, Khronos, W3C, and GSMA initiatives will help ensure SpatialDDS complements existing geospatial, XR, and telecom standards rather than duplicating them.

Together, these directions point toward a future where SpatialDDS is not just a protocol but a foundation for an open, interoperable ecosystem of real-time world models.

We invite implementers, researchers, and standards bodies to explore SpatialDDS, contribute extensions, and help shape it into a shared backbone for real-time spatial computing and AI world models.


## **8. Glossary of Acronyms**

**AI** – Artificial Intelligence

**AR** – Augmented Reality

**DDS** – Data Distribution Service (OMG standard middleware)

**GSMA** – GSM Association (global mobile industry group)

**IMU** – Inertial Measurement Unit

**IoT** – Internet of Things

**MR** – Mixed Reality

**MSF** – Metaverse Standards Forum

**NeRF** – Neural Radiance Field (neural representation of 3D scenes)

**OGC** – Open Geospatial Consortium

**OMG** – Object Management Group (standards body for DDS)

**ROS** – Robot Operating System

**SfM** – Structure from Motion

**SLAM** – Simultaneous Localization and Mapping

**VIO** – Visual-Inertial Odometry

**VLM** – Vision-Language Model

**VPS** – Visual Positioning Service

**VR** – Virtual Reality

**W3C** – World Wide Web Consortium

**XR** – Extended Reality (umbrella term including AR, VR, MR)


## **9. References**

### **DDS & Middleware**

\[1\] Object Management Group. *Data Distribution Service (DDS) for Real-Time Systems.* OMG Standard. Available: [https://www.omg.org/spec/DDS](https://www.omg.org/spec/DDS)

\[2\] Object Management Group. *DDS for eXtremely Resource Constrained Environments (DDS-XRCE).* OMG Standard. Available: [https://www.omg.org/spec/DDS-XRCE](https://www.omg.org/spec/DDS-XRCE)

\[3\] eProsima. *Fast DDS Documentation.* Available: [https://fast-dds.docs.eprosima.com](https://fast-dds.docs.eprosima.com/)

\[4\] Eclipse Foundation. *Cyclone DDS.* Available: [https://projects.eclipse.org/projects/iot.cyclonedds](https://projects.eclipse.org/projects/iot.cyclonedds)

### **XR & Spatial Computing**

\[5\] Khronos Group. *OpenXR Specification.* Available: [https://www.khronos.org/openxr](https://www.khronos.org/openxr)

\[6\] Open Geospatial Consortium. *OGC GeoPose 1.0 Data Exchange Standard.* Available: [https://www.ogc.org/standards/geopose](https://www.ogc.org/standards/geopose)

### **Geospatial Standards**

\[7\] Open Geospatial Consortium. *CityGML Standard.* Available: [https://www.ogc.org/standards/citygml](https://www.ogc.org/standards/citygml)

\[8\] Geohash. *Wikipedia Entry.* Available: [https://en.wikipedia.org/wiki/Geohash](https://en.wikipedia.org/wiki/Geohash)

### **SLAM, SfM & AI World Models**

\[9\] Mur-Artal, R., Montiel, J. M. M., & Tardós, J. D. (2015). *ORB-SLAM: A Versatile and Accurate Monocular SLAM System.* IEEE Transactions on Robotics, 31(5), 1147–1163.

\[10\] Schönberger, J. L., & Frahm, J.-M. (2016). *Structure-from-Motion Revisited.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 4104–4113.

\[11\] Sarlin, P.-E., Unagar, A., Larsson, M., et al. (2020). *From Coarse to Fine: Robust Hierarchical Localization at Large Scale.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 12716–12725.

\[12\] Google Research. *ARCore Geospatial API & Visual Positioning Service.* Developer Documentation. Available: [https://developers.google.com/ar](https://developers.google.com/ar)


## **Appendix A: Core Profile 1.0**

*The Core profile defines the fundamental data structures for SpatialDDS. It includes pose graphs, 3D geometry tiles, anchors, transforms, and generic blob transport. This is the minimal interoperable baseline for exchanging world models across devices and services.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Core 1.2

module spatial {
  module core {

    // ---------- Utility ----------
    struct Time {
      int32  sec;     // seconds since UNIX epoch (UTC)
      uint32 nsec;    // nanoseconds [0..1e9)
    };

    struct PoseSE3 {
      double t[3];    // translation (x,y,z)
      double q[4];    // quaternion (w,x,y,z)
    };

    @appendable struct TileKey {
      @key uint32 x;     // tile coordinate (quadtree/3D grid)
      @key uint32 y;
      @key uint32 z;     // use 0 for 2D schemes
      @key uint8  level; // LOD level
    };

    // ---------- Geometry ----------
    enum PatchOp { ADD = 0, REPLACE = 1, REMOVE = 2 };

    @appendable struct BlobRef {
      string blob_id;   // UUID or content-address
      string role;      // "mesh","attr/normals","pcc/geom","pcc/attr",...
      string checksum;  // SHA-256 (hex)
    };

    @appendable struct TileMeta {
      @key TileKey key;              // unique tile key
      string tile_id_compat;         // optional human-readable id
      double min_xyz[3];             // AABB min (local frame)
      double max_xyz[3];             // AABB max (local frame)
      uint32 lod;                    // may mirror key.level
      uint64 version;                // monotonic full-state version
      string encoding;               // "glTF+Draco","MPEG-PCC","V3C","PLY",...
      string checksum;               // checksum of composed tile
      sequence<string, 32> blob_ids; // blobs composing this tile
      // optional geo hints
      double centroid_llh[3];        // lat,lon,alt (deg,deg,m) or NaN
      double radius_m;               // rough extent (m) or NaN
    };

    @appendable struct TilePatch {
      @key TileKey key;              // which tile
      uint64 revision;               // monotonic per-tile
      PatchOp op;                    // ADD/REPLACE/REMOVE
      string target;                 // submesh/attr/"all"
      sequence<BlobRef, 8> blobs;    // payload refs
      string post_checksum;          // checksum after apply
      Time   stamp;                  // production time
    };

    @appendable struct BlobChunk {
      @key string blob_id;               // which blob
      uint32 index;                      // chunk index (0..N-1)
      sequence<uint8, 262144> data;      // ≤256 KiB per sample
      boolean last;                      // true on final chunk
    };

    // ---------- Pose Graph (minimal) ----------
    enum EdgeTypeCore { ODOM = 0, LOOP = 1 };

    @appendable struct Node {
      string map_id;
      @key string node_id;     // unique keyframe id
      PoseSE3 pose;            // pose in frame_id
      double  cov[36];         // 6x6 covariance (row-major); NaN if unknown
      Time    stamp;
      string  frame_id;        // e.g., "map"
      string  source_id;
      uint64  seq;             // per-source monotonic
      uint64  graph_epoch;     // for major rebases/merges
    };

    @appendable struct Edge {
      string map_id;
      @key string edge_id;     // unique edge id
      string from_id;          // source node
      string to_id;            // target node
      EdgeTypeCore type;       // ODOM or LOOP
      double information[36];  // 6x6 info matrix (row-major)
      Time   stamp;
      string source_id;
      uint64 seq;
      uint64 graph_epoch;
    };

    // ---------- Geo anchoring ----------
    enum GeoFrameKind { ECEF = 0, ENU = 1, NED = 2 };

    @appendable struct GeoPose {
      double lat_deg;
      double lon_deg;
      double alt_m;            // ellipsoidal meters
      double q[4];             // orientation (w,x,y,z)
      GeoFrameKind frame_kind; // ECEF/ENU/NED
      string frame_ref;        // for ENU/NED: "@lat,lon,alt"
      Time   stamp;
      double cov[9];           // 3x3 pos covariance (m^2), row-major; NaN if unknown
    };

    @appendable struct GeoAnchor {
      @key string anchor_id;   // e.g., "anchor/4th-and-main"
      string map_id;
      string frame_id;         // local frame (e.g., "map")
      GeoPose geopose;         // global pose
      string  method;          // "GNSS","VisualFix","Surveyed","Fusion"
      double  confidence;      // 0..1
      string  checksum;        // integrity/versioning
    };

    @appendable struct FrameTransform {
      @key string transform_id; // e.g., "map->ENU@lat,lon,alt"
      string parent_frame;      // global frame (ENU@..., ECEF, ...)
      string child_frame;       // local frame ("map")
      PoseSE3 T_parent_child;   // transform parent->child
      Time    stamp;
      double  cov[36];          // 6x6 covariance; NaN if unknown
    };

    // ---------- Snapshot / Catch-up ----------
    @appendable struct SnapshotRequest {
      @key TileKey key;        // which tile
      uint64 up_to_revision;   // 0 = latest
    };

    @appendable struct SnapshotResponse {
      @key TileKey key;                 // tile key
      uint64 revision;                  // snapshot revision served
      sequence<string, 64> blob_ids;    // composing blobs
      string checksum;                  // composed state checksum
    };

  }; // module core
};   // module spatial

```

## **Appendix B: Discovery Profile 1.0**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Discovery 1.2
// Lightweight announces for services, coverage, and content

module spatial {
  module disco {

    typedef spatial::core::Time Time;
    // Canonical manifest references use the spatialdds:// URI scheme.
    typedef string SpatialUri;

    enum ServiceKind {
      VPS = 0,
      MAPPING = 1,
      RELOCAL = 2,
      SEMANTICS = 3,
      STORAGE = 4,
      CONTENT = 5,
      ANCHOR_REGISTRY = 6,
      OTHER = 255
    };

    @appendable struct KV {
      string key;
      string value;
    };

    @appendable struct ServiceAnnounce {
      @key string service_id;
      string name;
      ServiceKind kind;
      string version;
      string org;
      sequence<string,16> rx_topics;
      sequence<string,16> tx_topics;
      sequence<KV,32> hints;
      SpatialUri manifest_uri;  // MUST be a spatialdds:// URI for this service manifest
      string auth_hint;
      Time stamp;
      uint32 ttl_sec;
    };

    @appendable struct CoverageHint {
      @key string service_id;
      sequence<string,64> geohash;
      double bbox[4];           // [min_lon, min_lat, max_lon, max_lat]
      double center_lat; double center_lon; double radius_m;
      Time stamp;
      uint32 ttl_sec;
    };

    @appendable struct ContentAnnounce {
      @key string content_id;
      string provider_id;
      string title;
      string summary;
      sequence<string,16> tags;
      string class_id;
      SpatialUri manifest_uri;  // MUST be a spatialdds:// URI for this content manifest
      double center_lat; double center_lon; double radius_m;
      Time available_from;
      Time available_until;
      Time stamp;
      uint32 ttl_sec;
    };

  }; // module disco
};

```

## **Appendix C: Anchor Registry Profile 1.0**

*The Anchors profile defines durable GeoAnchors and the Anchor Registry. Anchors act as persistent world-locked reference points, while the registry makes them discoverable and maintainable across sessions, devices, and services.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Anchors 1.2
// Bundles and updates for anchor registries

module spatial {
  module anchors {
    typedef spatial::core::Time Time;
    typedef spatial::core::GeoPose GeoPose;

    @appendable struct AnchorEntry {
      @key string anchor_id;
      string name;
      GeoPose geopose;
      double confidence;
      sequence<string,8> tags;
      Time stamp;
      string checksum;
    };

    @appendable struct AnchorSet {
      @key string set_id;
      string title;
      string provider_id;
      string map_frame;
      string version;
      sequence<string,16> tags;
      double center_lat; double center_lon; double radius_m;
      sequence<AnchorEntry,256> anchors;
      Time stamp;
      string checksum;
    };

    enum AnchorOp { ADD=0, UPDATE=1, REMOVE=2 };

    @appendable struct AnchorDelta {
      @key string set_id;
      AnchorOp op;
      AnchorEntry entry;
      uint64 revision;
      Time stamp;
      string post_checksum;
    };

    @appendable struct AnchorSetRequest {
      @key string set_id;
      uint64 up_to_revision;
    };

    @appendable struct AnchorSetResponse {
      @key string set_id;
      uint64 revision;
      AnchorSet set;
    };

  }; // module anchors
};

```

## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The VIO profile carries raw and fused IMU/magnetometer samples. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **VIO / Inertial Extension 1.0**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS VIO/Inertial 1.2

module spatial {
  module vio {

    typedef spatial::core::Time Time;

    // IMU calibration
    @appendable struct ImuInfo {
      @key string imu_id;
      string frame_id;
      double accel_noise_density;    // (m/s^2)/√Hz
      double gyro_noise_density;     // (rad/s)/√Hz
      double accel_random_walk;      // (m/s^3)/√Hz
      double gyro_random_walk;       // (rad/s^2)/√Hz
      Time   stamp;
    };

    // Raw IMU sample
    @appendable struct ImuSample {
      @key string imu_id;
      double accel[3];               // m/s^2
      double gyro[3];                // rad/s
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    // Magnetometer
    @appendable struct MagnetometerSample {
      @key string mag_id;
      double mag[3];                 // microtesla
      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
    };

    // Convenience raw 9-DoF bundle
    @appendable struct SensorFusionSample {
      @key string fusion_id;         // e.g., device id
      double accel[3];               // m/s^2
      double gyro[3];                // rad/s
      double mag[3];                 // microtesla
      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
    };

    // Fused state (orientation ± position)
    enum FusionMode { ORIENTATION_3DOF = 0, ORIENTATION_6DOF = 1, POSE_6DOF = 2 };
    enum FusionSourceKind { EKF = 0, AHRS = 1, VIO = 2, IMU_ONLY = 3, MAG_AIDED = 4, AR_PLATFORM = 5 };

    @appendable struct FusedState {
      @key string fusion_id;
      FusionMode       mode;
      FusionSourceKind source_kind;

      double q[4];                   // quaternion (w,x,y,z)
      boolean has_position;
      double t[3];                   // meters, in frame_id

      double gravity[3];             // m/s^2 (NaN if unknown)
      double lin_accel[3];           // m/s^2 (NaN if unknown)
      double gyro_bias[3];           // rad/s (NaN if unknown)
      double accel_bias[3];          // m/s^2 (NaN if unknown)

      double cov_orient[9];          // 3x3 covariance (NaN if unknown)
      double cov_pos[9];             // 3x3 covariance (NaN if unknown)

      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
      double quality;                // 0..1
    };

  }; // module vio
};

```

### **SLAM Frontend Extension 1.0**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS SLAM Frontend 1.2

module spatial {
  module slam_frontend {

    // Reuse core: Time, etc.
    typedef spatial::core::Time Time;

    // Camera calibration
    enum DistortionModelKind { NONE = 0, RADTAN = 1, EQUIDISTANT = 2, KANNALA_BRANDT = 3 };

    @appendable struct CameraInfo {
      @key string camera_id;
      uint32 width;  uint32 height;   // pixels
      double fx; double fy;           // focal (px)
      double cx; double cy;           // principal point (px)
      DistortionModelKind dist_kind;
      sequence<double, 8> dist;       // model params (bounded)
      string frame_id;                // camera frame
      Time   stamp;                   // calib time (or 0 if static)
    };

    // 2D features & descriptors per keyframe
    @appendable struct Feature2D {
      double u; double v;     // pixel coords
      float  scale;           // px
      float  angle;           // rad [0,2π)
      float  score;           // detector response
    };

    @appendable struct KeyframeFeatures {
      @key string node_id;                  // keyframe id
      string camera_id;
      string desc_type;                     // "ORB32","BRISK64","SPT256Q",...
      uint32 desc_len;                      // bytes per descriptor
      boolean row_major;                    // layout hint
      sequence<Feature2D, 4096> keypoints;  // ≤4096
      sequence<uint8, 1048576> descriptors; // ≤1 MiB packed bytes
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    // Optional cross-frame matches
    @appendable struct FeatureMatch {
      string node_id_a;  uint32 idx_a;
      string node_id_b;  uint32 idx_b;
      float  score;      // similarity or distance
    };

    @appendable struct MatchSet {
      @key string match_id;                // e.g., "kf_12<->kf_18"
      sequence<FeatureMatch, 8192> matches;
      Time   stamp;
      string source_id;
    };

    // Sparse 3D landmarks & tracks (optional)
    @appendable struct Landmark {
      @key string lm_id;
      string map_id;
      double p[3];
      double cov[9];                       // 3x3 pos covariance; NaN if unknown
      sequence<uint8, 4096> desc;          // descriptor bytes
      string desc_type;
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    @appendable struct TrackObs {
      string node_id;                      // observing keyframe
      double u; double v;                  // pixel coords
    };

    @appendable struct Tracklet {
      @key string track_id;
      string lm_id;                        // optional link to Landmark
      sequence<TrackObs, 64> obs;          // ≤64 obs
      string source_id;
      Time   stamp;
    };

  }; // module slam_frontend
};

```

### **Semantics / Perception Extension 1.0**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Semantics 1.2

module spatial {
  module semantics {

    typedef spatial::core::Time Time;
    typedef spatial::core::TileKey TileKey;

    // 2D detections per keyframe (image space)
    @appendable struct Detection2D {
      @key string det_id;       // unique per publisher
      string node_id;           // keyframe id
      string camera_id;         // camera
      string class_id;          // ontology label
      float  score;             // [0..1]
      float  bbox[4];           // [u_min,v_min,u_max,v_max] (px)
      boolean has_mask;         // if a pixel mask exists
      string  mask_blob_id;     // BlobChunk ref (role="mask")
      Time   stamp;
      string source_id;
    };

    @appendable struct Detection2DSet {
      @key string set_id;                 // batch id (e.g., node_id + seq)
      string node_id;
      string camera_id;
      sequence<Detection2D, 256> dets;    // ≤256
      Time   stamp;
      string source_id;
    };

    // 3D detections in world/local frame (scene space)
    @appendable struct Detection3D {
      @key string det_id;
      string frame_id;           // e.g., "map" (pose known elsewhere)
      boolean has_tile;
      TileKey tile_key;          // valid when has_tile = true

      string class_id;           // semantic label
      float  score;              // [0..1]

      // Oriented bounding box in frame_id
      double center[3];          // m
      double size[3];            // width,height,depth (m)
      double q[4];               // orientation (w,x,y,z)

      // Uncertainty (optional; NaN if unknown)
      double cov_pos[9];         // 3x3 position covariance
      double cov_rot[9];         // 3x3 rotation covariance

      // Optional instance tracking
      string track_id;

      Time   stamp;
      string source_id;
    };

    @appendable struct Detection3DSet {
      @key string set_id;                 // batch id
      string frame_id;                    // common frame for the set
      boolean has_tile;
      TileKey tile_key;                   // valid when has_tile = true
      sequence<Detection3D, 128> dets;    // ≤128
      Time   stamp;
      string source_id;
    };

  }; // module semantics
};

```

### **AR + Geo Extension 1.0**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS AR+Geo 1.2

module spatial {
  module argeo {

    typedef spatial::core::Time Time;
    typedef spatial::core::PoseSE3 PoseSE3;
    typedef spatial::core::GeoPose GeoPose;

    @appendable struct NodeGeo {
      string map_id;
      @key string node_id;      // same id as core::Node
      PoseSE3 pose;             // local pose in map frame
      GeoPose geopose;          // corresponding global pose (WGS84/ECEF/ENU/NED)
      double  cov[36];          // 6x6 covariance in local frame; NaN if unknown
      Time    stamp;
      string  frame_id;         // local frame
      string  source_id;
      uint64  seq;
      uint64  graph_epoch;
    };

  }; // module argeo
};

```

## **Appendix E: Provisional Extension Examples**

The following examples illustrate how provisional extensions might be used in practice. They are not normative and are provided only to show how Neural and Agent profiles could appear on the wire.

### **Example: Neural Extension (Provisional)**

*This example shows how a service might publish metadata for a Gaussian splat field covering part of a city block.*

```idl
neural::NeuralFieldMeta {
  field_id = "sf-market-01";
  kind = GAUSSIANS;
  encoding = "gsplat-2024";
  min_x = -50; min_y = -20; min_z = 0;
  max_x = 80;  max_y = 40;  max_z = 60;
  base_res_x = 0; base_res_y = 0; base_res_z = 0; // not applicable
  channels = 4; // RGBA
  blob_ids = ["blob:shard01", "blob:shard02"];
  revision = 12;
  stamp = { sec=1700000000, nsec=0 };
}

```

### **Example: Agent Extension (Provisional)**

*This example shows how an AI planner could issue a navigation task and later update its status.*

```idl
agent::Task {
  task_id = "route-2025-001";
  kind = "navigate";
  subject_id = "robot-42";
  inputs = ["geo.anchor:main-entrance"];
  due = { sec=1700000500, nsec=0 };
  notes = "Deliver package to lobby.";
}

agent::TaskStatus {
  task_id = "route-2025-001";
  status = RUNNING;
  result_uri = "";
  log = "En route, ETA 3 min.";
  stamp = { sec=1700000520, nsec=0 };
}

```
