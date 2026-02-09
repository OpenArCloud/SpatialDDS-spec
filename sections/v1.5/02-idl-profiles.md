// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.5 (© Open AR Cloud Initiative)

## **3\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

_See §2 Conventions for global normative rules._

### **3.1 IDL Profile Versioning & Negotiation (Normative)**

SpatialDDS uses semantic versioning tokens of the form `name@MAJOR.MINOR`.

* **MAJOR** increments for breaking schema or wire changes.
* **MINOR** increments for additive, compatible changes.

Identifier conventions: Profile tokens use `name@MAJOR.MINOR` (e.g., `core@1.5`). Module identifiers use `spatial.<profile>/MAJOR.MINOR` (e.g., `spatial.core/1.5`). These are canonically related: `core@1.5 ⇔ spatial.core/1.5`.

Participants advertise supported ranges via `caps.supported_profiles` (discovery) and manifest capabilities blocks. Consumers select the **highest compatible minor** within any shared major. Backward-compatibility clauses from 1.3 are retired; implementations only negotiate within their common majors. SpatialDDS 1.5 uses a single canonical quaternion order `(x, y, z, w)` across manifests, discovery payloads, and IDL messages.

### **3.2 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. All quaternion fields follow the OGC GeoPose component order `(x, y, z, w)` so orientation data can flow between GeoPose-aware systems without reordering. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

**GNSS diagnostics (Normative):** `NavSatStatus` is a companion to `GeoPose` that carries GNSS receiver diagnostics (fix type, DOP, satellite count, ground velocity) on a parallel topic. It is published alongside GNSS-derived GeoPoses and MUST NOT be used to annotate non-GNSS localization outputs.

**NavSatStatus Topic (Normative):** NavSatStatus SHOULD be published on the topic `spatialdds/geo/<gnss_id>/navsat_status/v1`, where `<gnss_id>` matches the `@key gnss_id` in the struct and identifies the GNSS receiver. NavSatStatus SHOULD use the same QoS profile as the associated GeoPose stream. Producers publishing GNSS-derived GeoPoses SHOULD co-publish NavSatStatus at the same cadence. NavSatStatus is not a registered discovery type and does not require a `TopicMeta` entry in `Announce.topics[]`.

#### **Blob Reassembly (Normative)**

Blob payloads are transported as `BlobChunk` sequences. Consumers MUST be prepared for partial delivery and SHOULD apply a per-blob timeout window based on expected rate and `total_chunks`.

- **Timeout guidance:** Consumers SHOULD apply a per-blob timeout of at least `2 × (total_chunks / expected_rate)` seconds when an expected rate is known.
- **Failure handling:** If all chunks have not arrived within this window under **RELIABLE** QoS, the consumer SHOULD discard the partial blob and MAY re-request it via `SnapshotRequest`.
- **BEST_EFFORT behavior:** Under **BEST_EFFORT** QoS, consumers MUST NOT assume complete delivery and SHOULD treat blobs as opportunistic.
- **Memory pressure:** Consumers MAY discard partial blobs early under memory pressure, but MUST NOT treat them as valid payloads.

#### Frame Identifiers (Reference)

SpatialDDS uses structured frame references via the `FrameRef { uuid, fqn }` type.
See *Appendix G Frame Identifiers (Informative Reference)* for the complete definition and naming rules.

Each Transform expresses a pose that maps coordinates from the `from` frame into the `to` frame (parent → child).

### **3.3 Discovery**

Discovery is how SpatialDDS peers **find each other**, **advertise what they publish**, and **select compatible streams**. Think of it as a built-in directory that rides the same bus: nodes announce, others filter and subscribe.

#### How it works (at a glance)
1. **Announce** — each node periodically publishes an announcement with capabilities and topics.
2. **Query** — clients publish simple filters (by profile version, type, QoS) to narrow results.
3. **Select** — clients subscribe to chosen topics; negotiation picks the highest compatible minor per profile.

#### **3.3.0 Discovery Layers & Bootstrap (Normative)**

SpatialDDS distinguishes two discovery layers:

- **Layer 1 — Network Bootstrap:** how a device discovers that a SpatialDDS DDS domain exists and obtains connection parameters. This is transport and access-network dependent.
- **Layer 2 — On-Bus Discovery:** how a device, once connected to a DDS domain, discovers services, coverage, and streams. This is what the Discovery profile defines.

Layer 1 mechanisms deliver a **Bootstrap Manifest** that provides the parameters needed to transition to Layer 2.

##### **Bootstrap Manifest (Normative)**

A bootstrap manifest is a small JSON document resolved by Layer 1 mechanisms:

