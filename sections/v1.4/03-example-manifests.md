## 8. Example Manifests

Manifests describe what a SpatialDDS node or dataset provides: **capabilities**, **coverage**, and **assets**. They are small JSON documents discoverable via the same bus or HTTP endpoints.

## Structure Overview
| Field | Purpose |
|-------|----------|
| `id` | Unique manifest identifier (UUID or URI) |
| `profile` | Manifest schema name and version (e.g., `spatial.manifest@1.4`) |
| `caps` | Supported profiles, features, and capabilities |
| `coverage` | Spatial or temporal extent of data |
| `assets` | Referenced content (tiles, descriptors, etc.) |

## Example Manifest (minimal)
```json
{
  "id": "manifest-001",
  "profile": "spatial.manifest@1.4",
  "caps": {
    "supported_profiles": [
      { "name": "core", "major": 1, "min_minor": 0, "max_minor": 3 }
    ],
    "features": ["lidar.range", "radar.tensor"]
  },
  "coverage": {
    "frame_ref": { "fqn": "earth-fixed", "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10" },
    "has_bbox": true,
    "bbox": [-122.420, 37.790, -122.410, 37.800],
    "geohash": ["9q8y"],
    "elements": [{
      "type": "volume",
      "has_bbox": false,
      "has_aabb": true,
      "aabb": { "min": [-122.420, 37.790, -10], "max": [-122.410, 37.800, 100] },
      "global": false
    }],
    "global": false
  },
  "assets": [{
    "kind": "features:ORB:v1",
    "uri": "https://example.org/descriptors/1",
    "mime": "application/x-array",
    "hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000"
  }]
}
```

## Field Notes
* **Capabilities (`caps`)** — declares supported profiles and feature flags. Peers use this to negotiate versions.  
* **Coverage (`coverage`)** — See §3.3.4 Coverage Model (Normative). Coverage blocks in manifests and discovery announces share the same semantics. See §2 Conventions for global normative rules.
* **Frame identity.** The `uuid` field is authoritative; `fqn` is a human-readable alias. Consumers SHOULD match frames by UUID and MAY show `fqn` in logs or UIs. See Appendix G for the full FrameRef model.
* **Assets (`assets`)** — URIs referencing external content. Each has a `kind`, `uri`, and optional `mime` and `hash`.
* All orientation fields follow the quaternion order defined in §2.1; older forms like `q_wxyz` are removed.

## Practical Guidance
* Keep manifests small and cacheable; they are for discovery, not bulk metadata.  
* When multiple frames exist, use one manifest per frame for clarity.  
* Use HTTPS, DDS, or file URIs interchangeably — the `uri` scheme is transport-agnostic.  
* Assets should prefer registered MIME types for interoperability.

## Summary
Manifests give every SpatialDDS resource a compact, self-describing identity. They express *what exists*, *where it is*, and *how to reach it* — without version-negotiation clutter or legacy fields.
