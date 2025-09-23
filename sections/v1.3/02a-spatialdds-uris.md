## **3. SpatialDDS URIs**

SpatialDDS uses URIs to provide stable, global identifiers for anchors, content, and services. URIs are short handles that applications can share across devices, clouds, and transports, and they can be dereferenced to retrieve a manifest with more details. Example manifests illustrating these identifiers are provided in Section 4 (Example Manifests).

**Syntax**

```
spatialdds://<authority>/<zone>/<type>/<id>[;v=<version>]
```

**Components**

* `<authority>` identifies the organization responsible for issuing the URI. It **MUST** be a DNS hostname or delegated subdomain that the issuer controls. Only lowercase ASCII letters (`a–z`), digits (`0–9`), and hyphen (`-`) are permitted within a label, and labels **MUST** be separated by dots (`.`). Comparison of `<authority>` values is case-insensitive, but URIs **SHOULD** be serialized in lowercase to avoid ambiguity.
* `<zone>` scopes identifiers within an authority (for example, a facility, campus, or logical shard). It **MUST** be a single path segment composed of 1–64 characters from the set `[a-z0-9_-]` and **MUST NOT** begin or end with `-` or `_`. `<zone>` values are case-sensitive, and authorities are responsible for guaranteeing uniqueness within each zone.
* `<type>` selects the semantic kind of resource being referenced. It **MUST** exactly match one of the allowed values listed below and is case-sensitive.
* `<id>` is the stable identifier assigned to the resource of the given `<type>`. It **MUST** be a 26-character Crockford Base32 ULID rendered in uppercase ASCII (`0–9`, `A–Z`, excluding `I`, `L`, `O`, and `U`). Implementations **MUST** treat `<id>` values as case-sensitive.
* `;v=<version>` is an optional semicolon-delimited parameter that advertises a specific manifest revision. When present, the `v` key **MUST** be lowercase and the `<version>` value **MUST** be 1–32 characters drawn from `[A-Za-z0-9._-]`. Authorities **MAY** use this parameter to differentiate immutable snapshots or schema-compatible updates; consumers **MUST** ignore unknown parameters.

**Allowed `<type>` values**

| `<type>` | IDL mapping | Description |
| --- | --- | --- |
| `anchor` | `spatial::anchors::AnchorEntry.anchor_id` | Durable localization anchor identifiers published through the Anchors profile. |
| `anchor-set` | `spatial::anchors::AnchorSet.set_id` | Anchor set bundles and registry revisions available through the Anchors profile. |
| `content` | `spatial::disco::ContentAnnounce.content_id` | Spatial content or experience manifests announced via the Discovery profile. |
| `service` | `spatial::disco::ServiceAnnounce.service_id` | Service manifests (e.g., VPS, mapping, relocalization) announced via the Discovery profile. |

Authorities **MUST** only issue URIs with `<type>` values from this table and **MUST** ensure that the `<id>` corresponds to the referenced IDL field. Additional types require an extension to this specification.

**Example**

```
spatialdds://museum.example.org/hall1/anchor/01J8QDFQX3W9X4CEX39M9ZP6TQ;v=3
```

To use a URI, a client asks the authority (e.g., `museum.example.org`) for the corresponding manifest. A manifest is a JSON document that describes the object (pose, coverage, endpoints, etc.). The URI is just the pointer; the manifest carries the details. Section 4 (Example Manifests) links several representative payloads that match the URIs defined here.

#### Resolving `spatialdds://` URIs

Clients dereference a SpatialDDS URI by contacting the named `<authority>` over HTTPS and retrieving the manifest that the URI points to. Resolution **MUST** follow these rules:

* **Resolver discovery**
  * Authorities that support SpatialDDS **MUST** publish a resolver descriptor at `https://<authority>/.well-known/spatialdds`. The document **MUST** be served with `Content-Type: application/json` and **MUST** contain at least a `resolver` member whose value is an absolute HTTPS URL prefix used for manifest lookups (for example, `{ "resolver": "https://api.example.org/spatialdds" }`).
  * The descriptor **MAY** contain an `alt_transports` array advertising additional retrieval mechanisms (e.g., `dds+tcp://…`, `ipfs://…`). Each entry **MUST** be a URI template describing how to obtain the manifest payload, and clients **MAY** use them according to local policy.
  * Clients **SHOULD** fetch and cache the descriptor for up to 24 hours. If the descriptor is unreachable, clients **MUST** fall back to the default resolver prefix `https://<authority>/.well-known/spatialdds/manifest`.

* **Manifest request**
  * Clients **MUST** resolve the URI path to `<resolver>/<zone>/<type>/<id>` using the prefix from the descriptor (or the default prefix when no descriptor is available). When the URI includes `;v=<version>`, the request **MUST** append the query parameter `?v=<version>` to the lookup URL without altering case.
  * Clients **MUST** issue an HTTPS `GET` request using HTTP/1.1 or HTTP/2, validate the server certificate against the `<authority>` hostname, and include the header `Accept: application/spatialdds+json, application/json;q=0.8`. Authorities **MUST NOT** require authentication for public manifests but **MAY** demand HTTP authentication or client certificates for protected manifests; such requirements **MUST** be advertised in the resolver descriptor via an `auth` member.
  * Resolver responses **MUST** return a manifest encoded as UTF-8 JSON with `Content-Type: application/spatialdds+json`. Authorities **MAY** add a `profile` parameter (e.g., `application/spatialdds+json;profile="anchor"`) so clients can verify the type before parsing. See Section 4 (Example Manifests) for representative resolver payloads.

* **Caching and expiry**
  * Resolver responses **MUST** include either a strong `ETag` or a `Last-Modified` header together with a `Cache-Control` directive. Clients **MUST** honor the provided directives but **MUST NOT** cache a manifest for longer than 7 days without revalidation. Implementations **SHOULD** revalidate with `If-None-Match`/`If-Modified-Since` when a cached entry is older than 1 hour and **MAY** respect shorter `max-age` values supplied by the authority.
  * Authorities **MAY** provide per-version immutable manifests by returning `Cache-Control: max-age=31536000, immutable` when the request specifies `;v=<version>`. Clients **MUST** treat such responses as immutable snapshots and **MUST** continue to revalidate versionless lookups on each use.

* **Error handling**
  * `404 Not Found` indicates that the URI is unknown; clients **MUST** stop retrying until new information is available. `410 Gone` signals that the resource has been permanently retired, and clients **MUST** evict cached copies. `451 Unavailable For Legal Reasons` communicates legal withholding and **MUST** be surfaced to users when possible.
  * `429 Too Many Requests` instructs clients to back off according to the `Retry-After` header. Temporary errors (`5xx`) **MAY** be retried with exponential backoff. Authorities **MAY** redirect (`301`/`308`) to another HTTPS origin; clients **MUST** follow redirects limited to the same `<authority>` or to resolver URLs listed in the descriptor.

Authorities that support non-HTTPS transports (for example, DDS-native discovery topics or content-addressed networks) advertise them through the resolver descriptor’s `alt_transports` field. Clients **MAY** use these alternatives when HTTPS is unavailable or policy prefers an on-bus manifest cache, but HTTPS resolution **MUST** remain supported so that any SpatialDDS URI can be dereferenced using common web tooling.
