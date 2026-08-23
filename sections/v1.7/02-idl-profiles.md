// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.7 (© Open AR Cloud Initiative)

## **3\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

_See §2 Conventions for global normative rules._

### **3.1 IDL Profile Versioning & Negotiation (Normative)**

SpatialDDS uses semantic versioning of the form `spatial.<profile>/MAJOR.MINOR`.

* **MAJOR** increments for breaking schema or wire changes.
* **MINOR** increments for additive, compatible changes.

> **Pre-adoption instability (Normative).** The compatibility contract above takes effect upon formal adoption of this specification. Throughout the 1.x pre-adoption series, MINOR revisions MAY include breaking schema or wire changes. Each revision's Profile Matrix (§3.5) and changelog identify breaking changes explicitly. Topic names retain the `/v1` segment through the 1.x series notwithstanding such changes. 1.7 is a stamped release; subsequent breaking changes land in 1.8 or later, not in revisions to this document.

Profile identifiers use the single form `spatial.<profile>/MAJOR.MINOR` (e.g., `spatial.core/1.7`) everywhere: prose, manifests, discovery payloads, and IDL constants.

Participants advertise supported ranges via `caps.supported_profiles` (discovery) and manifest capabilities blocks. Consumers select the **highest compatible minor** within any shared major. Backward-compatibility clauses from 1.3 are retired; implementations only negotiate within their common majors. SpatialDDS 1.7 uses a single canonical quaternion order `(x, y, z, w)` across manifests, discovery payloads, and IDL messages.

### **3.2 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. All quaternion fields follow the OGC GeoPose component order `(x, y, z, w)` so orientation data can flow between GeoPose-aware systems without reordering. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

**GNSS diagnostics (Normative):** `NavSatStatus` is a companion to `GeoPose` that carries GNSS receiver diagnostics (fix type, DOP, satellite count, ground velocity) on a parallel topic. It is published alongside GNSS-derived GeoPoses and MUST NOT be used to annotate non-GNSS localization outputs.

**NavSatStatus Topic (Normative):** NavSatStatus SHOULD be published on the topic `spatialdds/geo/<gnss_id>/navsat_status/v1`, where `<gnss_id>` matches the `@key gnss_id` in the struct. NavSatStatus SHOULD use the same QoS profile as the associated GeoPose stream.

NavSatStatus is registered as type `navsat_status` in the registered types table (§3.3.2). Producers publishing GNSS-derived GeoPoses SHOULD include a `TopicMeta` entry for NavSatStatus in their `Announce.topics[]`. Consumers MAY discover NavSatStatus topics through standard discovery mechanisms.

**GeoPose orientation reference (Normative).** `GeoPose` encodes WGS84 position (`lat_deg`, `lon_deg`, `alt_m`); its quaternion is always expressed in the local ENU tangent frame at that position, consistent with OGC GeoPose. Consumers needing another axis convention apply the §2.12 conversions. Local metric poses use `FramedPose`, whose `FrameRef` (with `coord_convention`) governs axes; `GeoPose` and `FramedPose` never require reconciliation of two convention systems on the same sample.

**Planned Trajectory (Normative):** `PlannedTrajectory` represents an agent's intended future path. It is published at the agent's replan rate (typically 1–10 Hz) and superseded by each new plan revision. Consumers MUST use the most recent `plan_revision` for a given `agent_id` and discard older revisions.

Waypoint timestamps represent planned arrival times in the future. Consumers SHOULD treat these as estimates subject to replanning. The `position_uncertainty_m` field, when present, indicates the planner's confidence in the waypoint position and typically grows with distance from the current state.

PlannedTrajectory is registered as type `planned_trajectory` in §3.3.2 and SHOULD be advertised on the topic `spatialdds/<scene>/plan/<agent_id>/trajectory/v1` using the `EVENT_RT` QoS profile.

**Entity Binding (Normative):** `EntityBinding` provides cross-topic correlation without imposing a scene graph hierarchy. Multiple publishers MAY publish bindings for the same `entity_id`; consumers MUST merge component lists and resolve conflicts (e.g., by preferring the binding with the most recent `stamp` or the highest-confidence source).

EntityBinding is intentionally flat — it does not express parent-child relationships, ownership, or transform inheritance. Consumers requiring hierarchical scene graph semantics SHOULD build their own entity hierarchy from the bindings received.

EntityBinding is registered as type `entity_binding` in §3.3.2 and SHOULD be advertised on the topic `spatialdds/<scene>/entity/binding/v1`. Publishers SHOULD use RELIABLE + TRANSIENT_LOCAL QoS so that late-joining consumers receive the current set of entity correlations.

#### **Blob Reassembly (Normative)**

Blob payloads are transported as `BlobChunk` sequences. Consumers MUST be prepared for partial delivery and SHOULD apply a per-blob timeout window based on expected rate and `total_chunks`.

Chunk payloads are bounded at 65,535 bytes for compatibility with common DDS language bindings' sequence-bound limits. Larger content is carried in more chunks; per-chunk `crc32` and blob-level checksums are unchanged.

- **Timeout guidance:** Consumers SHOULD apply a per-blob timeout of at least `2 × (total_chunks / expected_rate)` seconds when an expected rate is known.
- **Failure handling:** If all chunks have not arrived within this window under **RELIABLE** QoS, the consumer SHOULD discard the partial blob and MAY re-request it via `SnapshotRequest`.
- **BEST_EFFORT behavior:** Under **BEST_EFFORT** QoS, consumers MUST NOT assume complete delivery and SHOULD treat blobs as opportunistic.
- **Memory pressure:** Consumers MAY discard partial blobs early under memory pressure, but MUST NOT treat them as valid payloads.

#### Frame Identifiers (Reference)

SpatialDDS uses structured frame references via the `FrameRef { uuid, fqn, coord_convention? }` type. The optional `coord_convention` (added in 1.6) selects the axis convention for poses in this frame; see §2.12 for the full convention table and chaining rules. When absent, consumers MUST assume `ENU`.
See *Appendix G Frame Identifiers (Normative)* for the complete definition and naming rules.

Each Transform expresses a pose that maps coordinates from the `from` frame into the `to` frame (parent → child).

### **3.3 Discovery**

Discovery is how SpatialDDS peers **find each other**, **advertise what they publish**, and **select compatible streams**. Deployments can expose discovery using a **DDS binding** (query/announce on well-known topics), an **HTTP binding** (a REST endpoint that accepts spatial queries and returns service manifests), or both. HTTP resolvers may act as gateways to a DDS bus without changing the client-facing contract.

#### How it works (at a glance)
1. **Announce** — each node periodically publishes an announcement with capabilities and topics (DDS), or registers its manifest with an HTTP discovery service.
2. **Query** — clients publish spatial filters on the DDS bus (`CoverageQuery`), or issue an HTTP search request to `/.well-known/spatialdds/search`.
3. **Select** — clients subscribe to chosen topics; negotiation picks the highest compatible minor per profile.

#### **3.3.0 Discovery Layers & Bootstrap (Normative)**

SpatialDDS distinguishes three discovery layers:

- **Layer 1 — Network Bootstrap:** how a device discovers that a SpatialDDS deployment exists and obtains initial connection parameters. This is transport and access-network dependent (mDNS, Geospatial DNS-SD, QR codes, HTTPS well-known path).
- **Layer 1.5 — HTTP Discovery (optional):** how a device, without joining a DDS domain, queries for services by spatial region via an HTTP endpoint. This is the bridge between bootstrap and on-bus discovery for Internet-scale deployments where the client and service may be on different networks.
- **Layer 2 — On-Bus Discovery:** how a device, once connected to a DDS domain, discovers services, coverage, and streams via DDS topics. This is what the Discovery profile's IDL types define.

Layer 1 mechanisms deliver a **Bootstrap Manifest** that provides the parameters needed to transition to Layer 1.5 or Layer 2. Layer 1.5 delivers **Service Manifests** (§8.2.3) that provide the DDS connection parameters needed to transition to Layer 2. Clients MAY skip Layer 1.5 if Layer 1 already provides sufficient connection information (e.g., local mDNS bootstrap on the venue LAN).

