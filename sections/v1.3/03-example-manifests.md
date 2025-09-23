## **3. Example Manifests**

While SpatialDDS keeps its on-bus messages small and generic, richer details about services, maps, and experiences are provided out-of-band through manifests. A manifest is a lightweight JSON document referenced by a `manifest_uri` in a discovery announce. Manifests let providers describe capabilities, formats, coverage shapes, entry points, and assets without bloating the real-time data stream. The examples here show four common cases: a Visual Positioning Service (VPS) manifest that defines request/response topics and limits, a Mapping Service manifest that specifies tiling scheme and encodings, a Content/Experience manifest that lists anchors, tiles, and media for AR experiences, and an Anchors manifest that enumerates localization anchors with associated assets. Together they illustrate how manifests complement the DDS data plane by carrying descriptive metadata and policy.

### **A) VPS Manifest**

*This manifest describes a Visual Positioning Service (VPS). It specifies the service identifier, version, coverage area, and the topics used for queries and responses. It also lists supported input encodings and response types, allowing clients to determine compatibility before interacting with the service.*

```json
{{include:manifests/v1.3/vps_manifest.json}}
```

### **B) Mapping Service Manifest**

*This manifest describes a Mapping service that publishes geometry tiles for a given coverage area. It defines the service identifier, version, supported encodings, and the DDS topics used for requesting and receiving tile data. It enables clients to subscribe to live or cached geometry without ambiguity about formats or endpoints.*

```json
{{include:manifests/v1.3/mapping_service_manifest.json}}
```

### **C) Content/Experience Manifest**

*This manifest describes a spatial content or experience service. It declares a content identifier, version, anchor bindings, and optional dependencies on other manifests. This allows AR applications to discover and attach experiences to shared anchors while keeping the actual content assets (e.g., 3D models, media) external to DDS.*

```json
{{include:manifests/v1.3/content_experience_manifest.json}}
```

### **D) Anchors Manifest**

*This manifest lists durable localization anchors for a zone and points to feature or geometry assets used for relocalization or scene alignment.* Each anchor is identified by an `anchor_id` and includes a simplified GeoPose with `lat_deg`, `lon_deg`, `alt_m`, and quaternion fields ordered `(qw,qx,qy,qz)`. A `stamp` field on each anchor records its last update time. The manifest itself also carries a top-level `stamp` denoting when the set was generated; this maps to the `stamp` field of the `AnchorSet` IDL structure. `frame_kind` defaults to `ECEF`, `frame_ref` is omitted, and no covariance matrix is supplied. Consumers needing the full `GeoPose` from `idl/core.idl` should populate missing fields accordingly.

```json
{{include:manifests/v1.3/anchors_manifest.json}}
```