```json
{
  "spatialdds_bootstrap": "1.5",
  "domain_id": 42,
  "initial_peers": [
    "udpv4://192.168.1.100:7400",
    "udpv4://10.0.0.50:7400"
  ],
  "partitions": ["venue/museum-west"],
  "discovery_topic": "spatialdds/discovery/announce/v1",
  "manifest_uri": "spatialdds://museum.example.org/west/service/discovery",
  "auth": {
    "method": "none"
  }
}
```

**Field definitions**

| Field | Required | Description |
|---|---|---|
| `spatialdds_bootstrap` | REQUIRED | Bootstrap schema version (e.g., "1.5") |
| `domain_id` | REQUIRED | DDS domain ID to join |
| `initial_peers` | REQUIRED | One or more DDS peer locators for initial discovery |
| `partitions` | OPTIONAL | DDS partition(s) to join. Empty or absent means default partition. |
| `discovery_topic` | OPTIONAL | Override for the well-known announce topic. Defaults to `spatialdds/discovery/announce/v1`. |
| `manifest_uri` | OPTIONAL | A `spatialdds://` URI for the deployment's root manifest. |
| `auth` | OPTIONAL | Authentication hint. `method` is one of `"none"`, `"dds-security"`, `"token"`. |

**Normative rules**

- `domain_id` MUST be a valid DDS domain ID (0–232 per the RTPS specification; higher values may require non-standard configuration).
- `initial_peers` MUST contain at least one locator. Locator format follows the DDS implementation's peer descriptor syntax.
- Consumers SHOULD attempt all listed peers and use the first that responds.
- The bootstrap manifest is a discovery aid, not a security boundary. Deployments requiring authentication MUST use DDS Security or an equivalent transport-level mechanism.

##### **Well-Known HTTPS Path (Normative)**

Clients MAY fetch the bootstrap manifest from:

```
https://{authority}/.well-known/spatialdds
```

The response MUST be `application/json` using the bootstrap manifest schema. Servers SHOULD set `Cache-Control` headers appropriate to their deployment (e.g., `max-age=300`).

**Note:** The bootstrap path `/.well-known/spatialdds` and the resolver metadata path `/.well-known/spatialdds-resolver` serve distinct functions and MAY coexist on the same authority. The bootstrap path returns a Bootstrap Manifest (this section), while the resolver path returns resolver metadata for URI resolution (§7.5.2).

##### **DNS-SD Binding (Normative)**

DNS-SD is the recommended first binding for local bootstrap.

**Service type:** `_spatialdds._udp`

**TXT record keys**

| Key | Maps to | Example |
|---|---|---|
| `ver` | `spatialdds_bootstrap` | `1.5` |
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

##### **Other Bootstrap Mechanisms (Informative)**

- **DHCP:** vendor-specific option carrying a URL to the bootstrap manifest.
- **QR / NFC / BLE beacons:** encode a `spatialdds://` URI or direct URL to the bootstrap manifest.
- **Mobile / MEC:** edge discovery APIs provide a URL to the bootstrap manifest.

##### **Complete Bootstrap Chain (Informative)**

```
Access Network           Bootstrap              DDS Domain            On-Bus Discovery
     │                      │                       │                       │
     │  WiFi/5G/BLE/QR      │                       │                       │
     ├─────────────────────► │                       │                       │
     │                       │  DNS-SD / HTTPS /     │                       │
     │                       │  .well-known lookup   │                       │
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
     │                       │                       │  messages             │
     │                       │                       │  Issue CoverageQuery  │
     │                       │                       │  Select streams       │
     │                       │                       │  Begin operation      │
```


#### Key messages (abridged IDL)
*(Abridged IDL — see Appendix B for full definitions.)*
```idl
// Message shapes shown for orientation only
@extensibility(APPENDABLE) struct ProfileSupport { string name; uint32 major; uint32 min_minor; uint32 max_minor; boolean preferred; }
@extensibility(APPENDABLE) struct Capabilities   { sequence<ProfileSupport,64> supported_profiles; sequence<string,32> preferred_profiles; sequence<FeatureFlag,64> features; }
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
  CoverageFilter filter; // preferred in 1.5
  string expr;           // deprecated in 1.5; Appendix F.X grammar
  string reply_topic;    // topic to receive results
  string query_id;       // correlate request/response
}

The expression syntax is retained for legacy deployments and defined in Appendix F.X; `expr` is deprecated in 1.5 in favor of `filter`.

@extensibility(APPENDABLE) struct CoverageResponse {
  string query_id;
  sequence<Announce,256> results;
  string next_page_token;
}
```