On-bus bootstrap exchanges (a participant querying an already-joined bus for deployment parameters) are deployment-specific and not standardized; the Layer 1 mechanisms above are the interoperable bootstrap path.

##### **Bootstrap Manifest (Normative)**

A bootstrap manifest is a small JSON document resolved by Layer 1 mechanisms:

```json
{
  "spatialdds_bootstrap": "1.7",
  "domain_id": 42,
  "initial_peers": [
    "udpv4://192.168.1.100:7400",
    "udpv4://10.0.0.50:7400"
  ],
  "partitions": ["venue/museum-west"],
  "discovery_topic": "spatialdds/discovery/announce/v1",
  "manifest_uri": "spatialdds://museum.example.org/west/service/discovery"
}
```

**Field definitions**

| Field | Required | Description |
|---|---|---|
| `spatialdds_bootstrap` | REQUIRED | Bootstrap schema version (e.g., "1.7") |
| `domain_id` | REQUIRED | DDS domain ID to join |
| `initial_peers` | REQUIRED | One or more DDS peer locators for initial discovery |
| `partitions` | OPTIONAL | DDS partition(s) to join. Empty or absent means default partition. |
| `discovery_topic` | OPTIONAL | Override for the well-known announce topic. Defaults to `spatialdds/discovery/announce/v1`. |
| `manifest_uri` | OPTIONAL | A `spatialdds://` URI for the deployment's root manifest. |
| `auth_hint` | OPTIONAL | Auth-URI list per §3.3 `auth_hint` grammar. Empty or absent means no authentication hint. |

**Normative rules**

- `domain_id` MUST be a valid DDS domain ID (0–232 per the RTPS specification; higher values may require non-standard configuration).
- `initial_peers` MUST contain at least one locator. Locator format follows the DDS implementation's peer descriptor syntax.
- Consumers SHOULD attempt all listed peers and use the first that responds.
- The bootstrap manifest is a discovery aid, not a security boundary. Deployments requiring authentication MUST use DDS Security or an equivalent transport-level mechanism.

##### **Well-Known HTTPS Path (Normative)**

Clients MAY fetch the bootstrap manifest from:

```
https://{authority}/.well-known/spatialdds/bootstrap
```

The response MUST be `application/json` using the bootstrap manifest schema. Servers SHOULD set `Cache-Control` headers appropriate to their deployment (e.g., `max-age=300`).

**Note:** Three well-known paths are defined under the single `/.well-known/spatialdds` namespace (one RFC 8615 registration). The bootstrap path (`/.well-known/spatialdds/bootstrap`) returns a Bootstrap Manifest. The resolver metadata path (`/.well-known/spatialdds/resolver`) returns resolver metadata for URI resolution (§7.5.2). The search path (`/.well-known/spatialdds/search`) accepts spatial discovery queries and returns matching service manifests. All three serve distinct functions and MAY coexist on the same authority.

##### **HTTP Discovery Search Binding (Normative)**

The HTTP discovery search binding allows clients to query for SpatialDDS services by spatial region without joining a DDS domain. It mirrors the on-bus `CoverageQuery` / `CoverageResponse` pattern over HTTP, using the same coverage semantics (§3.3.4) and returning standard service manifests (§8.2.3).

**Endpoint:**

```
POST https://{authority}/.well-known/spatialdds/search
Content-Type: application/json
```

**Request body:**

| Field | Type | Required | Description |
|---|---|---|---|
| `coverage` | array of CoverageElement | REQUIRED | One or more spatial regions of interest. Uses the same `CoverageElement` schema as `CoverageQuery.coverage` — `bbox`, `aabb`, `crs`, `frame_ref`, `global`. |
| `filter` | CoverageFilter | OPTIONAL | Structured filter matching `CoverageFilter` — `type_in`, `qos_profile_in`, `module_id_in`. Empty arrays mean "match all." |
| `kind` | array of string | OPTIONAL | Filter by service kind: `"VPS"`, `"MAPPING"`, `"RELOCAL"`, `"SEMANTICS"`, `"STORAGE"`, `"CONTENT"`, `"ANCHOR_REGISTRY"`, `"OTHER"`. Empty or absent means all kinds. |
| `geohash` | string | OPTIONAL | Geohash string (3–7 characters). Shorthand for an earth-fixed bbox query. When present, the server expands the geohash to its bounding box and treats it as an additional coverage element. |
| `max_results` | integer | OPTIONAL | Maximum number of results to return (default: server-defined, recommended ≤100). |
| `page_token` | string | OPTIONAL | Opaque token from a previous response for pagination. |

**Minimal example — query by geohash:**

```http
POST /.well-known/spatialdds/search
Content-Type: application/json

{
  "geohash": "9q8yy"
}
```

**Full example — query by bbox with service kind filter:**

```http
POST /.well-known/spatialdds/search
Content-Type: application/json

{
  "coverage": [
    {
      "crs": "EPSG:4326",
      "bbox": [-122.420, 37.785, -122.405, 37.800]
    }
  ],
  "kind": ["VPS"],
  "filter": {
    "type_in": ["geopose"],
    "qos_profile_in": [],
    "module_id_in": []
  },
  "max_results": 10
}
```

**Response body:**

On success, the server MUST return HTTP `200 OK` with `Content-Type: application/json`. The body is a JSON object:

| Field | Type | Required | Description |
|---|---|---|---|
| `results` | array of Manifest | REQUIRED | Array of service manifests (§8.2.3 schema). Empty array if no services match. |
| `next_page_token` | string | OPTIONAL | Opaque token for fetching the next page. Absent or empty string means no more results. |

```json
{
  "results": [
    {
      "id": "spatialdds://acme-vps.example/sf-downtown/service/vps-main",
      "profile": "spatial.manifest/1.7",
      "rtype": "service",
      "service": {
        "service_id": "vps-main",
        "kind": "VPS",
        "name": "SF Downtown Visual Positioning",
        "org": "acme-vps.example",
        "version": "2025-q4",
        "connection": {
          "domain_id": 100,
          "initial_peers": ["tcpv4://vps.acme-vps.example:7400"],
          "partitions": ["sf/downtown"]
        },
        "topics": [
          { "name": "spatialdds/vps/query/v1", "type": "vps_query", "version": "v1", "qos_profile": "VPS_REQ" },
          { "name": "spatialdds/vps/result/v1", "type": "geopose", "version": "v1", "qos_profile": "VPS_RESP" }
        ]
      },
      "coverage": {
        "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
        "has_bbox": true,
        "bbox": [-122.420, 37.785, -122.405, 37.800],
        "global": false
      },
      "stamp": { "sec": 1735689600, "nanosec": 0 },
      "ttl_sec": 3600
    }
  ],
  "next_page_token": ""
}
```

**GET convenience form:**

For simple geohash-based queries (e.g., from a Geospatial DNS-SD `muri`), servers MUST also support:

```
GET https://{authority}/.well-known/spatialdds/search?geohash={geohash}
GET https://{authority}/.well-known/spatialdds/search?geohash={geohash}&kind={kind}
```

The GET form is equivalent to a POST with `{"geohash": "{geohash}"}` (and optional `kind` filter). The response format is identical.

**Spatial matching semantics:**

The server evaluates spatial overlap using the same *intersects* predicate as the on-bus `CoverageQuery`: a service matches if its coverage region intersects any of the requested coverage elements. When `geohash` is provided, the server expands it to its bounding box and applies the same intersection test. Services with `coverage.global == true` match all queries.

**Error handling:**

| Status | Meaning |
|---|---|
| `200` | Success. Body contains results (may be empty). |
| `400` | Malformed request (invalid geohash, missing coverage, bad JSON). |
| `401` / `403` | Authentication required or insufficient. |
| `404` | The `/.well-known/spatialdds/search` endpoint is not supported by this authority. |
| `429` | Rate limited. Client SHOULD retry with exponential backoff. |
| `5xx` | Server error. |

**Normative rules:**

