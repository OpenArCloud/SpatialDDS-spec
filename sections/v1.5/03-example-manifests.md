## 8. Manifest Schema (Normative)

The manifest schema is versioned as `spatial.manifest@MAJOR.MINOR`, consistent with the IDL profile scheme.

The manifest schema is defined as the `spatial.manifest` profile. It uses the same `name@MAJOR.MINOR` convention as IDL profiles, and `spatial.manifest@1.5` is the canonical identifier for this specification.

Manifests describe what a SpatialDDS node or dataset provides: **capabilities**, **coverage**, and **assets**. They are small JSON documents resolved via §7.5 and referenced by discovery announces.

### 8.1 Common Envelope (Normative)

Every `spatial.manifest@1.5` document MUST include the following top-level fields:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | REQUIRED | Unique manifest identifier. MUST be either a UUID or a valid `spatialdds://` URI. |
| `profile` | string | REQUIRED | MUST be `spatial.manifest@1.5`. |
| `rtype` | string | REQUIRED | Resource type: `anchor`, `anchor_set`, `content`, `tileset`, `service`, or `stream`. Determines the required type-specific block. |
| `caps` | object | OPTIONAL | Capabilities block. When present, MUST follow the same structure as discovery `Capabilities`. |
| `coverage` | object | OPTIONAL | Coverage block. When present, MUST follow the Coverage Model (§3.3.4). |
| `assets` | array | OPTIONAL | Array of `AssetRef` objects. Each entry MUST include `uri`, `media_type`, and `hash`. |
| `stamp` | object | OPTIONAL | Publication timestamp `{ "sec": <int>, "nanosec": <int> }`. |
| `ttl_sec` | integer | OPTIONAL | Cache lifetime hint in seconds. Clients SHOULD NOT use a cached manifest beyond `stamp + ttl_sec`. |
| `auth` | object | OPTIONAL | Authentication hints, consistent with `auth_hint` semantics in §3.3. |

**Validation rules (Normative)**:

- Unknown top-level fields MUST be ignored by consumers (forward compatibility).
- `profile` MUST match `spatial.manifest@1.<minor>` where `<minor>` ≥ 5. Consumers SHOULD accept any minor ≥ 5 within major 1.
- When `coverage` is present, it MUST follow all normative rules from §3.3.4, including `has_bbox`/`has_aabb` presence flags and finite coordinate requirements.
- `assets[].hash` MUST use the format `<algorithm>:<hex>` (e.g., `sha256:3af2...`).

**Envelope example (Informative)**
```json
{
  "id": "spatialdds://museum.example.org/hall1/anchor/main-entrance",
  "profile": "spatial.manifest@1.5",
  "rtype": "anchor",
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 3600
}
```

### 8.2 Type-Specific Blocks (Normative)

Each `rtype` value requires a corresponding top-level object with type-specific content. The key name matches the `rtype` value.

#### 8.2.1 `anchor` — Single Anchor Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `anchor.anchor_id` | string | REQUIRED | Matches `GeoAnchor.anchor_id`. |
| `anchor.geopose` | object | REQUIRED | GeoPose with `lat_deg`, `lon_deg`, `alt_m`, `q` (x,y,z,w), `frame_kind`, `frame_ref`. |
| `anchor.method` | string | OPTIONAL | Localization method (e.g., `Surveyed`, `GNSS`, `VisualFix`). |
| `anchor.confidence` | number | OPTIONAL | 0..1. |
| `anchor.frame_ref` | object | REQUIRED | `FrameRef` for the anchor's local frame. |
| `anchor.checksum` | string | OPTIONAL | Integrity hash for the anchor data. |

