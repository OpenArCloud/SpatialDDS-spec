## **1\. Introduction**

SpatialDDS is a lightweight, standards-based protocol, built on OMG DDS, for real-time exchange of spatial world models. It is designed as a shared data bus that allows devices, services, and AI agents to publish and subscribe to structured representations of the physical world — from pose graphs and 3D geometry to anchors, semantic detections, and service discovery. By providing a common substrate, SpatialDDS enables applications in robotics, AR/XR, digital twins, and smart cities to interoperate while also supporting new AI-driven use cases such as perception services, neural maps, and planning agents.

At its core, SpatialDDS is defined through IDL profiles that partition functionality into clean modules:

* **Core**: pose graphs, geometry tiles, anchors, transforms, and blobs.  
* **Discovery**: lightweight announce messages and manifests for services, coverage, anchors, and content.
* **Anchors**: durable anchors and registry updates for persistent world-locked reference points.  
* **Extensions**: optional domain-specific profiles including the shared Sensing Common base types plus VIO sensors, vision streams, SLAM frontend features, semantic detections, radar detections/tensors, lidar streams, and AR+Geo.

This profile-based design keeps the protocol lean and interoperable, while letting communities adopt only the pieces they need.

### **1.1 Conceptual Overview (Informative)**

This section explains the core ideas behind SpatialDDS without reference to specific IDL types or field names. Readers who understand these six concepts can navigate the rest of the specification efficiently. Everything below is informative — normative rules appear in §2 onward.

#### The Bus

SpatialDDS is a shared data bus. Devices, services, and AI agents publish and subscribe to typed messages describing the physical world — poses, geometry, anchors, detections, sensor streams. The bus is peer-to-peer (no central broker) and built on OMG DDS, which provides automatic discovery, schema enforcement, and fine-grained quality-of-service control. If you've used ROS 2 topics or MQTT with schemas, the publish/subscribe model is familiar. The difference is that SpatialDDS defines what the messages mean spatially, not just how they're delivered.

#### Profiles

SpatialDDS is modular. Functionality is organized into profiles — self-contained groups of message types that can be adopted independently:

* **Core** defines the universal building blocks: pose graphs, 3D geometry tiles, blob transport, and geo-anchoring primitives.
* **Discovery** lets participants find each other, advertise what they publish, and negotiate compatible versions.
* **Anchors** adds durable, world-locked reference points that persist across sessions.
* **Extensions** add domain-specific capabilities. A shared Sensing Common base provides frame metadata, calibration, ROI negotiation, and codec descriptors. Radar, lidar, and vision profiles build on that base. Additional extensions cover VIO, SLAM frontends, semantics, and AR+Geo alignment.

An implementation includes only the profiles it needs. An AR headset might use Core + Discovery + Anchors. A radar truck adds the radar extension. A digital twin backend subscribes to everything. Profile negotiation happens automatically — participants advertise what they support and the system converges on compatible versions.

#### Frames and Anchors

Every spatial message exists in a reference frame — a coordinate system identified by a UUID and a human-readable fully qualified name. Frames form a directed acyclic graph: a device has a body frame, sensors have frames relative to the body, and the body frame is related to a map frame by a transform. Anchors are special frames that are durable and globally positioned — a surveyed point on a building corner, a VPS-derived fix at a street intersection. They bridge the gap between local device coordinates and the real world, allowing multiple devices to share a common spatial context.

#### Discovery: Two Layers

Finding things happens in two stages:

1. Network bootstrap answers "where is the DDS domain?" A device arriving at a venue, connecting to a network, or scanning a QR code obtains a small bootstrap manifest containing a domain ID and initial peer addresses. Mechanisms include DNS-SD, a well-known HTTPS path, QR codes, and BLE beacons. (See §3.3.0 for the full bootstrap specification.)
2. On-bus discovery answers "what's available on this domain?" Once connected, the device subscribes to well-known discovery topics and receives announcements from services and content providers, each describing their capabilities, spatial coverage, and available data streams. The device filters for what it needs and subscribes.

#### URIs and Manifests

Every significant resource — an anchor, a service, a content bundle, a tileset — has a stable SpatialDDS URI (e.g., `spatialdds://museum.example.org/hall1/anchor/main-entrance`). URIs are lightweight handles passed around in discovery messages, QR codes, and application logic. When a client needs the full details, it resolves the URI to a manifest — a small JSON document describing the resource's capabilities, spatial coverage, and assets. Resolution follows a defined chain: check cache, try an advertised resolver, fall back to HTTPS. (See §7 for URI syntax and resolution rules; §8 for manifest structure.)

#### The Wire Stays Light

SpatialDDS messages are small and typed. Heavy content — meshes, point clouds, video frames, neural network weights — is never inlined in messages. Instead, messages carry blob references (IDs + checksums), and the actual bytes are transferred as blob chunks or fetched out-of-band via asset URIs. This keeps the bus fast and predictable even when the data behind it is large.

#### Navigating This Document

The specification is organized in two parts, as shown in the table of contents:

* **Part I (§1–§6)** provides motivation, conventions, profile descriptions, operational scenarios, and forward-looking discussion.
* **Part II (§7–Appendices)** contains the reference material: URI scheme and resolution, manifest examples, glossary, and the authoritative IDL appendices (A through E).

Most of Part I is informative context. Three sections within it contain normative rules and are labeled accordingly in their headings:

* **§2 Conventions (Normative)** — global rules for optional fields, numeric validity, quaternion order, ordering, IDL structure, and security.
* **§3.3.1 Topic Naming (Normative)** — how topic names are structured and what fields are required.
* **§3.3.4 Coverage Model (Normative)** — how spatial coverage is declared and evaluated.

In the appendices, IDL definitions (Appendices A–D) are always normative. Appendix E contains provisional extension examples and is explicitly informative. Appendix F defines the URI ABNF (normative). Appendix F.X (query expression grammar) is informative. Appendix G (frame identifiers) is an informative reference. Appendix H (operational scenarios) is informative.

When in doubt about whether something is normative: if it uses RFC 2119 keywords (MUST, SHALL, SHOULD, MAY), it's normative regardless of where it appears.

For role-specific guidance on which sections to read first, see the Reading Guide below.

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

1. **URI → Manifest lookup** – Durable SpatialDDS URIs point to JSON manifests that describe services, anchor sets, or content. Clients resolve the URI via HTTPS/TLS or a validated local cache per the SpatialURI Resolution rules (§7.5.5) to fetch capabilities, QoS hints, and connection parameters.
2. **Discovery → selecting a service** – Guided by the manifest and Discovery profile messages, participants determine which SpatialDDS services are available in their vicinity, their coverage areas, and how to engage them.
3. **Transport → messages on stream or DDS** – With a target service selected, the client joins the appropriate DDS domain/partition or auxiliary transport identified in the manifest and begins exchanging typed IDL messages for pose graphs, geometry, or perception streams.
4. **State updates / anchor resolution** – As data flows, participants publish and subscribe to state changes. Anchor registries and anchor delta messages keep spatial references aligned so downstream applications can resolve world-locked content with shared context.

This loop repeats as participants encounter new SpatialDDS URIs—keeping discovery, transport, and shared state synchronized.

### **SpatialDDS URIs**

SpatialDDS URIs give every anchor, service, and content bundle a stable handle that can be shared across devices and transports while still resolving to rich manifest metadata. They are the glue between lightweight on-bus messages and descriptive out-of-band manifests, ensuring that discovery pointers stay durable even as infrastructure moves. Section 6 (SpatialDDS URIs) defines the precise syntax, allowed types, and resolver requirements for these identifiers.