- Servers implementing the HTTP discovery search binding MUST support the POST form. The GET convenience form is also REQUIRED for interoperability with the Geospatial DNS-SD binding.
- The response MUST use the §8.2.3 service manifest schema for each result. Clients MUST be able to extract `service.connection` from any result and use it to join the service's DDS domain.
- Servers MUST respect the Coverage Model (§3.3.4) when evaluating spatial overlap: `coverage_frame_ref`, `bbox`, `aabb`, and `global` flags all apply.
- Servers SHOULD set `Cache-Control` headers appropriate to the deployment. Responses to geohash queries at precision 5 (city-district scale) MAY be cached for 60–300 seconds.
- Pagination follows the same contract as on-bus `CoverageResponse`: tokens are opaque, results are best-effort, and an empty `next_page_token` means no further pages.
- Servers MAY return results for all resource types (services, content, anchor sets) or restrict to services only. When `kind` is absent, servers SHOULD return services only unless the client explicitly requests other types via the `filter` field.
- The HTTP search endpoint and the on-bus `CoverageQuery` are independent mechanisms. Servers MAY implement one or both. Servers that implement both SHOULD return consistent results for equivalent queries.
- HTTPS with TLS is REQUIRED. Authentication follows the same rules as §7.5.4.

**Relationship to other well-known paths:**

| Path | Function | Returns |
|---|---|---|
| `/.well-known/spatialdds/bootstrap` | Bootstrap manifest | Bootstrap Manifest (domain_id, peers, partitions) |
| `/.well-known/spatialdds/resolver` | Resolver metadata | Resolver metadata (https_base, cache_ttl) |
| `/.well-known/spatialdds/search` | **Spatial discovery query** | **Array of service manifests** |

All three paths MAY coexist on the same authority. They serve distinct functions and do not conflict.

**Relationship to Geospatial DNS-SD:**

The Geospatial DNS-SD binding's `muri` TXT record value SHOULD point to the search endpoint's GET convenience form:

```
muri=https://discovery.example.org/.well-known/spatialdds/search?geohash=9q8yy
```

This directly connects the DNS bootstrap (Layer 1) to HTTP discovery (Layer 1.5) without requiring any intermediate resolution step.

##### **DNS-SD Binding (Normative)**

DNS-SD is the recommended first binding for local bootstrap.

**Service type:** `_spatialdds._udp`

**TXT record keys**

| Key | Maps to | Example |
|---|---|---|
| `ver` | `spatialdds_bootstrap` | `1.7` |
| `did` | `domain_id` | `42` |
| `part` | `partitions` (comma-separated) | `venue/museum-west` |
| `muri` | `manifest_uri` | `spatialdds://museum.example.org/west/service/discovery` |

**Resolution flow**

1. Device queries for `_spatialdds._udp.local` (mDNS) or `_spatialdds._udp.<domain>` (wide-area DNS-SD).
2. SRV record provides host and port for the initial DDS peer.
3. TXT record provides domain ID, partitions, and optional manifest URI.
4. Device constructs a bootstrap manifest from the SRV + TXT data and joins the DDS domain.
5. On-bus Discovery (Layer 2) takes over.

**Normative rules**

- `did` is REQUIRED in the TXT record.
- The SRV target and port MUST resolve to a reachable DDS peer locator.
- If `muri` is present, clients SHOULD resolve it after joining the domain to obtain full deployment metadata.

##### **Geospatial DNS-SD Binding (Normative)**

The geospatial DNS-SD binding allows a client with a GPS fix to discover SpatialDDS services by encoding its location as a geohash subdomain. This binding targets Internet-scale deployments where clients and services are on different networks.

**Subdomain pattern:**

```
_spatialdds._udp.<geohash>.geo.<authority>
```

where `<geohash>` is a standard base32 geohash [8] of the client's position and `<authority>` is the DNS zone hosting the discovery registry.

**Geohash precision levels**

| Characters | Cell size (approx.) | Typical use |
|---|---|---|
| 3 | ~156 km × 156 km | Metro region / country subdivision |
| 4 | ~39 km × 20 km | City |
| 5 | ~5 km × 5 km | District / neighborhood |
| 6 | ~1.2 km × 0.6 km | Block / venue cluster |
| 7 | ~153 m × 153 m | Single venue |

Clients SHOULD query at precision 5 (neighborhood scale) by default. Finer precision (6–7) is appropriate when the client has high-accuracy GNSS (RTK or similar).

**TXT record keys**

The TXT record uses the same key set as the local DNS-SD binding, with one addition:

| Key | Required | Description |
|---|---|---|
| `ver` | REQUIRED | Bootstrap schema version (e.g., `1.7`) |
| `did` | OPTIONAL | DDS domain ID. OPTIONAL because the geospatial binding's primary role is to hand off to an HTTP discovery service via `muri`, not to provide direct DDS connection. |
| `muri` | REQUIRED | HTTPS URL or `spatialdds://` URI for the discovery service, with the geohash passed as a query parameter or path segment. |
| `part` | OPTIONAL | DDS partition hint (comma-separated). |

**Resolution flow**

1. Client obtains its position (GPS, network location, or manual entry).
2. Client computes the base32 geohash at precision 5 (e.g., `37.7749°N, 122.4194°W` → `9q8yy`).
3. Client issues a DNS TXT query for `_spatialdds._udp.9q8yy.geo.<authority>`.
4. If the query returns `NXDOMAIN`, the client truncates to precision 4 (`9q8y`) and retries. This continues down to precision 3. If precision 3 also returns `NXDOMAIN`, bootstrap fails for this authority.
5. On success, the client extracts `muri` from the TXT record.
6. Client issues an HTTPS GET to the `muri` URL, which returns one or more SpatialDDS service manifests (§8.2.3) for services covering that geohash cell.
7. Client selects a service and connects using the `connection` hints in the manifest.

**Example DNS records (Route 53 / authoritative DNS)**

```
;; San Francisco downtown (~5 km² cell)
_spatialdds._udp.9q8yy.geo.spatialdds.example.org.  TXT  "ver=1.7" "muri=https://discovery.spatialdds.example.org/v1/services?geohash=9q8yy"

;; San Francisco marina district
_spatialdds._udp.9q8yk.geo.spatialdds.example.org.  TXT  "ver=1.7" "muri=https://discovery.spatialdds.example.org/v1/services?geohash=9q8yk"

;; London Soho
_spatialdds._udp.gcpvj.geo.spatialdds.example.org.  TXT  "ver=1.7" "muri=https://discovery.spatialdds.example.org/v1/services?geohash=gcpvj"
```

**Example HTTPS response** (from the `muri` endpoint)

The discovery service returns an array of standard SpatialDDS service manifests (§8.2.3):

```json
[
  {
    "id": "spatialdds://provider-a.example/sf-downtown/service/vps-main",
    "profile": "spatial.manifest/1.7",
    "rtype": "service",
    "service": {
      "service_id": "vps-main",
      "kind": "VPS",
      "name": "SF Downtown Visual Positioning",
      "org": "provider-a.example",
      "connection": {
        "domain_id": 100,
        "initial_peers": ["tcpv4://vps.provider-a.example:7400"]
      },
      "topics": [
        { "name": "spatialdds/vps/pose/v1", "type": "geopose", "version": "v1", "qos_profile": "POSE_RT" }
      ]
    },
    "coverage": {
      "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
      "has_bbox": true,
      "bbox": [-122.420, 37.785, -122.405, 37.800],
      "global": false
    },
    "stamp": { "sec": 1714070400, "nanosec": 0 },
    "ttl_sec": 3600
  }
]
```

**DNS zone delegation for federated operation**

Operators MAY delegate geohash-prefixed subdomains to independent authorities, enabling federated discovery where different organizations manage different geographic regions:

```
;; Top-level authority delegates San Francisco (geohash prefix "9q8") to provider A
9q8.geo.spatialdds.example.org.   NS  ns1.provider-a.example.

;; Top-level authority delegates London (geohash prefix "gcpv") to provider B
gcpv.geo.spatialdds.example.org.  NS  ns1.provider-b.example.
```