#### Minimal examples (JSON)
**Announce (capabilities + topics)**
```json
{
  "caps": {
    "supported_profiles": [
      { "name": "core",           "major": 1, "min_minor": 0, "max_minor": 3 },
      { "name": "discovery",      "major": 1, "min_minor": 1, "max_minor": 2 }
    ],
    "preferred_profiles": ["discovery@1.2"],
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
    "module_id_in": ["spatial.discovery/1.4", "spatial.discovery/1.5"]
  },
  "expr": "",
  "reply_topic": "spatialdds/discovery/response/q1",
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 30
}
```
```json
{ "query_id": "q1", "results": [ { "caps": { "supported_profiles": [ { "name": "discovery", "major": 1, "min_minor": 1, "max_minor": 2 } ] }, "topics": [ { "name": "spatialdds/perception/radar_1/radar_detection/v1", "type": "radar_detection", "version": "v1", "qos_profile": "RADAR_RT" }, { "name": "spatialdds/perception/radar_1/radar_tensor/v1", "type": "radar_tensor", "version": "v1", "qos_profile": "RADAR_RT" } ] } ], "next_page_token": "" }
```

#### Norms & filters
* Announces **MUST** include `caps.supported_profiles`; peers choose the highest compatible minor within a shared major.
* Each advertised topic **MUST** declare `name`, `type`, `version`, and `qos_profile` per Topic Identity (§3.3.1); optional throughput hints (`target_rate_hz`, `max_chunk_bytes`) are additive.
* Discovery topics SHALL restrict `type` to {`geometry_tile`, `video_frame`, `radar_detection`, `radar_tensor`, `seg_mask`, `desc_array`, `rf_beam`}, `version` to `v1`, and `qos_profile` to {`GEOM_TILE`, `VIDEO_LIVE`, `RADAR_RT`, `SEG_MASK_RT`, `DESC_BATCH`, `RF_BEAM_RT`}.
* `caps.preferred_profiles` is an optional tie-breaker **within the same major**.
* `caps.features` carries namespaced feature flags; unknown flags **MUST** be ignored.
* `FeatureFlag` is a struct (not a raw string) to allow future appended fields (e.g., version or parameters) without breaking wire compatibility.
* `CoverageQuery.filter` provides structured matching for `type`, `qos_profile`, and `module_id`.
* Empty sequences in `CoverageFilter` mean “match all” for that field.
* When multiple filter fields are populated, they are ANDed; a result MUST match at least one value in every non-empty sequence.
* Version range matching stays in profile negotiation (`supported_profiles` with `min_minor`/`max_minor`), not in coverage queries.
* `CoverageQuery.expr` is deprecated in 1.5. If `has_filter` is true, responders MUST ignore `expr`.
* Responders page large result sets via `next_page_token`; every response **MUST** echo the caller’s `query_id`.

#### **Pagination Contract (Normative)**

1. **Opacity.** Page tokens are opaque strings produced by the responder. Consumers MUST NOT parse, construct, or modify them.
2. **Consistency.** Results are best-effort. Pages may include duplicates or miss nodes that arrived/departed between pages. Consumers SHOULD deduplicate by `service_id`.
3. **Expiry.** Responders SHOULD honor page tokens for at least `ttl_sec` seconds from the originating query’s `stamp`. After expiry, responders MAY return an empty result set rather than an error.
4. **Termination.** An empty string in `next_page_token` means no further pages remain.
5. **Page size.** Responders choose page size. Consumers MUST accept any non-zero page size.

#### **Announce Lifecycle (Normative)**

- **Departure:** A node that leaves the bus gracefully SHOULD publish a `Depart` message. Consumers MUST remove the corresponding `service_id` from their local directory upon receiving `Depart`. `Depart` does not replace TTL-based expiry.
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

###### Example
```json
{
  "name": "spatialdds/perception/radar_1/radar_detection/v1",
  "type": "radar_detection",
  "version": "v1",
  "qos_profile": "RADAR_RT"
}
```

#### **3.3.2 Typed Topics Registry**

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Large, reliable transfers |
| `video_frame` | Encoded video/image | Real-time camera streams |
| `radar_detection` | Per-frame detection set | Structured radar detections |
| `radar_tensor` | N-D float/int tensor | Raw/processed radar data cube |
| `rf_beam` | Beam sweep power vectors | Phased-array beam power measurements |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation |
| `desc_array` | Feature descriptor sets | Vector or embedding batches |

These registered types ensure consistent topic semantics without altering wire framing. New types can be registered additively through this table or extensions.

