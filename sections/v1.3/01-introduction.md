## **1\. Introduction**

SpatialDDS is a lightweight, standards-based protocol for real-time exchange of spatial world models. It is designed as a shared data bus that allows devices, services, and AI agents to publish and subscribe to structured representations of the physical world — from pose graphs and 3D geometry to anchors, semantic detections, and service discovery. By providing a common substrate, SpatialDDS enables applications in robotics, AR/XR, digital twins, and smart cities to interoperate while also supporting new AI-driven use cases such as perception services, neural maps, and planning agents.

At its core, SpatialDDS is defined through **IDL profiles** that partition functionality into clean modules:

* **Core**: pose graphs, geometry tiles, anchors, transforms, and blobs.  
* **Discovery**: lightweight announce messages and manifests for services, coverage, anchors, and content.
* **Anchors**: durable anchors and registry updates for persistent world-locked reference points.  
* **Extensions**: optional domain-specific profiles including VIO sensors, SLAM frontend features, semantic detections, AR+Geo, and provisional Neural/Agent profiles.

This profile-based design keeps the protocol lean and interoperable, while letting communities adopt only the pieces they need.

### **Why DDS?**

SpatialDDS builds directly on the OMG Data Distribution Service (DDS), a proven standard for real-time distributed systems. DDS provides:

* **Peer-to-peer publish/subscribe** with automatic discovery, avoiding centralized brokers.  
* **Typed data** with schema enforcement, versioning, and language bindings.  
* **Fine-grained QoS** for reliability, liveliness, durability, and latency control.  
* **Scalability** across edge devices, vehicles, and cloud backends.

This foundation ensures that SpatialDDS is not just a message format, but a full-fledged, high-performance middleware for spatial computing.

### **Benefits across domains**

* **Robotics & Autonomous Vehicles**: Share pose graphs, maps, and detections across robots, fleets, and control centers.  
* **Augmented & Mixed Reality**: Fuse VPS results and anchors into persistent, shared spatial contexts; stream geometry and semantics to clients.  
* **Digital Twins & Smart Cities**: Ingest real-time streams of geometry, anchors, and semantics into twin backends, and republish predictive overlays.  
* **IoT & Edge AI**: Integrate lightweight perception services, sensors, and planners that consume and enrich the shared world model.  
* **AI World Models & Agents**: Provide foundation models and AI agents with a structured, typed view of the physical world for perception, reasoning, and planning.

### **Design Principles**

* **Keep the wire light**  
  SpatialDDS defines compact, typed messages via IDL. Heavy or variable content (meshes, splats, masks, assets) is carried as blobs, referenced by stable IDs. This avoids bloating the bus while keeping payloads flexible.  
* **Profiles, not monoliths**  
  SpatialDDS is organized into modular profiles: Core, Discovery, and Anchors form the foundation, while optional Extensions (VIO, SLAM Frontend, Semantics, AR+Geo) and provisional profiles (Neural, Agent) add domain-specific capabilities. Implementers adopt only what they need, keeping deployments lean and interoperable.  
* **AI-ready, domain-neutral**  
  While motivated by SLAM, AR, robotics, and digital twins, the schema is deliberately generic. Agents, foundation models, and AI services can publish and subscribe alongside devices without special treatment.  
* **Anchors as first-class citizens**  
  Anchors provide durable, shared reference points that bridge positioning, mapping, and content attachment. The Anchor Registry makes them discoverable and persistent across sessions.  
* **Discovery without heaviness**
  Lightweight announce messages plus JSON manifests allow services (like VPS, mapping, or anchor registries) and content/experiences to be discovered at runtime without centralized registries.
* **Interoperability with existing standards**
  SpatialDDS is designed to align with and complement related standards such as OGC GeoPose, CityGML/3D Tiles, and Khronos OpenXR. This ensures it can plug into existing ecosystems rather than reinvent them.

### **SpatialDDS URIs**

SpatialDDS uses URIs to provide stable, global identifiers for anchors, content, and services. URIs are short handles that applications can share across devices, clouds, and transports, and they can be dereferenced to retrieve a manifest with more details.

**Syntax**

```
spatialdds://<authority>/<zone>/<type>/<id>[;v=<version>]
```

**Components**

* `<authority>` identifies the organization responsible for issuing the URI. It **MUST** be a DNS hostname or delegated subdomain that the issuer controls. Only lowercase ASCII letters (`a–z`), digits (`0–9`), and hyphen (`-`) are permitted within a label, and labels **MUST** be separated by dots (`.`). Comparison of `<authority>` values is case-insensitive, but URIs **SHOULD** be serialized in lowercase to avoid ambiguity.
* `<zone>` scopes identifiers within an authority (for example, a facility, campus, or logical shard). It **MUST** be a single path segment composed of 1–64 characters from the set `[a-z0-9_-]` and **MUST NOT** begin or end with `-` or `_`. `<zone>` values are case-sensitive, and authorities are responsible for guaranteeing uniqueness within each zone.
* `<type>` selects the semantic kind of resource being referenced. It **MUST** exactly match one of the allowed values listed below and is case-sensitive.
* `<id>` is the stable identifier assigned to the resource of the given `<type>`. It **MUST** be a 26-character Crockford Base32 ULID rendered in uppercase ASCII (`0–9`, `A–Z`, excluding `I`, `L`, `O`, and `U`). Implementations **MUST** treat `<id>` values as case-sensitive.
* `;v=<version>` is an optional semicolon-delimited parameter that advertises a specific manifest revision. When present, the `v` key **MUST** be lowercase and the `<version>` value **MUST** be 1–32 characters drawn from `[A-Za-z0-9._-]`. Authorities **MAY** use this parameter to differentiate immutable snapshots or schema-compatible updates; consumers **MUST** ignore unknown parameters.

**Allowed `<type>` values**

| `<type>` | IDL mapping | Description |
| --- | --- | --- |
| `anchor` | `spatial::anchors::AnchorEntry.anchor_id` | Durable localization anchor identifiers published through the Anchors profile. |
| `anchor-set` | `spatial::anchors::AnchorSet.set_id` | Anchor set bundles and registry revisions available through the Anchors profile. |
| `content` | `spatial::disco::ContentAnnounce.content_id` | Spatial content or experience manifests announced via the Discovery profile. |
| `service` | `spatial::disco::ServiceAnnounce.service_id` | Service manifests (e.g., VPS, mapping, relocalization) announced via the Discovery profile. |

Authorities **MUST** only issue URIs with `<type>` values from this table and **MUST** ensure that the `<id>` corresponds to the referenced IDL field. Additional types require an extension to this specification.

**Example**

```
spatialdds://museum.example.org/hall1/anchor/01J8QDFQX3W9X4CEX39M9ZP6TQ;v=3
```

To use a URI, a client asks the authority (e.g., `museum.example.org`) for the corresponding manifest. A manifest is a JSON document that describes the object (pose, coverage, endpoints, etc.). The URI is just the pointer; the manifest carries the details.