Each delegate manages all geohash cells under its prefix using standard DNS zone management. This mirrors the hierarchical structure of the DNS itself.

**Normative rules**

- `muri` is REQUIRED in the TXT record for geospatial bindings. The geospatial binding's purpose is to locate an HTTP discovery endpoint; direct DDS connection via `did` + SRV alone is NOT sufficient because the client's network path to the DDS domain is not implied by geographic proximity.
- `ver` is REQUIRED and MUST match the local DNS-SD binding's version key.
- The geohash MUST be a valid base32 geohash [8] of 3–7 characters. Clients MUST reject TXT records found under geohash subdomains shorter than 3 characters or longer than 7 characters.
- The fallback-to-shorter-prefix algorithm MUST NOT retry below precision 3 to avoid excessive DNS queries.
- The `muri` endpoint MUST return `application/json` containing either a single service manifest (§8.2.3) or a JSON array of service manifests. An empty array indicates no services in the requested cell.
- DNS operators SHOULD populate records at precision 5 for general use. Finer precision (6–7) MAY be added for dense urban areas with multiple providers per neighborhood.
- Clients MUST validate the `coverage` field in returned manifests against their actual position. A geohash cell is an approximation; the manifest's `bbox` or `coverage` elements are authoritative for determining whether a service actually covers the client's location.
- DNS TTLs SHOULD be set appropriately for the deployment's dynamism. Static deployments (fixed VPS infrastructure) MAY use TTLs of 3600 seconds or more. Dynamic deployments (pop-up events, temporary coverage) SHOULD use shorter TTLs (60–300 seconds).

**Relationship to local DNS-SD**

The geospatial and local DNS-SD bindings serve different deployment scales and MAY coexist:

| Binding | Network scope | Client prerequisite | Primary output |
|---|---|---|---|
| Local DNS-SD (mDNS) | Same LAN | WiFi connection | DDS domain_id + peer locator |
| Local DNS-SD (wide-area) | Known authority | Domain name (from QR, app config) | DDS domain_id + peer locator |
| Geospatial DNS-SD | Internet | GPS fix | HTTP discovery URL → service manifests |

A client arriving at a venue MAY try local mDNS first (fastest, no Internet dependency), fall back to geospatial DNS if mDNS yields no results (works over cellular, finds services across networks), and finally fall back to the HTTPS well-known path if a venue domain is available.

##### **Other Bootstrap Mechanisms (Informative)**

- **DHCP:** vendor-specific option carrying a URL to the bootstrap manifest.
- **QR / NFC / BLE beacons:** encode a `spatialdds://` URI or direct URL to the bootstrap manifest.
- **Mobile / MEC:** edge discovery APIs provide a URL to the bootstrap manifest.

##### **Complete Bootstrap Chain (Informative)**

**Path A — Local bootstrap (same LAN)**

```
Access Network           Bootstrap              DDS Domain            On-Bus Discovery
     │                      │                       │                       │
     │  WiFi/5G/BLE/QR      │                       │                       │
     ├─────────────────────► │                       │                       │
     │                       │  DNS-SD (mDNS) /      │                       │
     │                       │  .well-known / QR      │                       │
     │                       ├─────────────────────► │                       │
     │                       │  Bootstrap Manifest   │                       │
     │                       │  (domain_id, peers,   │                       │
     │                       │   partitions)         │                       │
     │                       │ ◄─────────────────────┤                       │
     │                       │                       │  Join DDS domain      │
     │                       │                       ├─────────────────────► │
     │                       │                       │  Subscribe to         │
     │                       │                       │  .../announce/v1      │
     │                       │                       │  Receive Announce     │
     │                       │                       │  Issue CoverageQuery  │
     │                       │                       │  Select streams       │
     │                       │                       │  Begin operation      │
```

**Path B — Internet bootstrap (cross-network, geospatial)**

```
GPS Fix               Geo DNS-SD            HTTP Discovery         DDS Domain
  │                      │                       │                       │
  │  Compute geohash     │                       │                       │
  ├─────────────────────►│                       │                       │
  │                      │  TXT query:           │                       │
  │                      │  _spatialdds._udp     │                       │
  │                      │  .<geohash>.geo.<auth> │                       │
  │                      ├──────────────────────►│                       │
  │                      │  TXT: muri=https://…  │                       │
  │                      │◄──────────────────────┤                       │
  │                      │                       │                       │
  │  HTTPS GET muri      │                       │                       │
  ├──────────────────────────────────────────────►│                       │
  │                      │                       │  Service manifest(s)  │
  │                      │                       │  (domain_id, peers,   │
  │                      │                       │   topics, coverage)   │
  │◄──────────────────────────────────────────────┤                       │
  │                      │                       │                       │
  │  Select service, connect via TCP/TLS         │                       │
  ├──────────────────────────────────────────────────────────────────────►│
  │                      │                       │  Begin operation      │
```


#### Key messages (abridged IDL)
*(Abridged IDL — see Appendix B for full definitions.)*
```idl
// ABRIDGED — see Appendix B for normative definitions
// Message shapes shown for orientation only
@extensibility(APPENDABLE) struct ProfileSupport { string name; uint32 major; uint32 min_minor; uint32 max_minor; }
@extensibility(APPENDABLE) struct Capabilities   { sequence<ProfileSupport,64> supported_profiles; sequence<string,32> preferred_profiles; sequence<string,64> features; }
@extensibility(APPENDABLE) struct TopicMeta      { string name; string type; string version; string qos_profile; float32 target_rate_hz; uint32 max_chunk_bytes; }

@extensibility(APPENDABLE) struct Announce {
  // ... node identity, endpoints ...
  Capabilities caps;                  // profiles, preferences, features
  sequence<TopicMeta,128> topics;     // typed topics offered by this node
}

@extensibility(APPENDABLE) struct CoverageFilter {
  sequence<string,16> type_in;
  sequence<string,16> qos_profile_in;
  sequence<string,16> module_id_in;
}

@extensibility(APPENDABLE) struct CoverageQuery {
  // minimal illustrative fields
  boolean has_filter;
  CoverageFilter filter; // structured matching
  string reply_topic;    // topic to receive results
  string query_id;       // correlate request/response
}

@extensibility(APPENDABLE) struct ServiceSummary {
  string service_id;
  ServiceKind kind;
  string name;
  SpatialUri manifest_uri;      // resolve for full caps/topics/transforms
  sequence<CoverageElement,4> coverage;
  FrameRef coverage_frame_ref;
  Time stamp;
  uint32 ttl_sec;
}

@extensibility(APPENDABLE) struct CoverageResponse {
  string query_id;
  sequence<ServiceSummary,256> results;
  string next_page_token;
}
```

#### Minimal examples (JSON)
**Announce (capabilities + topics)**
```json
{
  "caps": {
    "supported_profiles": [
      { "name": "spatial.core",      "major": 1, "min_minor": 7, "max_minor": 7 },
      { "name": "spatial.discovery", "major": 1, "min_minor": 7, "max_minor": 7 }
    ],
    "preferred_profiles": ["spatial.discovery/1.7"],
    "features": ["blob.crc32"]
  },
  "topics": [
    { "name": "spatialdds/perception/cam_front/video_frame/v1", "type": "video_frame", "version": "v1", "qos_profile": "VIDEO_LIVE" },
    { "name": "spatialdds/perception/radar_1/radar_detection/v1",  "type": "radar_detection", "version": "v1", "qos_profile": "RADAR_RT"   },
    { "name": "spatialdds/perception/radar_1/radar_tensor/v1",     "type": "radar_tensor", "version": "v1", "qos_profile": "RADAR_RT"      }
  ]
}
```

**Query + Response**
```json
{
  "query_id": "q1",
  "has_filter": true,
  "filter": {
    "type_in": ["radar_detection", "radar_tensor"],
    "qos_profile_in": [],
    "module_id_in": ["spatial.discovery/1.7"]
  },
  "reply_topic": "spatialdds/discovery/response/q1",
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 30
}
```

Reply topics are consumer-chosen and exempt from the application-topic pattern.