Implementations defining custom `type` and `qos_profile` values SHOULD follow the naming pattern (`myorg.depth_frame`, `DEPTH_LIVE`) and document their DDS QoS mapping.

#### **3.3.3 QoS Profiles**

QoS profiles define delivery guarantees and timing expectations for each topic type.

| Profile | Reliability | Ordering | Typical Deadline | Use Case |
|----------|--------------|----------|------------------|-----------|
| `GEOM_TILE` | Reliable | Ordered | 200 ms | 3D geometry, large tile data |
| `VIDEO_LIVE` | Best-effort | Ordered | 33 ms | Live video feeds |
| `VIDEO_ARCHIVE` | Reliable | Ordered | 200 ms | Replay or stored media |
| `RADAR_RT` | Partial | Ordered | 20 ms | Real-time radar data (detections or tensors) |
| `RF_BEAM_RT` | Best-effort | Ordered | 20 ms | Real-time beam sweep data |
| `SEG_MASK_RT` | Best-effort | Ordered | 33 ms | Live segmentation masks |
| `DESC_BATCH` | Reliable | Ordered | 100 ms | Descriptor or feature batches |

###### Notes

* Each topic advertises its `qos_profile` during discovery.
* Profiles capture trade-offs between latency, reliability, and throughput.
* Implementations may tune low-level DDS settings, but the profile name is canonical.
* Mixing unrelated data (e.g., radar + video) in a single QoS lane is discouraged.

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
- `global == true` means worldwide coverage regardless of regional hints. Producers MAY omit `bbox`, `geohash`, or `elements` in that case.
- When `global == false`, producers MAY supply any combination of regional hints; consumers SHOULD treat the union of all regions as the effective coverage.
- Manifests MAY provide any combination of `bbox`, `geohash`, and `elements`. Discovery coverage MAY omit `geohash` and rely solely on `bbox` and `aabb`. Consumers SHALL treat all hints consistently according to the Coverage Model.
- When `has_bbox == true`, `bbox` MUST contain finite coordinates; consumers SHALL reject non-finite values. When `has_bbox == false`, consumers MUST ignore `bbox` entirely. Same rules apply to `has_aabb` and `aabb`.
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
  * **Sensing Module Family**: `sensing.common` defines shared frame metadata, calibration, QoS hints, and codec descriptors. Radar, lidar, and vision profiles inherit those types and layer on their minimal deltas—`RadSensorMeta`/`RadDetectionSet`/`RadTensorMeta`/`RadTensorFrame` for radar, `PointCloud`/`ScanBlock`/`return_type` for lidar, and `ImageFrame`/`SegMask`/`FeatureArray` for vision. The provisional `rf_beam` extension adds `RfBeamMeta`/`RfBeamFrame`/`RfBeamArraySet` for phased-array beam power measurements. Deployments MAY import the specialized profiles independently but SHOULD declare the `sensing.common@1.x` dependency when they do.
  * **VIO Profile**: Raw and fused IMU and magnetometer samples for visual-inertial pipelines.
  * **SLAM Frontend Profile**: Features, descriptors, and keyframes for SLAM and SfM pipelines.
  * **Semantics Profile**: 2D and 3D detections for AR occlusion, robotics perception, and analytics.
  * **AR+Geo Profile**: GeoPose, frame transforms, and geo-anchoring structures for global alignment and persistent AR content.
* **Provisional Extensions (Optional)**
  * **Neural Profile**: Metadata for neural fields (e.g., NeRFs, Gaussian splats) and optional view-synthesis requests.
  * **Agent Profile**: Generic task and status messages for AI agents and planners.

Together, these profiles give SpatialDDS the flexibility to support robotics, AR/XR, digital twins, IoT, and AI world models—while ensuring that the wire format remains lightweight, codec-agnostic, and forward-compatible.

#### **Profile Matrix (SpatialDDS 1.5)**

- spatial.core/1.5
- spatial.discovery/1.5
- spatial.anchors/1.5
- spatial.manifest/1.5 (manifest schema profile for SpatialDDS 1.5)
- spatial.argeo/1.5
- spatial.sensing.common/1.5
- spatial.sensing.rad/1.5
- spatial.sensing.lidar/1.5
- spatial.sensing.vision/1.5
- spatial.slam_frontend/1.5
- spatial.vio/1.5
- spatial.semantics/1.5

The Sensing module family keeps sensor data interoperable: `sensing.common` unifies pose stamps, calibration blobs, ROI negotiation, and quality reporting. Radar, lidar, and vision modules extend that base without redefining shared scaffolding, ensuring multi-sensor deployments can negotiate payload shapes and interpret frame metadata consistently.