```json
{
  "id": "spatialdds://museum.example.org/hall1/anchor/main-entrance",
  "profile": "spatial.manifest@1.5",
  "rtype": "anchor",
  "anchor": {
    "anchor_id": "main-entrance",
    "geopose": {
      "lat_deg": 37.7934,
      "lon_deg": -122.3941,
      "alt_m": 12.6,
      "q": [0.0, 0.0, 0.0, 1.0],
      "frame_kind": "ENU",
      "frame_ref": {
        "uuid": "fc6a63e0-99f7-445b-9e38-0a3c8a0c1234",
        "fqn": "earth-fixed"
      }
    },
    "method": "Surveyed",
    "confidence": 0.98,
    "frame_ref": {
      "uuid": "6c2333a0-8bfa-4b43-9ad9-7f22ee4b0001",
      "fqn": "museum/hall1/map"
    }
  },
  "coverage": {
    "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
    "has_bbox": true,
    "bbox": [-122.395, 37.793, -122.393, 37.794],
    "global": false
  },
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 86400
}
```

#### 8.2.2 `anchor_set` — Anchor Bundle Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `anchor_set.set_id` | string | REQUIRED | Matches `AnchorSet.set_id`. |
| `anchor_set.title` | string | OPTIONAL | Human-readable name. |
| `anchor_set.provider_id` | string | OPTIONAL | Publishing organization. |
| `anchor_set.version` | string | OPTIONAL | Set version string. |
| `anchor_set.anchors` | array | REQUIRED | Array of anchor objects (same schema as `anchor` block above, without the envelope). |
| `anchor_set.center_lat` | number | OPTIONAL | Approximate center latitude. |
| `anchor_set.center_lon` | number | OPTIONAL | Approximate center longitude. |
| `anchor_set.radius_m` | number | OPTIONAL | Approximate coverage radius in meters. |

#### 8.2.3 `service` — Service Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `service.service_id` | string | REQUIRED | Matches `Announce.service_id`. |
| `service.kind` | string | REQUIRED | One of `VPS`, `MAPPING`, `RELOCAL`, `SEMANTICS`, `STORAGE`, `CONTENT`, `ANCHOR_REGISTRY`, `OTHER`. |
| `service.name` | string | OPTIONAL | Human-readable service name. |
| `service.org` | string | OPTIONAL | Operating organization. |
| `service.version` | string | OPTIONAL | Service version. |
| `service.connection` | object | OPTIONAL | DDS connection hints (see below). |
| `service.topics` | array | OPTIONAL | Array of `TopicMeta`-shaped objects describing available topics. |

**`service.connection` fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `domain_id` | integer | OPTIONAL | DDS domain ID. |
| `partitions` | array of string | OPTIONAL | DDS partitions. |
| `initial_peers` | array of string | OPTIONAL | DDS peer locators. |

```json
{
  "id": "spatialdds://city.example.net/downtown/service/vps-main;v=2024-q2",
  "profile": "spatial.manifest@1.5",
  "rtype": "service",
  "service": {
    "service_id": "vps-main",
    "kind": "VPS",
    "name": "Downtown Visual Positioning",
    "org": "city.example.net",
    "version": "2024-q2",
    "connection": {
      "domain_id": 42,
      "partitions": ["city/downtown"],
      "initial_peers": ["udpv4://10.0.1.50:7400"]
    },
    "topics": [
      { "name": "spatialdds/vps/cam_front/video_frame/v1", "type": "video_frame", "version": "v1", "qos_profile": "VIDEO_LIVE" }
    ]
  },
  "caps": {
    "supported_profiles": [
      { "name": "core", "major": 1, "min_minor": 0, "max_minor": 5 },
      { "name": "discovery", "major": 1, "min_minor": 0, "max_minor": 5 }
    ],
    "features": ["blob.crc32"]
  },
  "coverage": {
    "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
    "has_bbox": true,
    "bbox": [-122.420, 37.790, -122.410, 37.800],
    "global": false
  },
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 3600
}
```

#### 8.2.4 `content` — Content / Experience Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `content.content_id` | string | REQUIRED | Matches `ContentAnnounce.content_id`. |
| `content.title` | string | OPTIONAL | Human-readable title. |
| `content.summary` | string | OPTIONAL | Brief description. |
| `content.tags` | array of string | OPTIONAL | Searchable tags. |
| `content.class_id` | string | OPTIONAL | Content classification. |
| `content.dependencies` | array of string | OPTIONAL | Array of `spatialdds://` URIs required before use. |
| `content.available_from` | object | OPTIONAL | Time object — content is not valid before this. |
| `content.available_until` | object | OPTIONAL | Time object — content expires after this. |