```json
{ "query_id": "q1",
  "results": [
    { "service_id": "radar-1", "kind": "OTHER",
      "name": "Radar aggregation",
      "manifest_uri": "spatialdds://ops.example.org/plant1/service/radar-1",
      "coverage": [ { "has_bbox": true, "bbox": [-122.42, 37.78, -122.40, 37.80], "global": false } ],
      "coverage_frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
      "stamp": { "sec": 1714070400, "nanosec": 0 }, "ttl_sec": 300 } ],
  "next_page_token": "" }
```

#### Norms & filters
* Announces **MUST** include `caps.supported_profiles`; peers choose the highest compatible minor within a shared major.
* Each advertised topic **MUST** declare `name`, `type`, `version`, and `qos_profile` per Topic Identity (§3.3.1); optional throughput hints (`target_rate_hz`, `max_chunk_bytes`) are additive.
* Each advertised topic's `type` SHALL be a value registered in the Typed Topics Registry (§3.3.2) or a documented deployment-specific extension per §3.3.1; `version` SHALL follow Topic Version Stability (§3.3.1); and `qos_profile` SHALL be a profile named in §3.3.3 or a documented deployment-specific extension.
* `caps.preferred_profiles` is an optional tie-breaker **within the same major**.
* `caps.features` carries namespaced feature flags; unknown flags **MUST** be ignored.
* `CoverageQuery.filter` provides structured matching for `type`, `qos_profile`, and `module_id`.
* Empty sequences in `CoverageFilter` mean “match all” for that field.
* When multiple filter fields are populated, they are ANDed; a result MUST match at least one value in every non-empty sequence.
* Version range matching stays in profile negotiation (`supported_profiles` with `min_minor`/`max_minor`), not in coverage queries.
* Responders page large result sets via `next_page_token`; every response **MUST** echo the caller’s `query_id`.

#### **Pagination Contract (Normative)**

1. **Opacity.** Page tokens are opaque strings produced by the responder. Consumers MUST NOT parse, construct, or modify them.
2. **Consistency.** Results are best-effort. Pages may include duplicates or miss nodes that arrived/departed between pages. Consumers SHOULD deduplicate by `service_id`.
3. **Expiry.** Responders SHOULD honor page tokens for at least `ttl_sec` seconds from the originating query’s `stamp`. After expiry, responders MAY return an empty result set rather than an error.
4. **Termination.** An empty string in `next_page_token` means no further pages remain.
5. **Page size.** Responders choose page size. Consumers MUST accept any non-zero page size.

#### **Announce Lifecycle (Normative)**

- **Departure:** A node leaving the bus gracefully MUST dispose its `Announce` instance (DDS instance state `NOT_ALIVE_DISPOSED`) so that durable readers and late joiners observe the removal, and SHOULD also publish `Depart` (which bridges to non-DDS transports). Consumers MUST treat a disposed `Announce` instance or a received `Depart` as removal of that `service_id` from their local directory. TTL-based expiry remains the backstop for ungraceful departure.
- **Staleness:** Consumers SHOULD discard Announce samples where `now - stamp > 2 * ttl_sec`.
- **Re-announce cadence:** Producers SHOULD re-announce at intervals no greater than `ttl_sec / 2` to prevent premature expiry.
- **Rate limiting:** Producers SHOULD NOT re-announce more frequently than once per second unless capabilities, coverage, or topics have changed. Consumers MAY rate-limit processing per `service_id`.

#### **Well-Known Discovery Topics (Normative)**

| Message Type | Topic Name |
|---|---|
| `Announce` | `spatialdds/discovery/announce/v1` |
| `Depart` | `spatialdds/discovery/depart/v1` |
| `CoverageQuery` | `spatialdds/discovery/query/v1` |
| `CoverageHint` | `spatialdds/discovery/coverage_hint/v1` |
| `ContentAnnounce` | `spatialdds/discovery/content/v1` |

`CoverageResponse` uses the `reply_topic` specified in the originating `CoverageQuery`.

**QoS defaults for discovery topics**

| Topic | Reliability | Durability | History |
|---|---|---|---|
| `announce` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `depart` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `query` | RELIABLE | VOLATILE | KEEP_ALL |
| `coverage_hint` | BEST_EFFORT | VOLATILE | KEEP_LAST(1) per key |
| `content` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |

**CoverageResponse reply topic QoS (Normative)**  
The writer for `reply_topic` SHOULD use **RELIABLE**, **VOLATILE**, **KEEP_ALL**.  
The querier SHOULD create a matching reader before publishing the `CoverageQuery`.

#### **Discovery trust (Normative)**
ANNOUNCE messages provide discovery convenience and are not, by themselves, authoritative. Clients **MUST** apply the Security Model requirements in §2.7 before trusting advertised URIs, topics, or services.

#### Asset references

Discovery announcements and manifests share a single `AssetRef` structure composed of URI, media type, integrity hash, and optional `MetaKV` metadata bags. AssetRef and MetaKV are normative types for asset referencing in the Discovery profile.

#### **`auth_hint` (Normative)**
`auth_hint` provides a machine-readable hint describing how clients can authenticate and authorize access to the service or resolve associated resources. `auth_hint` does **not** replace deployment policy; clients may enforce stricter requirements than indicated.

- If `auth_hint` is **empty** or omitted, it means “no authentication hint provided.” Clients **MUST** fall back to deployment policy (e.g., DDS Security configuration, trusted network assumptions, or authenticated manifest retrieval).
- If `auth_hint` is **present**, it **MUST** be interpreted as one or more **auth URIs** encoded as a comma-separated list.

**Grammar (normative):**  
`auth_hint := auth-uri ("," auth-uri)*`  
`auth-uri := scheme ":" scheme-specific`

**Required schemes (minimum set):**
- `ddssec:` indicates that the DDS transport uses **OMG DDS Security** (governance/permissions) for authentication and access control.
  - Example: `ddssec:profile=default`
  - Example: `ddssec:governance=spatialdds://auth.example/…/governance.xml;permissions=spatialdds://auth.example/…/permissions.xml`
- `oauth2:` indicates OAuth2-based access for HTTP(S) resolution or service APIs.
  - Example: `oauth2:issuer=https://auth.example.com;aud=spatialdds;scope=vps.localize`
- `mtls:` indicates mutual TLS for HTTP(S) resolution endpoints.
  - Example: `mtls:https://resolver.example.com`

**Client behavior (normative):**
- A client **MUST** treat `auth_hint` as advisory configuration and **MUST** still validate the authenticity of the service/authority via a trusted mechanism (DDS Security identity or authenticated artifact retrieval).
- If the client does not support any scheme listed in `auth_hint`, it **MUST** fail gracefully and report “unsupported authentication scheme.”

**Examples (informative):**
- `auth_hint="ddssec:profile=city-austin"`
- `auth_hint="ddssec:governance=spatialdds://city.example/…/gov.xml,oauth2:issuer=https://auth.city.example;aud=spatialdds;scope=catalog.read"`

#### What fields mean (quick reference)
| Field | Use |
|------|-----|
| `caps.supported_profiles` | Version ranges per profile. Peers select the **highest compatible minor** within a shared major. |
| `caps.preferred_profiles` | Optional tie-breaker hint (only within a major). |
| `caps.features` | Optional feature flags (namespaced strings). Unknown flags can be ignored. |
| `topics[].type` / `version` / `qos_profile` | Topic Identity keys used to filter and match streams; see the allowed sets above. |
| `reply_topic`, `query_id` | Allows asynchronous, paged responses and correlation. |

#### Practical notes
* Announce messages stay small and periodic; re-announce whenever capabilities, coverage, or topics change.
* Queries are stateless filters. Responders may page through results; clients track `next_page_token` until empty.
* Topic names follow `spatialdds/<domain>/<stream>/<type>/<version>` per §3.3.1; filter by `type` and `qos_profile` instead of parsing payloads.
* Negotiation is automatic once peers see each other’s `supported_profiles`; emit diagnostics like `NO_COMMON_MAJOR(name)` when selection fails.

