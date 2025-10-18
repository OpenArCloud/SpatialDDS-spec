## **7. Example Manifests**

While SpatialDDS keeps its on-bus messages small and generic, richer details about services, maps, and experiences are provided out-of-band through manifests. A manifest is a lightweight JSON document referenced by a `manifest_uri` in a discovery announce. SpatialDDS 1.4 continues the convention introduced in v1.3: manifest pointers are canonical `spatialdds://` URIs (e.g., `spatialdds://acme.services/sf/service/vps-main`) that resolve using the rules described in Section 6 (SpatialDDS URIs), guaranteeing stable identifiers even when manifests are hosted on rotating infrastructure. Manifests let providers describe capabilities, formats, coverage shapes, entry points, and assets without bloating the real-time data stream. The examples here show four common cases: a Visual Positioning Service (VPS) manifest that defines request/response topics and limits, a Mapping Service manifest that specifies tiling scheme and encodings, a Content/Experience manifest that lists anchors, tiles, and media for AR experiences, and an Anchors manifest that enumerates localization anchors with associated assets. Together they illustrate how manifests complement the DDS data plane by carrying descriptive metadata and policy.

### Manifest Versioning (Normative)

**Purpose.** Manifest schema identifiers keep discovery clients and services aligned on layout and semantics.

**Schema identifier.** Every manifest MUST include a top-level field:

```json
{ "schema_version": "manifest@1.4" }
```

**Version model.**

* Identifiers follow `name@MAJOR.MINOR` (e.g., `manifest@1.4`).
* **MAJOR** signals breaking layout or semantics; **MINOR** captures additive, backward-compatible changes.

**Reader behavior.**

* If the manifest MAJOR equals the reader’s supported MAJOR and the manifest MINOR is greater than or equal to the reader’s MINOR, the reader MUST parse the manifest and ignore unknown fields.
* If the manifest MAJOR exceeds the reader’s supported MAJOR, the reader MUST reject the manifest with a clear error.
* Producers MUST populate all fields required by the declared MAJOR version.

**Changelog & schema artifacts.**

* Each MINOR revision MUST appear in the manifest changelog and SHOULD ship with a JSON Schema (e.g., `schemas/manifest/1.4.schema.json`).

### Capabilities via Manifests (Out-of-Band, Normative)

**Purpose.** Allow consumers to evaluate compatibility and select streams using only a manifest (for example, fetched from the web or bundled with an application) without relying on live discovery.

**Placement.** Capabilities are declared both at the **manifest root** and within each **topic** entry.

#### Root-level capabilities
Manifests **SHOULD** include a `capabilities` block that advertises supported IDL profile ranges and optional feature flags:

```json
{
  "schema_version": "manifest@1.4",
  "capabilities": {
    "supported_profiles": [
      { "name": "core",           "major": 1, "min_minor": 0, "max_minor": 3 },
      { "name": "discovery",      "major": 1, "min_minor": 1, "max_minor": 2 },
      { "name": "sensing.common", "major": 1, "min_minor": 0, "max_minor": 1 },
      { "name": "sensing.rad",    "major": 1, "min_minor": 1, "max_minor": 1 }
    ],
    "preferred_profiles": [ "discovery@1.2", "core@1.*" ],
    "features": [ "blob.crc32", "rad.tensor.zstd" ]
  }
}
```

**Semantics.**
* `supported_profiles` follows the same version model as IDL negotiation: `name@MAJOR.MINOR` with Highest-Compatible-Minor selection within a shared **MAJOR** (see Section 2.0).
* `preferred_profiles` is an **optional** ordered hint to break ties **within a common MAJOR**.
* `features` is an **optional** list of vendor- or spec-defined boolean capabilities (namespaced strings recommended, for example `rad.tensor.zstd`). Unknown features MUST be ignored by readers.

#### Topic descriptors (selection hints)
Each topic entry **SHALL** declare the typed-topic keys so consumers can filter without parsing payloads:

```json
{
  "topics": [
    {
      "name": "spatialdds/perception/cam_front/video_frame/v1",
      "type": "video_frame",
      "version": "v1",
      "qos_profile": "VIDEO_LIVE"
    },
    {
      "name": "spatialdds/perception/radar_1/radar_tensor/v1",
      "type": "radar_tensor",
      "version": "v1",
      "qos_profile": "RADAR_RT"
    }
  ]
}
```

**Requirements.**
* `type`, `version`, and `qos_profile` MUST match the **Typed Topics Registry** (Section 4.7).
* A topic MUST NOT mix types; the `name` SHOULD follow the canonical path pattern (Section 4.7.1).
* Readers MAY filter topics by `type`, `version`, and `qos_profile` using only manifest contents.

#### Reader behavior (deterministic, no live discovery)
Given a manifest, a reader:
1. Parses `capabilities.supported_profiles` and selects the **Highest-Compatible-Minor** per profile.
2. Filters `topics[]` by desired `type`/`qos_profile`.
3. Optionally checks `features[]` for required capabilities.
4. Proceeds to subscribe/connect using the referenced topic names/URIs.

Unknown fields in the capabilities block MUST be ignored to preserve forward compatibility within the same manifest major.

