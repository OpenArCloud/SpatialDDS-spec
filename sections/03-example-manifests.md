## **3. Example Manifests**

While SpatialDDS keeps its on-bus messages small and generic, richer details about services, maps, and experiences are provided out-of-band through manifests. A manifest is a lightweight JSON document referenced by a `manifest_uri` in a discovery announce. Manifests let providers describe capabilities, formats, coverage shapes, entry points, and assets without bloating the real-time data stream. The examples here show four common cases: a Visual Positioning Service (VPS) manifest that defines request/response topics and limits, a Mapping Service manifest that specifies tiling scheme and encodings, a Content/Experience manifest that lists anchors, tiles, and media for AR experiences, and an Anchors manifest that enumerates localization anchors with associated assets. Together they illustrate how manifests complement the DDS data plane by carrying descriptive metadata and policy.

### **A) VPS Manifest**

*This manifest describes a Visual Positioning Service (VPS). It specifies the service identifier, version, coverage area, and the topics used for queries and responses. It also lists supported input encodings and response types, allowing clients to determine compatibility before interacting with the service.*

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

### **B) Mapping Service Manifest**

*This manifest describes a Mapping service that publishes geometry tiles for a given coverage area. It defines the service identifier, version, supported encodings, and the DDS topics used for requesting and receiving tile data. It enables clients to subscribe to live or cached geometry without ambiguity about formats or endpoints.*

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

### **C) Content/Experience Manifest**

*This manifest describes a spatial content or experience service. It declares a content identifier, version, anchor bindings, and optional dependencies on other manifests. This allows AR applications to discover and attach experiences to shared anchors while keeping the actual content assets (e.g., 3D models, media) external to DDS.*

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

### **D) Anchors Manifest**

*This manifest lists durable localization anchors for a zone and points to feature or geometry assets used for relocalization or scene alignment.* Each anchor is identified by an `anchor_id` and includes a simplified GeoPose with `lat_deg`, `lon_deg`, `alt_m`, and quaternion fields ordered `(qw,qx,qy,qz)`. A `stamp` field on each anchor records its last update time. The manifest itself also carries a top-level `stamp` denoting when the set was generated; this maps to the `stamp` field of the `AnchorSet` IDL structure. `frame_kind` defaults to `ECEF`, `frame_ref` is omitted, and no covariance matrix is supplied. Consumers needing the full `GeoPose` from `idl/core.idl` should populate missing fields accordingly.

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