#### Summary
Discovery keeps the wire simple: nodes publish what they have, clients filter for what they need, and the system converges on compatible versions. Use typed topic metadata to choose streams, rely on capabilities to negotiate versions without additional application-level handshakes, and treat discovery traffic as the lightweight directory for every SpatialDDS deployment.

#### **3.3.1 Topic Naming (Normative)**

SpatialDDS topics are identified by a structured **name**, a **type**, a **version**, and a declared **Quality-of-Service (QoS)** profile. Together these define both *what* a stream carries and *how* it behaves on the wire.

Each topic follows this pattern:
```
spatialdds/<domain>/<stream>/<type>/<version>
```
| Segment | Meaning | Example |
|----------|----------|----------|
| `<domain>` | Logical app domain | `perception` |
| `<stream>` | Sensor or stream ID | `cam_front` |
| `<type>` | Registered data type | `video_frame` |
| `<version>` | Schema or message version | `v1` |

This pattern applies to application data topics. Well-known discovery topics (§3.3 tables) and topic templates defined by individual profiles (e.g., `spatialdds/<scene>/plan/<agent_id>/trajectory/v1`) are normative as specified where they are defined and MAY use additional path segments. The `<type>` segment of an application topic name is a human-readable hint; the authoritative type of a topic is the `type` field in its `TopicMeta` / manifest entry, not the topic name.

###### Example
```json
{
  "name": "spatialdds/perception/radar_1/radar_detection/v1",
  "type": "radar_detection",
  "version": "v1",
  "qos_profile": "RADAR_RT"
}
```

##### Topic Version Stability (Normative)

The version segment in topic names (e.g., `/v1`) corresponds to the **profile MAJOR version**, not the MINOR version. Topic names change only when a profile increments its MAJOR version number. Concretely:

- `spatial.sensing.vision/1.7` → `spatial.sensing.vision/1.8`: topic names remain `/v1` (same MAJOR).
- `spatial.sensing.vision/1.7` → `spatial.sensing.vision/2.0`: topic names change to `/v2` (MAJOR incremented).

Profile MINOR bumps (`@extensibility(APPENDABLE)` additions) MUST NOT change topic names. This guarantees that consumers subscribing to `/v1` topics continue to receive messages after MINOR-version updates without resubscribing.

#### **3.3.2 Typed Topics Registry**

> **Registry completeness rule.** Every struct in Appendices A–D intended for publication as a topic SHALL have a registry row. Adding a topic-bearing struct without a registry row is a spec defect. Provisional registered types (`rf_beam`, `radio_scan`) ship under `idl/<ver>/provisional/`.

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Large, reliable transfers — `core::TileMeta`; QoS `GEOM_TILE` |
| `video_frame` | Encoded video/image | Real-time camera streams — `sensing::vision::VisionFrame`; QoS `VIDEO_LIVE` |
| `radar_detection` | Per-frame detection set | Structured radar detections — `sensing::rad::RadDetectionSet`; QoS `RADAR_RT` |
| `radar_tensor` | N-D float/int tensor | Raw/processed radar data cube — `sensing::rad::RadTensorFrame`; QoS `RADAR_RT` |
| `rf_beam` | Beam sweep power vectors | Phased-array beam power measurements — `sensing::rf_beam::RfBeamFrame`; QoS `RF_BEAM_RT` (provisional) |
| `radio_scan` | Per-scan radio observations | WiFi/BLE/UWB/cellular fingerprint observations — `sensing::radio::RadioScan`; QoS `RADIO_SCAN_RT` (provisional) |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation — `sensing::vision::VisionFrame` (alias of `video_frame`); QoS `SEG_MASK_RT` |
| `desc_array` | Feature descriptor sets | Vector or embedding batches — `slam_frontend::KeyframeFeatures`; QoS `DESC_BATCH` |
| `map_meta` | Map lifecycle descriptor | Latched; TRANSIENT_LOCAL — `mapping::MapMeta`; QoS `MAP_META` |
| `map_alignment` | Inter-map transform | Latched; TRANSIENT_LOCAL — `mapping::MapAlignment`; QoS `MAP_META` |
| `map_event` | Map lifecycle event | Lightweight notifications — `mapping::MapEvent`; QoS `MAP_META` |
| `spatial_zone` | Named zone definition | Latched; TRANSIENT_LOCAL — `events::SpatialZone`; QoS `ZONE_META` |
| `spatial_event` | Spatially-scoped event | Typed alerts and anomalies — `events::SpatialEvent`; QoS `EVENT_RT` |
| `zone_state` | Zone occupancy snapshot | Periodic dashboard feed — `events::ZoneState`; QoS `ZONE_META` |
| `navsat_status` | GNSS receiver diagnostics | Companion to GeoPose — `core::NavSatStatus` |
| `planned_trajectory` | Future agent trajectory with waypoints | Intent sharing, cooperative planning — `core::PlannedTrajectory`; QoS `EVENT_RT` |
| `entity_binding` | Cross-topic entity correlation | Scene graph construction, digital twins — `core::EntityBinding` |
| `geopose` | Global pose sample | GNSS/VPS localization outputs — `core::GeoPose`; QoS `POSE_RT` |
| `vps_query` | VPS localization request | Query image/features + hints — `argeo::VpsRequest`; QoS `VPS_REQ` |
| `vps_response` | VPS localization response | `argeo::VpsResponse`; QoS `VPS_RESP` |
| `framed_pose` | Located metric pose | `core::FramedPose`; QoS `POSE_RT` |
| `detection3d` | 3D detection set | `semantics::Detection3DSet`; QoS `DET_RT` |
| `detection2d` | 2D (image-space) detection set | `semantics::Detection2DSet`; QoS `DET_RT` |
| `fused_track` | Cross-source fused track set | `semantics::FusedTrackSet`; QoS `DET_RT` |
| `lidar_frame` | Per-frame lidar cloud index | `sensing::lidar::LidarFrame`; QoS `LIDAR_RT` |
| `lidar_meta` | Lidar stream metadata | `sensing::lidar::LidarMeta`; QoS `SENSOR_META` (latched) |
| `radar_tensor_meta` | Radar tensor stream metadata | `sensing::rad::RadTensorMeta`; QoS `SENSOR_META` (latched) |
| `video_meta` | Camera/vision stream metadata | `sensing::vision::VisionMeta`; QoS `SENSOR_META` (latched) |
| `rf_beam_meta` | RF beam stream metadata (provisional) | `sensing::rf_beam::RfBeamMeta`; QoS `SENSOR_META` (latched) |
| `imu_sample` | Raw IMU sample | `vio::ImuSample`; QoS `IMU_RT` |
| `anchor_delta` | Anchor registry delta | `anchors::AnchorDelta`; QoS `ANCHOR_DELTA` |
| `rad_sensor_meta` | Radar (detection) stream metadata | `sensing::rad::RadSensorMeta`; QoS `SENSOR_META` (latched) |
| `radio_sensor_meta` | Radio stream metadata (provisional) | `sensing::radio::RadioSensorMeta`; QoS `SENSOR_META` (latched) |

These registered types ensure consistent topic semantics without altering wire framing. New types can be registered additively through this table or extensions.

Implementations defining custom `type` and `qos_profile` values SHOULD follow the naming pattern (`myorg.depth_frame`, `DEPTH_LIVE`) and document their DDS QoS mapping.

##### **Informative Example Registrations**

*Types defined only in Appendix E examples (informative). These registrations are **not** part of the conformance surface — the normative registry gate does not require or check them; it only confirms they resolve.*

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `agent_status` | Agent availability advertisement | `agent::AgentStatus` (informative example, Appendix E) |
| `task_offer` | Agent bid on a task | `agent::TaskOffer` (informative example, Appendix E) |
| `task_assignment` | Coordinator task binding | `agent::TaskAssignment` (informative example, Appendix E) |

#### **3.3.3 QoS Profiles**

QoS profiles define delivery guarantees and timing expectations for each topic type.