### **Assets**

Every manifest asset now adheres to a **uniform base contract** with an optional, namespaced metadata bag:

**Base (required for every asset)**

* `uri` — how to retrieve the asset
* `media_type` — IANA or registry-friendly identifier (parameters allowed)
* `hash` — content hash, e.g., `sha256:<hex>`
* `bytes` — content length in bytes

**meta (optional, extensible)**

* `meta` is an object keyed by **namespaces**; each value is a **JSON object** whose schema is owned by that namespace.
* The base remains stable; metadata can evolve independently without changing the manifest base schema.

**Prohibited**

* Free-form `kind` strings and mixing type-specific fields into the base (for example `count`, `descriptor_bytes`, or `patch_frame`).
  Put those details under a namespaced `meta` entry instead.

**Example**

```json
  "assets": [
    {
      "uri": "s3://bucket/path/image_001.jpg",
      "media_type": "image/jpeg",
      "hash": "sha256:9b0a…",
      "bytes": 342187
    },
    {
      "uri": "https://cdn.example.com/features/scene123.json",
      "media_type": "application/vnd.sdds.features+json;algo=orb;v=1",
      "hash": "sha256:ab12…",
      "bytes": 65536,
      "meta": {
        "sensing.vision.features": {
          "count": 2048,
          "descriptor_bytes": 32
        }
      }
    }
  ]
```

All manifests in SpatialDDS 1.4 **must** publish quaternions using the canonical GeoPose component order `(x, y, z, w)` inside a single `q_xyzw` array.

Example discovery announcements would therefore carry manifest URIs such as:

* `spatial::disco::ServiceAnnounce.manifest_uri = spatialdds://acme.services/sf/service/vps-main`
* `spatial::disco::ServiceAnnounce.manifest_uri = spatialdds://acme.services/sf/service/mapping-tiles`
* `spatial::disco::ContentAnnounce.manifest_uri = spatialdds://acme.services/sf/content/market-stroll`

### Example: Discovery announce with capabilities (minimal)

```json
{
  "caps": {
    "supported_profiles": [
      { "name": "core",           "major": 1, "min_minor": 0, "max_minor": 3, "preferred": true  },
      { "name": "discovery",      "major": 1, "min_minor": 1, "max_minor": 2, "preferred": true  },
      { "name": "sensing.common", "major": 1, "min_minor": 0, "max_minor": 1, "preferred": false }
    ]
  }
}
```

SpatialDDS 1.4 retains the lighter way to explain where a service operates. Publishers can name the frame for their coverage, add a few transforms back to `"earth-fixed"`, and optionally list coarse `coverage.volumes[]` boxes. Those hints help clients decide, at a glance, whether a service overlaps the space they care about before loading heavier details.

Discovery mirrors that upgrade with optional `CoverageVolume` hints on announces and an opt-in `CoverageQuery` message for active volume requests. In v1.4 the query now carries a caller-supplied `query_id` plus a `reply_topic` so responders can correlate answers and route them to the right pub/sub path, and a new paged `CoverageResponse` mirrors the `query_id` when returning matching `ContentAnnounce` records. Implementations that ignore the active-query fields continue to interoperate.

### Frame Manifest Reference
Producers SHOULD include a manifest hint that points to a frame manifest:

```json
{
  "frames_uri": "https://example.com/rig01/frames.json",
  "frames_hash": "sha256:…"
}
```

The referenced document enumerates frames as `{uuid, fqn, parent_uuid}` tuples so consumers can validate topology and aliases independently of on-bus samples.

### **A) VPS Manifest**

*This manifest describes a Visual Positioning Service (VPS). It specifies the service identifier, version, coverage area, and the topics used for queries and responses. It also lists supported input encodings and response types, allowing clients to determine compatibility before interacting with the service.*

```json
{{include:manifests/v1.4/vps_manifest.json}}
```

### **B) Mapping Service Manifest**

*This manifest describes a Mapping service that publishes geometry tiles for a given coverage area. It defines the service identifier, version, supported encodings, and the DDS topics used for requesting and receiving tile data. It enables clients to subscribe to live or cached geometry without ambiguity about formats or endpoints.*

```json
{{include:manifests/v1.4/mapping_service_manifest.json}}
```

### **C) Content/Experience Manifest**

*This manifest describes a spatial content or experience service. It declares a content identifier, version, anchor bindings, and optional dependencies on other manifests. This allows AR applications to discover and attach experiences to shared anchors while keeping the actual content assets (e.g., 3D models, media) external to DDS.*

```json
{{include:manifests/v1.4/content_experience_manifest.json}}
```

### **D) Anchors Manifest**

*This manifest enumerates durable localization anchors for a zone and links them to relocalization or scene-alignment assets.* Each anchor entry supplies an `anchor_id`, a simplified GeoPose (latitude, longitude, altitude, quaternion), and whatever metadata or asset descriptors the publisher wants to expose (timestamps, quality hints, coverage tags, etc.). Top-level fields mirror the publisher's registry structure—no default frame assumptions or cache semantics are imposed by the specification.

```json
{{include:manifests/v1.4/anchors_manifest.json}}
```
