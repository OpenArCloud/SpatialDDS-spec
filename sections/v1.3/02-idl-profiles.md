## **2\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

### **2.1 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. All quaternion fields follow the OGC GeoPose component order `(x, y, z, w)` so orientation data can flow between GeoPose-aware systems without reordering. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

### **2.2 Discovery**

The Discovery profile adds a minimal, lightweight way to announce services, anchors, content, and registries in the real world. It complements DDS’s built-in participant and topic discovery by describing what a service does, where it operates, and how to learn more. Announcements are deliberately simple—service kind, coarse coverage (via geohash or a bounding-box array), and a pointer to a manifest for richer details. This keeps the bus lean while enabling clients to discover and connect to services such as VPS, mapping, anchor registries, semantics, or AR content providers without requiring heavy registries or complex protocols.

SpatialDDS augments these announcements with an active discovery model so clients can query for relevant resources instead of waiting passively. Deployments can expose this discovery interface using either an **HTTP binding**—where a resolver serves a well-known endpoint that accepts queries and returns filtered results—or a **DDS binding**, which maps the same query/announce pattern onto well-known topics for low-latency, distributed environments. Installations may adopt either approach or both; HTTP resolvers may also act as gateways to a DDS bus without changing the client-facing contract.

Both bindings share a common message model. A **query** identifies the resource type (for example, `tileset` or `anchor`) and an area of interest expressed as a coverage element. **Announcements** respond with matching resources, providing the resource identity, coverage, and the endpoint clients should use. For now the spatial predicate is simply *intersects*: a resource is relevant if its coverage overlaps the requested volume. The same request/response shape means applications can switch transports—or operate across mixed deployments—without rewriting discovery logic.

#### Example: HTTP resolver

An HTTP client searching for tilesets that intersect a bounding box in San Francisco would issue:

```http
POST /.well-known/spatialdds/search
Content-Type: application/json

{
  "rtype": "tileset",
  "volume": {
    "type": "bbox",
    "frame": "earth-fixed",
    "crs": "EPSG:4979",
    "bbox": [-122.42, 37.79, -122.40, 37.80]
  }
}
```

A matching response could be:

```json
[
  {
    "self_uri": "spatialdds://openarcloud.org/zone:sf/service/tileset:city3d",
    "rtype": "tileset",
    "bounds": {
      "type": "bbox",
      "frame": "earth-fixed",
      "crs": "EPSG:4979",
      "bbox": [-122.42, 37.79, -122.40, 37.80]
    },
    "endpoint": "https://example.org/tiles/city3d.json",
    "mime": "application/vnd.ogc.3dtiles+json"
  }
]
```

This is the typical shape of an HTTP discovery response. Each entry corresponds to a `ContentAnnounce` object (the same structure used in the DDS binding), keeping resolver results and bus announcements aligned.

The DDS binding mirrors this interaction with query and announce topics, letting edge deployments deliver the same discovery experience without leaving the data bus.

### **2.3 Anchors**

The Anchors profile provides a structured way to share and update collections of durable, world-locked anchors. While Core includes individual GeoAnchor messages, this profile introduces constructs such as AnchorSet for publishing bundles (e.g., a venue’s anchor pack) and AnchorDelta for lightweight updates. This makes it easy for clients to fetch a set of anchors on startup, stay synchronized through incremental changes, and request full snapshots when needed. Anchors complement VPS results by providing the persistent landmarks that make AR content and multi-device alignment stable across sessions and users.

### **2.4 Profiles Summary**

The complete SpatialDDS IDL bundle is organized into the following profiles:

* **Core Profile**  
  Fundamental building blocks: pose graphs, geometry tiles, anchors, transforms, and blob transport.  
* **Discovery Profile**
   Lightweight announce messages plus active query/response bindings for services, coverage areas, anchors, and spatial content or experiences.
* **Anchors Profile**  
  Durable anchors and the Anchor Registry, enabling persistent world-locked reference points.

Together, Core, Discovery, and Anchors form the foundation of SpatialDDS, providing the minimal set required for interoperability.

* **Extensions**  
  * **VIO Profile**: Raw and fused IMU and magnetometer samples for visual-inertial pipelines.  
  * **SLAM Frontend Profile**: Features, descriptors, and keyframes for SLAM and SfM pipelines.  
  * **Semantics Profile**: 2D and 3D detections for AR occlusion, robotics perception, and analytics.  
  * **AR+Geo Profile**: GeoPose, frame transforms, and geo-anchoring structures for global alignment and persistent AR content.  
* **Provisional Extensions (Optional)**  
  * **Neural Profile**: Metadata for neural fields (e.g., NeRFs, Gaussian splats) and optional view-synthesis requests.  
  * **Agent Profile**: Generic task and status messages for AI agents and planners.

Together, these profiles give SpatialDDS the flexibility to support robotics, AR/XR, digital twins, IoT, and AI world models—while ensuring that the wire format remains lightweight, codec-agnostic, and forward-compatible.