| Profile | Reliability | Ordering | Durability | History | Deadline | Use Case |
|----------|--------------|----------|------------|---------|----------|-----------|
| `GEOM_TILE` | Reliable | Ordered | Transient-local | KeepLast(1) | — | 3D geometry, large tile data |
| `VIDEO_LIVE` | Best-effort | Ordered | Volatile | KeepLast(1) | 33 ms | Live video feeds |
| `VIDEO_ARCHIVE` | Reliable | Ordered | Volatile | KeepAll | — | Replay or stored media |
| `RADAR_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 100 ms | Real-time radar data (detections or tensors) |
| `RF_BEAM_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 20 ms | Real-time beam sweep data |
| `RADIO_SCAN_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | — | Radio fingerprint scans (WiFi/BLE/UWB) |
| `SEG_MASK_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 33 ms | Live segmentation masks |
| `DESC_BATCH` | Reliable | Ordered | Volatile | KeepAll | — | Descriptor or feature batches |
| `MAP_META` | Reliable | Ordered | Transient-local | KeepLast(1) | — | Map descriptors, alignments, events |
| `ZONE_META` | Reliable | Ordered | Transient-local | KeepLast(1) | — | Zone definitions, zone state |
| `EVENT_RT` | Reliable | Ordered | Volatile | KeepLast(64) | — | Spatial events and alerts |
| `POSE_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 33 ms | Live pose streams |
| `VPS_REQ` | Reliable | Ordered | Volatile | KeepAll | — | VPS localization requests |
| `VPS_RESP` | Reliable | Ordered | Volatile | KeepAll | — | VPS localization responses |
| `DET_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 100 ms | Detection sets (2D/3D) |
| `LIDAR_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 100 ms | Lidar frames |
| `IMU_RT` | Best-effort | Ordered | Volatile | KeepLast(1) | 10 ms | IMU samples |
| `SENSOR_META` | Reliable | Ordered | Transient-local | KeepLast(1) | — | Sensor/stream metadata |
| `ANCHOR_DELTA` | Reliable | Ordered | Volatile | KeepAll | — | Anchor delta streams; snapshots via manifests |

###### Notes

* Each topic advertises its `qos_profile` during discovery.
* Profiles capture trade-offs between latency, reliability, and throughput.
* `RADAR_RT` is **Best-effort**: detection sets tolerate loss, and integrity of individual samples is protected by per-type checksums where present. There is no partial-reliability kind in DDS.
* Mixing unrelated data (e.g., radar + video) in a single QoS lane is discouraged.

> **Normative QoS surface.** For each profile, Reliability, Durability, History, and Deadline (as specified in the table columns) are normative: writers and readers SHALL set exactly these policies. Where Deadline is "—", the Deadline QoS SHALL be left at its default (infinite). Other DDS policies MAY be tuned per deployment.
>
> **Deadline is request/offered.** A reader requesting a Deadline does not match a writer that offers none, and the failure is silent — no error is raised and no samples flow. This is why Deadline values are normative rather than typical. Note that DDS Deadline is a per-instance inter-sample-period contract, not a latency bound; it is therefore specified only for periodic stream profiles.

##### Discovery and Manifest Integration

Every `Announce.topics[]` entry and manifest topic reference SHALL include:
- `type` — one of the registered type values
- `version` — the schema or message version
- `qos_profile` — one of the standard or extended QoS names

For each advertised topic, `type`, `version`, and `qos_profile` MUST be present and MUST either match a registered value in this specification or a documented deployment-specific extension.

Consumers use these three keys to match and filter streams without inspecting payload bytes. Brokers and routers SHOULD isolate lanes by `(topic, stream_id, qos_profile)` to avoid head-of-line blocking.

#### **3.3.4 Coverage Model (Normative)**

- `coverage_frame_ref` is the canonical frame for an announcement. `CoverageElement.frame_ref` MAY override it, but SHOULD be used sparingly (e.g., mixed local frames). If absent, consumers MUST use `coverage_frame_ref`.
- When `coverage_eval_time` is present, consumers SHALL evaluate any referenced transforms at that instant before interpreting `coverage_frame_ref`.
- When `CoverageElement.has_coverage_window` is true, the coverage geometry is valid only between `coverage_window_start` and `coverage_window_end`. Consumers MUST NOT assume coverage outside this window. Producers advertising moving coverage (e.g., patrol routes, fleet trajectories) SHOULD publish updated `Announce` messages as coverage windows expire.
- When `has_coverage_window` is false, the coverage is persistent (time-invariant) and remains valid until the `Announce` is superseded or the participant leaves the domain.
- `coverage_eval_time` and `coverage_window` serve different purposes: `coverage_eval_time` specifies *when to evaluate time-varying transforms*; `coverage_window` specifies *when the coverage itself is valid*. Both MAY be present simultaneously.
- `global == true` means worldwide coverage regardless of regional hints. Producers MAY omit `bbox`, `geohash`, or `elements` in that case.
- When `global == false`, producers MAY supply any combination of regional hints; consumers SHOULD treat the union of all regions as the effective coverage.
- Manifests MAY provide any combination of `bbox`, `geohash`, and `elements`. Discovery coverage MAY omit `geohash` and rely solely on `bbox` and `aabb`. Consumers SHALL treat all hints consistently according to the Coverage Model.
- When `has_bbox == true`, `bbox` MUST contain finite coordinates; consumers SHALL reject non-finite values. When `has_bbox == false`, consumers MUST ignore `bbox` entirely. Same rules apply to `has_aabb` and `aabb`.
- **Circle.** `circle_center` follows the same frame rules as `bbox` (geographic: lon, lat[, alt]; local: meters in `coverage_frame_ref`); `circle_radius_m` is always meters. For intersects evaluation a circle MAY be approximated by its bounding box; producers SHOULD prefer the circle form over a hand-computed bounding box so consumers can recover the exact footprint.
- **Derived coverage.** A service whose coverage is a function of its inputs (e.g., a fusion service) SHOULD list the contributing services in `coverage_source_ids`. A non-empty list marks the declared coverage elements as an approximation of the union of the sources' coverage; consumers MAY resolve the sources for exact extents. An empty list means coverage is self-asserted.
- Earth-fixed frames (`fqn` rooted at `earth-fixed`) encode WGS84 longitude/latitude/height. Local frames MUST reference anchors or manifests that describe the transform back to an earth-fixed root (Appendix G).
- Discovery announces and manifests share the same coverage semantics and flags. `CoverageQuery` responders SHALL apply these rules consistently when filtering or paginating results.
- See §2 Conventions for global normative rules.

### Earth-fixed roots and local frames

For global interoperability, SpatialDDS assumes that earth-fixed frames
(e.g., WGS84 longitude/latitude/height) form the root of the coverage
hierarchy. Local frames (for devices, vehicles, buildings, or ships) may
appear in coverage elements, but if the coverage is intended to be
globally meaningful, these local frames must be relatable to an
earth-fixed root through declared transforms or manifests.

Implementations are not required to resolve every local frame at runtime,
but when they do, the resulting coverage must be interpretable in an
earth-fixed reference frame.

#### Local-Frame Datasets Without GPS (Informative)
Some datasets and deployments operate entirely in a local metric coordinate frame without a known WGS84 origin. In this case:

1. The `coverage_frame_ref` SHOULD reference a local frame (e.g., `fqn = "map/local"`), not `earth-fixed`.
2. `GeoPose` fields (lat_deg, lon_deg, alt_m) MUST NOT be populated with fabricated values. Use local `FrameTransform` instead.
3. The Anchors profile can bridge local and earth-fixed frames when a GPS fix or survey becomes available.
4. `coverage.global` MUST be `false` for local-frame-only deployments.

This is the expected path for indoor robotics, warehouse automation, and datasets recorded without RTK-GPS.

#### Coverage Evaluation Pseudocode (Informative)
```
if coverage.global:
    regions = WORLD
else:
    regions = union(bbox, geohash, elements[*].aabb)
