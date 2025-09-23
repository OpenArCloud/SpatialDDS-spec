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