#### 8.2.5 `tileset` — Tileset Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `tileset.tileset_id` | string | REQUIRED | Unique tileset identifier. |
| `tileset.encoding` | string | REQUIRED | Tile encoding (e.g., `glTF+Draco`, `3DTiles`, `MPEG-PCC`). |
| `tileset.frame_ref` | object | REQUIRED | `FrameRef` for the tileset's coordinate frame. |
| `tileset.version` | string | OPTIONAL | Tileset version. |
| `tileset.lod_levels` | integer | OPTIONAL | Number of LOD levels. |
| `tileset.tile_count` | integer | OPTIONAL | Total tile count (informative hint). |

#### 8.2.6 `stream` — Stream Manifest

| Field | Type | Required | Description |
|---|---|---|---|
| `stream.stream_id` | string | REQUIRED | Matches the `stream_id` used in sensing profiles. |
| `stream.topic` | object | REQUIRED | `TopicMeta`-shaped object. |
| `stream.connection` | object | OPTIONAL | Same schema as `service.connection`. |

### 8.3 JSON Schema (Normative)

An official JSON Schema for `spatial.manifest@1.5` is published at:

```
https://spatialdds.org/schemas/manifest/1.5/spatial-manifest.schema.json
```

Manifests MAY include a `$schema` field pointing to this URL for self-description.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://spatialdds.org/schemas/manifest/1.5/spatial-manifest.schema.json",
  "title": "SpatialDDS Manifest 1.5",
  "type": "object",
  "required": ["id", "profile", "rtype"],
  "properties": {
    "id": { "type": "string" },
    "profile": { "type": "string", "pattern": "^spatial\\.manifest@1\\.[5-9][0-9]*$" },
    "rtype": { "type": "string", "enum": ["anchor", "anchor_set", "content", "tileset", "service", "stream"] },
    "caps": { "$ref": "#/$defs/Capabilities" },
    "coverage": { "$ref": "#/$defs/Coverage" },
    "assets": { "type": "array", "items": { "$ref": "#/$defs/AssetRef" } },
    "stamp": { "$ref": "#/$defs/Time" },
    "ttl_sec": { "type": "integer", "minimum": 0 },
    "auth": { "type": "object" }
  },
  "oneOf": [
    { "properties": { "rtype": { "const": "anchor" } }, "required": ["anchor"] },
    { "properties": { "rtype": { "const": "anchor_set" } }, "required": ["anchor_set"] },
    { "properties": { "rtype": { "const": "service" } }, "required": ["service"] },
    { "properties": { "rtype": { "const": "content" } }, "required": ["content"] },
    { "properties": { "rtype": { "const": "tileset" } }, "required": ["tileset"] },
    { "properties": { "rtype": { "const": "stream" } }, "required": ["stream"] }
  ],
  "additionalProperties": true
}
```

### 8.4 Field Notes (Normative)
* **Capabilities (`caps`)** — declares supported profiles and feature flags. Peers use this to negotiate versions.  
* **Coverage (`coverage`)** — See §3.3.4 Coverage Model (Normative). Coverage blocks in manifests and discovery announces share the same semantics. See §2 Conventions for global normative rules.
* **Frame identity.** The `uuid` field is authoritative; `fqn` is a human-readable alias. Consumers SHOULD match frames by UUID and MAY show `fqn` in logs or UIs. See Appendix G for the full FrameRef model.
* **Assets (`assets`)** — URIs referencing external content. Each has a `uri`, `media_type`, and `hash`.
* All orientation fields follow the quaternion order defined in §2.1.

### 8.5 Practical Guidance (Informative)
* Keep manifests small and cacheable; they are for discovery, not bulk metadata.  
* When multiple frames exist, use one manifest per frame for clarity.  
* Use HTTPS, DDS, or file URIs interchangeably — the `uri` scheme is transport-agnostic.  
* Assets should prefer registered media types for interoperability.

### 8.6 Summary (Informative)
Manifests give every SpatialDDS resource a compact, self-describing identity. They express *what exists*, *where it is*, and *how to reach it*.
