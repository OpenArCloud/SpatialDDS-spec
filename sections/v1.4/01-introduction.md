## **1\. Introduction**

SpatialDDS is a lightweight, standards-based protocol, built on OMG DDS, for real-time exchange of spatial world models. It is designed as a shared data bus that allows devices, services, and AI agents to publish and subscribe to structured representations of the physical world — from pose graphs and 3D geometry to anchors, semantic detections, and service discovery. By providing a common substrate, SpatialDDS enables applications in robotics, AR/XR, digital twins, and smart cities to interoperate while also supporting new AI-driven use cases such as perception services, neural maps, and planning agents.

At its core, SpatialDDS is defined through IDL profiles that partition functionality into clean modules:

* **Core**: pose graphs, geometry tiles, anchors, transforms, and blobs.  
* **Discovery**: lightweight announce messages and manifests for services, coverage, anchors, and content.
* **Anchors**: durable anchors and registry updates for persistent world-locked reference points.  
* **Extensions**: optional domain-specific profiles including the shared Sensing Common base types plus VIO sensors, vision streams, SLAM frontend features, semantic detections, radar tensors, lidar streams, AR+Geo, and provisional Neural/Agent profiles.

This profile-based design keeps the protocol lean and interoperable, while letting communities adopt only the pieces they need.

### **Reading Guide (Informative)**

- **Architects & product planners** — Start with §1 and §2 to internalize the motivation, shared conventions, and global rules before drilling into profiles.
- **Implementers & SDK authors** — Focus on Part II plus Appendix A (core IDLs), Appendix B (discovery), Appendix C (anchors), and Appendix D (extensions).
- **Routing, filtering, and coverage developers** — Read §3.3 (Discovery), §3.3.4 (Coverage Model), and Appendix B/F.X for the binding grammars.

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
  SpatialDDS is organized into modular profiles. Core, Discovery, and Anchors form the foundation; Extension Profiles add domain-specific capabilities. Implementations include only what they need while maintaining interoperability.
* **AI-ready, domain-neutral**
  While motivated by SLAM, AR, robotics, and digital twins, the schema is deliberately generic. Agents, foundation models, and AI services can publish and subscribe alongside devices without special treatment.
* **Anchors as first-class citizens**
  Anchors provide durable, shared reference points that bridge positioning, mapping, and content attachment. The Anchor Registry makes them discoverable and persistent across sessions.
* **Discovery without heaviness**
  Lightweight announce messages plus JSON manifests allow services (like VPS, mapping, or anchor registries) and content/experiences to be discovered at runtime without centralized registries.
* **Interoperability with existing standards**
  SpatialDDS is designed to align with and complement related standards such as OGC GeoPose, CityGML/3D Tiles, and Khronos OpenXR. This ensures it can plug into existing ecosystems rather than reinvent them.

### **Specification Layers (Informative)**

| Layer | Purpose | Core Artifacts |
|-------|---------|----------------|
| **Core Transport** | Pub/Sub framing, QoS, reliability | `core`, `discovery` IDLs |
| **Spatial Semantics** | Anchors, poses, transforms, manifests | `anchors`, `geo`, `manifests` |
| **Sensing Extensions** | Radar, LiDAR, Vision modules | `sensing.*` profiles |

### **Architecture Overview & Data Flow**

Before diving into identifiers and manifests, it helps to see how SpatialDDS components interlock when a client joins the bus. The typical flow looks like:

### High-level layering

SpatialDDS follows the same four-layer model shown in the architecture diagrams:

Applications
    ↓ use
SpatialDDS Profiles
    ↓ define
DDS Topics (typed + QoS)
    ↓ are described by
Discovery & Manifests
    ↓ reference
spatial:// URIs

- Applications (AR, robotics, digital twins, telco sensing, AI runtimes) use
  SpatialDDS profiles instead of raw DDS topics.
- Profiles define the shared types, semantics, and QoS groupings.
- DDS topics carry typed streams with well-known QoS names.
- Discovery and manifests describe the available streams and their spatial
  coverage.
- URIs provide stable identifiers for anchors, maps, content, and services.

This textual view matches the layered diagrams used in the presentation.

```
SpatialDDS URI ──▶ Manifest Resolver ──▶ Discovery Topic ──▶ DDS/Data Streams ──▶ Shared State & Anchors
        │                 │                      │                   │                      │
   (§7)             (§8)                (§3.3)                   (§3)                   (§5 & Appendix C)
```

1. **URI → Manifest lookup** – Durable SpatialDDS URIs point to JSON manifests that describe services, anchor sets, or content. Clients resolve the URI according to the SpatialURI Resolution rules (§7.5) to fetch capabilities, QoS hints, and connection parameters.
2. **Discovery → selecting a service** – Guided by the manifest and Discovery profile messages, participants determine which SpatialDDS services are available in their vicinity, their coverage areas, and how to engage them.
3. **Transport → messages on stream or DDS** – With a target service selected, the client joins the appropriate DDS domain/partition or auxiliary transport identified in the manifest and begins exchanging typed IDL messages for pose graphs, geometry, or perception streams.
4. **State updates / anchor resolution** – As data flows, participants publish and subscribe to state changes. Anchor registries and anchor delta messages keep spatial references aligned so downstream applications can resolve world-locked content with shared context.

This loop repeats as participants encounter new SpatialDDS URIs—keeping discovery, transport, and shared state synchronized.

### **SpatialDDS URIs**

SpatialDDS URIs give every anchor, service, and content bundle a stable handle that can be shared across devices and transports while still resolving to rich manifest metadata. They are the glue between lightweight on-bus messages and descriptive out-of-band manifests, ensuring that discovery pointers stay durable even as infrastructure moves. Section 6 (SpatialDDS URIs) defines the precise syntax, allowed types, and resolver requirements for these identifiers.