frame = coverage_frame_ref unless element.frame_ref present
evaluate transforms at coverage_eval_time if present
```

##### Implementation Guidance (Non-Normative)

* No change to on-wire framing — this metadata lives at the discovery layer.
* Named QoS profiles simplify cross-vendor interoperability and diagnostics.
* For custom types, follow the same naming pattern and document new QoS presets.
* All examples and tables herein are **additive**.

##### Discovery recipe (tying the examples together)

1. **Announce** — the producer sends `Announce` (see JSON example above) to advertise `caps` and `topics`.
2. **CoverageQuery** — the consumer issues a `CoverageQuery` (see query JSON) to filter by profile, topic type, or QoS.
3. **CoverageResponse** — the Discovery producer replies with `CoverageResponse` (see response JSON), returning results plus an optional `next_page_token` for pagination.

### **3.4 Anchors**

The Anchors profile provides a structured way to share and update collections of durable, world-locked anchors. While Core includes individual GeoAnchor messages, this profile introduces constructs such as AnchorSet for publishing bundles (e.g., a venue’s anchor pack) and AnchorDelta for lightweight updates. This makes it easy for clients to fetch a set of anchors on startup, stay synchronized through incremental changes, and request full snapshots when needed. Anchors complement VPS results by providing the persistent landmarks that make AR content and multi-device alignment stable across sessions and users.

### **3.5 Profiles Summary**

The complete SpatialDDS IDL bundle is organized into the following profiles:

* **Core Profile**  
  Fundamental building blocks: pose graphs, geometry tiles, anchors, transforms, and blob transport.  
* **Discovery Profile**
   Lightweight announce messages plus active query/response bindings for services, coverage areas, anchors, and spatial content or experiences.
* **Anchors Profile**  
  Durable anchors and the Anchor Registry, enabling persistent world-locked reference points.

Together, Core, Discovery, and Anchors form the foundation of SpatialDDS, providing the minimal set required for interoperability.

* **Extensions**
  * **Sensing Module Family**: `sensing.common` defines shared frame metadata, calibration, QoS hints, and codec descriptors. Radar, lidar, and vision profiles inherit those types and layer on their minimal deltas—`RadSensorMeta`/`RadDetectionSet`/`RadTensorMeta`/`RadTensorFrame` for radar, `PointCloud`/`ScanBlock`/`return_type` for lidar, and `ImageFrame`/`SegMask`/`FeatureArray` for vision. The provisional `rf_beam` extension adds `RfBeamMeta`/`RfBeamFrame`/`RfBeamArraySet` for phased-array beam power measurements, and the provisional `radio` extension adds `RadioSensorMeta`/`RadioScan` for WiFi/BLE/UWB fingerprint transport. Deployments MAY import the specialized profiles independently but SHOULD declare the `spatial.sensing.common/1.x` dependency when they do.
  * **VIO Profile**: Raw and fused IMU and magnetometer samples for visual-inertial pipelines.
  * **SLAM Frontend Profile**: Features, descriptors, and keyframes for SLAM and SfM pipelines.
  * **Semantics Profile**: 2D and 3D detections for AR occlusion, robotics perception, and analytics.
  * **AR+Geo Profile**: GeoPose, frame transforms, and geo-anchoring structures for global alignment and persistent AR content.
  * **Mapping Profile**: Map lifecycle descriptors (`MapMeta`), extended multi-source edge types, inter-map alignment transforms (`MapAlignment`), and lifecycle events for multi-agent map exchange.
  * **Spatial Events Profile**: Typed zone definitions (`SpatialZone`), spatially-scoped events (`SpatialEvent`), and periodic zone state summaries (`ZoneState`) for smart infrastructure and safety monitoring.
* **Provisional Extensions (Optional)**
  * **Neural Profile**: Metadata for neural fields (e.g., NeRFs, Gaussian splats) and optional view-synthesis requests.
  * **Agent Profile**: Generic task and status messages for AI agents and planners.

Together, these profiles give SpatialDDS the flexibility to support robotics, AR/XR, digital twins, IoT, and AI world models—while ensuring that the wire format remains lightweight, codec-agnostic, and forward-compatible.

#### **Profile Matrix (SpatialDDS 1.7)**

| Profile | Version in 1.7 | Status | 1.7 Change |
|---|---|---|---|
| spatial.core | 1.7 | Stable | **Breaking:** `Time.sec` int64; compound `@key` on `Node`/`Edge`; `GeoPose` orientation fixed to local ENU (removed `frame_kind`/`frame_ref`, `GeoFrameKind`); `TileMeta` single `aabb` (removed `min_xyz`/`max_xyz`/`lod`); removed `BlobChunk.last`. **Findings batch 2 (draft rev):** Breaking — `BlobChunk.data` bound 262144→65535; Additive — `MetaKV.entries` typed rows + `common::KV` |
| spatial.discovery | 1.7 | Stable | **Breaking:** `CoverageResponse` returns `ServiceSummary` rows; `caps.features` now `sequence<string>` (removed `FeatureFlag`); removed `ProfileSupport.preferred`, `CoverageElement.type`, `CoverageQuery.expr`. **Findings batch 2 (draft rev):** Additive — `ServiceKind` +SENSING/INFRASTRUCTURE/FUSION; `CoverageElement` circle; `Announce.coverage_source_ids` |
| spatial.sensing.common | 1.7 | Stable | **Findings batch 2 (draft rev):** Additive — `Codec` +PNG |
| spatial.manifest | 1.7 | Stable | Single-identifier profile string; schema bumped to `/1.7` |
| spatial.anchors | 1.7 | Stable | No IDL change (version unified to 1.7) |
| spatial.argeo | 1.7 | Stable | **Findings batch 3 (draft rev):** Additive — VPS request/response pair (`VpsRequest`/`VpsResponse`/`QualityRequirements`/`VpsStatus`) |
| spatial.sensing.rad | 1.7 | Stable | No IDL change (version unified to 1.7) |
| spatial.sensing.lidar | 1.7 | Stable | No IDL change (version unified to 1.7) |
| spatial.sensing.vision | 1.7 | Stable | No IDL change (version unified to 1.7) |
| spatial.slam_frontend | 1.7 | Stable | **Findings batch 2 (draft rev):** Breaking — `KeyframeFeatures.descriptors` bound 1048576→65535 (larger sets via blob transfer) |
| spatial.vio | 1.7 | Stable | **Findings batch 2 (draft rev):** Additive — `ImuSample` accel/gyro covariance (`CovMatrix`) |
| spatial.semantics | 1.7 | Stable | **Findings batch 2 (draft rev):** Additive — `Detection3D.velocity`. **Batch 3:** Additive — `FusedTrack` / `FusedTrackSet` |
| spatial.mapping | 1.7 | Stable | **Breaking:** compound `@key` on `mapping::Edge` (`map_id`, `edge_id`), aligning with `core::Node`/`Edge` |
| spatial.events | 1.7 | Stable | **Findings batch 2 (draft rev):** Additive — `EventType.PREDICTED_CONFLICT`; `SpatialEvent.participant_ids` |
| spatial.sensing.rf_beam | 1.7 | Provisional (Appendix E) | No IDL change (version unified to 1.7) |
| spatial.sensing.radio | 1.7 | Provisional (Appendix E) | No IDL change (version unified to 1.7) |
| spatial.neural | 1.7 | Informative example (Appendix E) | No IDL change (version unified to 1.7) |
| spatial.agent | 1.7 | Informative example (Appendix E) | No IDL change (version unified to 1.7) |

Through the 1.x pre-adoption series, all modules version together with the specification. Every `MODULE_ID` and `schema_version` in 1.7 is `spatial.<profile>/1.7`. Topic names continue to use the `/v1` segment per §3.3.1 Topic Version Stability — minor profile bumps do not change topic names.

> `spatial.manifest/1.7` defines the JSON schema for SpatialDDS manifests, not an IDL module. It does not have a corresponding `MODULE_ID` declaration in the IDL. Provisional profile definitions and examples are specified in Appendix E.

The Sensing module family keeps sensor data interoperable: `sensing.common` unifies pose stamps, calibration blobs, ROI negotiation, and quality reporting. Radar, lidar, and vision modules extend that base without redefining shared scaffolding, ensuring multi-sensor deployments can negotiate payload shapes and interpret frame metadata consistently.
