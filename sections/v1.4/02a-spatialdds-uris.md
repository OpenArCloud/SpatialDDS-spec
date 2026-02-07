## **7. SpatialDDS URIs**

### 7.1 Why SpatialDDS URIs matter

SpatialDDS URIs are the shorthand that lets participants talk about anchors, content, and services without exchanging the full manifests up front. They bridge human concepts—"the anchor in Hall 1" or "the localization service for Midtown"—with machine-readable manifests that deliver the precise data, coordinate frames, and capabilities needed later in the flow.

### 7.2 Key ingredients

Every SpatialDDS URI names four ideas:

* **Authority** – who owns the namespace and keeps the identifiers stable.
* **Zone** – a slice of that authority’s catalog, such as a venue, fleet, or logical shard.
* **Type** – whether the reference points to an anchor, a bundle of anchors, a piece of content, or a service endpoint.
* **Identifier (with optional version)** – the specific record the manifest will describe.

The exact tokens and encoding rules are defined by the individual profiles, but at a glance the URIs read like `spatialdds://authority/zone/type/id;v=version`. Readers only need to recognize which part expresses ownership, scope, semantics, and revision so they can reason about the rest of the system.

Formal syntax is given in Appendix F.

### 7.3 Working with SpatialDDS URIs

Once a URI is known, clients resolve it according to the **SpatialURI Resolution rules** (§7.5). The manifest reveals everything the client needs to act: anchor poses, dependency graphs for experiences, or how to reach a service. Because URIs remain lightweight, they are easy to pass around in tickets, QR codes, or discovery topics while deferring the heavier data fetch until runtime.

### 7.4 Examples

```text
spatialdds://museum.example.org/hall1/anchor/01J8QDFQX3W9X4CEX39M9ZP6TQ
spatialdds://city.example.net/downtown/service/01HA7M6XVBTF6RWCGN3X05S0SM;v=2024-q2
spatialdds://studio.example.com/stage/content/01HCQF7DGKKB3J8F4AR98MJ6EH
```

In the manifest samples later in this specification, each of these identifiers expands into a full JSON manifest. Reviewing those examples shows how a single URI flows from a discovery payload, through manifest retrieval, to runtime consumption.

Authorities SHOULD use DNS hostnames they control to ensure globally unique, delegatable SpatialDDS URIs.

### 7.5 SpatialURI Resolution (Normative)

This section defines the **required baseline** mechanism for resolving SpatialDDS URIs to concrete resources (for example, JSON manifests). It does not change any IDL definitions.

#### 7.5.1 Resolution Order (Normative)

When resolving a `spatialdds://` URI, a client MUST perform the following steps in order:

1. **Validate syntax** — The URI MUST conform to Appendix F.
2. **Local cache** — If a valid, unexpired cache entry exists, the client MUST use it.
3. **Advertised resolver** — If discovery metadata supplies a resolver endpoint, the client MUST use it.
4. **HTTPS fallback** — The client MUST attempt HTTPS resolution as defined below.
5. **Failure** — If unresolved, the client MUST treat the resolution as failed.

#### 7.5.2 HTTPS Resolution (Required Baseline)

All SpatialDDS authorities **MUST** support HTTPS-based resolution.

##### Resolver Metadata (Normative)

Each authority **MUST** expose the resolver metadata at:

```
https://{authority}/.well-known/spatialdds-resolver
```

Minimum response body:

```json
{
  "authority": "example.com",
  "https_base": "https://example.com/spatialdds/resolve",
  "cache_ttl_sec": 300
}
```

##### Resolve Request (Normative)

Clients resolve a SpatialURI via:

```
GET {https_base}?uri={urlencoded SpatialURI}
```

Example:

```
GET https://example.com/spatialdds/resolve?uri=spatialdds://example.com/zone:austin/manifest:vps
```

##### Resolve Response (Normative)

On success, servers **MUST** return:

- HTTP `200 OK`
- The resolved resource body
- A correct `Content-Type`
- At least one integrity signal (`ETag`, `Digest`, or a checksum field in the body)

#### 7.5.3 Error Handling (Normative)

Servers **MUST** use standard HTTP status codes:

- `400` invalid URI
- `404` not found
- `401` / `403` unauthorized
- `5xx` server error

Clients **MUST** treat any non-200 response as resolution failure.

#### 7.5.4 Security (Normative)

- HTTPS resolution **MUST** use TLS.
- Authentication **MAY** be required when advertised.
- Clients **MAY** enforce local trust policies.
