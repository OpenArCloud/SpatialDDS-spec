## **7. Example Manifests**

While SpatialDDS keeps its on-bus messages small and generic, richer details about services, maps, and experiences are provided out-of-band through manifests. A manifest is a lightweight JSON document referenced by a `manifest_uri` in a discovery announce. SpatialDDS 1.4 continues the convention introduced in v1.3: manifest pointers are canonical `spatialdds://` URIs (e.g., `spatialdds://acme.services/sf/service/vps-main`) that resolve using the rules described in Section 6 (SpatialDDS URIs), guaranteeing stable identifiers even when manifests are hosted on rotating infrastructure. Manifests let providers describe capabilities, formats, coverage shapes, entry points, and assets without bloating the real-time data stream. The examples here show four common cases: a Visual Positioning Service (VPS) manifest that defines request/response topics and limits, a Mapping Service manifest that specifies tiling scheme and encodings, a Content/Experience manifest that lists anchors, tiles, and media for AR experiences, and an Anchors manifest that enumerates localization anchors with associated assets. Together they illustrate how manifests complement the DDS data plane by carrying descriptive metadata and policy.

All manifests in SpatialDDS 1.4 **must** publish quaternions using the canonical GeoPose component order `(x, y, z, w)` inside a single `q_xyzw` array. Readers shall continue to accept legacy `q_wxyz` arrays or scalar `qw/qx/qy/qz` fields for one minor release, but they must convert them to canonical order and surface a warning when doing so. If both encodings appear, implementations must prefer `q_xyzw`.

Example discovery announcements would therefore carry manifest URIs such as:

* `spatial::disco::ServiceAnnounce.manifest_uri = spatialdds://acme.services/sf/service/vps-main`
* `spatial::disco::ServiceAnnounce.manifest_uri = spatialdds://acme.services/sf/service/mapping-tiles`
* `spatial::disco::ContentAnnounce.manifest_uri = spatialdds://acme.services/sf/content/market-stroll`

Legacy HTTPS download links can still be advertised inside the manifest body, but the discovery announcements themselves now use the SpatialDDS URI scheme so clients have a consistent, scheme-agnostic handle to resolve.

SpatialDDS 1.4 retains the lighter way to explain where a service operates. Publishers can name the frame for their coverage, add a few transforms back to `"earth-fixed"`, and optionally list coarse `coverage.volumes[]` boxes. Those hints help clients decide, at a glance, whether a service overlaps the space they care about before loading heavier details.

Discovery mirrors that upgrade with optional `CoverageVolume` hints on announces and an opt-in `CoverageQuery` message for active volume requests. Implementations that ignore the new fields continue to interoperate.

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
