## **SpatialDDS: A Protocol for Real-World Spatial Computing**

*An open invitation to build a shared bus for spatial data, AI world models, and digital twins.*

**Version**: 1.2  
**Date**: 12 September 2025  
**Author**: James Jackson [Open AR Cloud, Metaverse Standards Forum - Real/Virtual World Integration WG Co-chair]

## Contents
1. [Introduction](sections/01-introduction.md)
2. [IDL Profiles](sections/02-idl-profiles.md)
3. [Example Manifests](sections/03-example-manifests.md)
4. [Operational Scenarios](sections/04-operational-scenarios.md)
5. [Conclusion](sections/conclusion.md)
6. [Future Directions](sections/future-directions.md)
7. [Glossary of Acronyms](sections/glossary.md)
8. [References](sections/references.md)
9. Appendices
   - [Appendix A: Core Profile 1.0](sections/appendix-a.md)
   - [Appendix B: Discovery Profile 1.0](sections/appendix-b.md)
   - [Appendix C: Anchor Registry Profile 1.0](sections/appendix-c.md)
   - [Appendix D: Extension Profiles](sections/appendix-d.md)
   - [Appendix E: Provisional Extension Examples](sections/appendix-e.md)

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


## **2\. IDL Profiles**

The SpatialDDS IDL bundle defines the schemas used to exchange real-world spatial data over DDS. It is organized into complementary profiles: **Core**, which provides the backbone for pose graphs, geometry, and geo-anchoring; **Discovery**, which enables lightweight announcements of services, coverage, anchors, and content; and **Anchors**, which adds support for publishing and updating sets of durable world-locked anchors. Together, these profiles give devices, services, and applications a common language for building, sharing, and aligning live world models—while staying codec-agnostic, forward-compatible, and simple enough to extend for domains such as robotics, AR/XR, IoT, and smart cities.

### **2.1 Core SpatialDDS**

The Core profile defines the essential building blocks for representing and sharing a live world model over DDS. It focuses on a small, stable set of concepts: pose graphs, 3D geometry tiles, blob transport for large payloads, and geo-anchoring primitives such as anchors, transforms, and simple GeoPoses. The design is deliberately lightweight and codec-agnostic: tiles reference payloads but do not dictate mesh formats, and anchors define stable points without tying clients to a specific localization method. By centering on graph \+ geometry \+ anchoring, the Core profile provides a neutral foundation that can support diverse pipelines across robotics, AR, IoT, and smart city contexts.

### **2.2 Discovery**

The Discovery profile adds a minimal, lightweight way to announce services, anchors, content, and registries in the real world. It complements DDS’s built-in participant and topic discovery by describing what a service does, where it operates, and how to learn more. Announcements are deliberately simple—service kind, coarse coverage (via geohash or a bounding-box array `[min_lon, min_lat, max_lon, max_lat]`), and a pointer to a manifest for richer details. This keeps the bus lean while enabling clients to discover and connect to services such as VPS, mapping, anchor registries, semantics, or AR content providers without requiring heavy registries or complex protocols.

### **2.3 Anchors**

The Anchors profile provides a structured way to share and update collections of durable, world-locked anchors. While Core includes individual GeoAnchor messages, this profile introduces constructs such as AnchorSet for publishing bundles (e.g., a venue’s anchor pack) and AnchorDelta for lightweight updates. This makes it easy for clients to fetch a set of anchors on startup, stay synchronized through incremental changes, and request full snapshots when needed. Anchors complement VPS results by providing the persistent landmarks that make AR content and multi-device alignment stable across sessions and users.

### **2.4 Profiles Summary**

The complete SpatialDDS IDL bundle is organized into the following profiles:

* **Core Profile**  
  Fundamental building blocks: pose graphs, geometry tiles, anchors, transforms, and blob transport.  
* **Discovery Profile**  
   Lightweight announce messages and manifests for services, coverage areas, anchors, and spatial content or experiences.
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


## **3. Example Manifests**

While SpatialDDS keeps its on-bus messages small and generic, richer details about services, maps, and experiences are provided out-of-band through manifests. A manifest is a lightweight JSON document referenced by a `manifest_uri` in a discovery announce. Manifests let providers describe capabilities, formats, coverage shapes, entry points, and assets without bloating the real-time data stream. The examples here show four common cases: a Visual Positioning Service (VPS) manifest that defines request/response topics and limits, a Mapping Service manifest that specifies tiling scheme and encodings, a Content/Experience manifest that lists anchors, tiles, and media for AR experiences, and an Anchors manifest that enumerates localization anchors with associated assets. Together they illustrate how manifests complement the DDS data plane by carrying descriptive metadata and policy.

### **A) VPS Manifest**

*This manifest describes a Visual Positioning Service (VPS). It specifies the service identifier, version, coverage area, and the topics used for queries and responses. It also lists supported input encodings and response types, allowing clients to determine compatibility before interacting with the service.*

See [`manifests/vps_manifest.json`](../manifests/vps_manifest.json).

### **B) Mapping Service Manifest**

*This manifest describes a Mapping service that publishes geometry tiles for a given coverage area. It defines the service identifier, version, supported encodings, and the DDS topics used for requesting and receiving tile data. It enables clients to subscribe to live or cached geometry without ambiguity about formats or endpoints.*

See [`manifests/mapping_service_manifest.json`](../manifests/mapping_service_manifest.json).

### **C) Content/Experience Manifest**

*This manifest describes a spatial content or experience service. It declares a content identifier, version, anchor bindings, and optional dependencies on other manifests. This allows AR applications to discover and attach experiences to shared anchors while keeping the actual content assets (e.g., 3D models, media) external to DDS.*

See [`manifests/content_experience_manifest.json`](../manifests/content_experience_manifest.json).

### **D) Anchors Manifest**

*This manifest lists durable localization anchors for a zone and points to feature or geometry assets used for relocalization or scene alignment.* Each anchor is identified by an `anchor_id` and includes a simplified GeoPose with `lat_deg`, `lon_deg`, `alt_m`, and quaternion fields ordered `(qw,qx,qy,qz)`. A `stamp` field on each anchor records its last update time. The manifest itself also carries a top-level `stamp` denoting when the set was generated; this maps to the `stamp` field of the `AnchorSet` IDL structure. `frame_kind` defaults to `ECEF`, `frame_ref` is omitted, and no covariance matrix is supplied. Consumers needing the full `GeoPose` from `idl/core.idl` should populate missing fields accordingly.

See [`manifests/anchors_manifest.json`](../manifests/anchors_manifest.json).


## **4\. Operational Scenarios: From SLAM to AI World Models**

SpatialDDS is designed to be practical and flexible across real-world deployments. The following scenarios illustrate how the Core, Discovery, Anchors, and Extension profiles can be combined in different ways to support robotics, AR/XR, smart city, IoT, and AI-driven applications. Each scenario lists the profiles involved and the key DDS topics flowing in and out, showing how the schema maps onto actual use cases. Optional profiles such as Neural and Agent are marked clearly, allowing implementers to see future directions without requiring them in the baseline.

### **Core SLAM/SfM Scenarios**

These scenarios cover the foundational use cases for spatial mapping and localization. They show how devices and services exchange features, images, pose graphs, and geometry tiles to support SLAM and structure-from-motion pipelines, either on-device, at the edge, or in multi-agent systems.

1. **On-device Visual(-Inertial) SLAM**  
   A single device runs its own SLAM, fusing camera and IMU, publishing nodes/edges.  
* **Profiles:** Core (Pose Graph, VIO)  
* **Topics In:** raw IMU/camera  
* **Topics Out:** pg.node, pg.edge, geo.tf

2. **Device → Edge Distributed SLAM**  
   A mobile device streams features/images to an edge server for map building.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe, BlobChunk (images)  
* **Topics Out:** pg.node, pg.edge, geom.tile.\*

3. **Multi-Agent SLAM with Global Alignment**  
   Multiple devices contribute to a shared map, aligning through anchors.  
* **Profiles:** Core, Anchors  
* **Topics In:** pg.node/edge from peers  
* **Topics Out:** pg.edge (loop closures), geo.tf (frame alignment)

4. **Offline SfM / Batch Reconstruction**  
   A service reconstructs geometry from stored images/features.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** BlobChunk (image sets), feat.keyframe  
* **Topics Out:** geom.tile.meta/patch/blob

### **Service Scenarios**

These scenarios describe how SpatialDDS supports services that go beyond local SLAM, such as Visual Positioning Services (VPS), cooperative relocalization, map delivery, and anchor registries. Discovery messages and manifests play a key role here, allowing clients to find and interact with services dynamically.

5. **Relocalization / Place Recognition**  
   A service matches incoming features against a prior map for relocalization.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe  
* **Topics Out:** geo.fix, pg.nodegeo


6. **VPS — Features-only Query**  
   Client sends features; service returns a pose or node with geo anchor.  
* **Profiles:** Core, SLAM Frontend  
* **Topics In:** feat.keyframe  
* **Topics Out:** geo.fix or pg.nodegeo


7. **VPS — Image-only Query**  
   Client sends an image; service extracts features and returns pose.  
* **Profiles:** Core  
* **Topics In:** BlobChunk (role=“image/jpeg”)  
* **Topics Out:** geo.fix or pg.nodegeo


8. **Cooperative VPS / Crowd Relocalization**  
   Devices share queries and matches to improve coverage.  
* **Profiles:** Core, Discovery  
* **Topics In:** feat.keyframe, geo.fix  
* **Topics Out:** shared pg.edge or consensus geo.fix


9. **Mapping Service Consumption (Discovery)**  
   Clients discover and fetch map tiles for their area of interest.  
* **Profiles:** Core, Discovery  
* **Topics In:** disco.service, geom.tile.meta/patch/blob  
* **Topics Out:** local cache of geometry


10. **Anchor Registry Subscription (Discovery)**  
    Clients subscribe to a registry of persistent anchors.  
* **Profiles:** Core, Anchors, Discovery  
* **Topics In:** anchors.set, anchors.delta  
* **Topics Out:** geo.tf (local → anchor/world alignment)

### **Consumer Scenarios**

These scenarios focus on AR clients and applications that consume maps, anchors, and semantics. They show how SpatialDDS delivers persistent content alignment, semantic overlays, and shared localization for end-user experiences.

11. **AR Client Map Consumption**  
    An AR headset consumes geometry and anchors to render content.  
* **Profiles:** Core, Anchors  
* **Topics In:** geom.tile.\*, geo.anchor, geo.tf  
* **Topics Out:** none


12. **Semantics-Assisted Mapping**  
    A client enriches tiles with object detections for smarter AR overlays.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob  
* **Topics Out:** semantics.det.3d.set


13. **AR Client with VPS \+ Anchor Registry**  
    A client uses VPS fixes plus anchors for persistent localization.  
* **Profiles:** Core, Anchors, Discovery  
* **Topics In:** feat.keyframe or image blobs, anchors.set  
* **Topics Out:** geo.tf

### **Lifecycle / Recovery Scenario**

This scenario illustrates how a device or client can quickly catch up with the current state of the world after joining late or recovering from a failure. By fetching cached tiles and anchors, clients can synchronize efficiently without disrupting live streams.

14. **Catch-Up & Recovery (Reality Feed Style)**  
    A late joiner fetches cached tiles/anchors to sync quickly.  
* **Profiles:** Core, Anchors  
* **Topics In:** geom.tile.meta/patch/blob, anchors.set  
* **Topics Out:** resumed pg.node/edge

### **AI & World-Model Extensions**

These scenarios extend SpatialDDS beyond SLAM and AR into the realm of AI agents, neural maps, and digital twins. They demonstrate how AI perception services, planning agents, and predictive twin backends can plug into the same bus, consuming and enriching the shared world model. Neural and Agent profiles are optional extensions, and scenarios that use them are marked accordingly.

15. **VLM/Detector as a Perception Service**  
    An AI model consumes images and publishes 2D/3D detections.  
* **Profiles:** Core, Semantics (+ SLAM Frontend if features in)  
* **Topics In:** geom.tile.blob, optionally feat.keyframe  
* **Topics Out:** semantics.det.2d.set, semantics.det.3d.set


16. **Captioning / Visual QA Agent**  
    A vision-language model provides captions/labels tied to anchors or tiles.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob, geo.anchor  
* **Topics Out:** semantics.det.2d.set (with captions), agent.answer (optional)


17. **Neural Map — Remote View Synthesis** *(optional Neural extension)*  
    Thin clients request rendered views from a neural map service.  
* **Profiles:** Core (+ Neural if adopted)  
* **Topics In:** neural.view.req  
* **Topics Out:** neural.view.resp with images


18. **Neural Map — Asset Streaming** *(optional Neural extension)*  
    Neural assets (e.g., Gaussian splats) are streamed as blobs for local rendering.  
* **Profiles:** Core (+ Neural if adopted)  
* **Topics In:** geom.tile.meta/patch (encoding=“nerf”/“gaussians”)  
* **Topics Out:** none


19. **Digital Twin Ingest (Realtime → Twin Backend)**  
    A digital twin backend ingests SpatialDDS streams for persistent modeling.  
* **Profiles:** Core, Semantics, Anchors  
* **Topics In:** pg.node/edge, geom.tile.\*, geo.anchor, semantics.det.3d.set  
* **Topics Out:** none


20. **Digital Twin → SpatialDDS (Predictive Overlays)**  
    A twin service publishes predictions or overlays back to clients.  
* **Profiles:** Core, Semantics  
* **Topics In:** none (internal twin logic)  
* **Topics Out:** semantics.det.3d.set, geom.tile.\*


21. **Route/Task Planning Agent** *(optional Agent extension)*  
    An AI agent consumes world state and publishes goals or routes.  
* **Profiles:** Core (+ Agent if adopted)  
* **Topics In:** pg.node, geo.tf, semantics.det.3d.set, geo.anchor  
* **Topics Out:** task.route, task.goal, or agent.task/status


22. **Human-in-the-Loop Labeling & Training Data Capture**  
    Detections are corrected by humans and fed back for model improvement.  
* **Profiles:** Core, Semantics  
* **Topics In:** geom.tile.blob, semantics.det.\* (proposals)  
* **Topics Out:** semantics.det.\* (corrected), data.capture.meta

Taken together, these scenarios show how SpatialDDS functions as a real-time bus for spatial world models. From raw sensing and SLAM pipelines to AR content, digital twins, and AI-driven perception and planning, the protocol provides a common substrate that lets diverse systems interoperate without heavy gateways or custom formats. This positions SpatialDDS as a practical foundation for AI world models that are grounded in the physical world.


## **5. Conclusion**

SpatialDDS provides a lightweight, standards-based framework for exchanging real-world spatial data over DDS. By organizing schemas into modular profiles — with Core, Discovery, and Anchors as the foundation and Extensions adding domain-specific capabilities — it supports everything from SLAM pipelines and AR clients to digital twins, smart city infrastructure, and AI-driven world models. Core elements such as pose graphs, geometry tiles, anchors, and discovery give devices and services a shared language for building and aligning live models of the world, while provisional extensions like Neural and Agent point toward richer semantics and autonomous agents. Taken together, SpatialDDS positions itself as a practical foundation for real-time spatial computing—interoperable, codec-agnostic, and ready to serve as the data bus for AI and human experiences grounded in the physical world.


## **6. Future Directions**

While SpatialDDS establishes a practical baseline for real-time spatial computing, several areas invite further exploration:

* **Reference Implementations**  
  Open-source libraries and bridges to existing ecosystems (e.g., ROS 2, OpenXR, OGC APIs) would make it easier for developers to adopt SpatialDDS in robotics, AR, and twin platforms.  
* **Semantic Enrichment**  
  Extending beyond 2D/3D detections, future work could align with ontologies and scene graphs to enable richer machine-readable semantics for AI world models and analytics.  
* **Neural Integration**  
  Provisional support for neural fields (NeRFs, Gaussian splats) could mature into a stable profile, ensuring consistent ways to stream and query neural representations across devices and services.  
* **Agent Interoperability**  
  Lightweight tasking and coordination schemas could evolve into a standard Agent profile, supporting multi-agent planning and human-AI collaboration at scale.  
* **Standards Alignment**  
  Ongoing coordination with OGC, Khronos, W3C, and GSMA initiatives will help ensure SpatialDDS complements existing geospatial, XR, and telecom standards rather than duplicating them.

Together, these directions point toward a future where SpatialDDS is not just a protocol but a foundation for an open, interoperable ecosystem of real-time world models.

We invite implementers, researchers, and standards bodies to explore SpatialDDS, contribute extensions, and help shape it into a shared backbone for real-time spatial computing and AI world models.


## **7. Glossary of Acronyms**

**AI** – Artificial Intelligence

**AR** – Augmented Reality

**DDS** – Data Distribution Service (OMG standard middleware)

**GSMA** – GSM Association (global mobile industry group)

**IMU** – Inertial Measurement Unit

**IoT** – Internet of Things

**MR** – Mixed Reality

**MSF** – Metaverse Standards Forum

**NeRF** – Neural Radiance Field (neural representation of 3D scenes)

**OGC** – Open Geospatial Consortium

**OMG** – Object Management Group (standards body for DDS)

**ROS** – Robot Operating System

**SfM** – Structure from Motion

**SLAM** – Simultaneous Localization and Mapping

**VIO** – Visual-Inertial Odometry

**VLM** – Vision-Language Model

**VPS** – Visual Positioning Service

**VR** – Virtual Reality

**W3C** – World Wide Web Consortium

**XR** – Extended Reality (umbrella term including AR, VR, MR)


## **8. References**

### **DDS & Middleware**

\[1\] Object Management Group. *Data Distribution Service (DDS) for Real-Time Systems.* OMG Standard. Available: [https://www.omg.org/spec/DDS](https://www.omg.org/spec/DDS)

\[2\] Object Management Group. *DDS for eXtremely Resource Constrained Environments (DDS-XRCE).* OMG Standard. Available: [https://www.omg.org/spec/DDS-XRCE](https://www.omg.org/spec/DDS-XRCE)

\[3\] eProsima. *Fast DDS Documentation.* Available: [https://fast-dds.docs.eprosima.com](https://fast-dds.docs.eprosima.com/)

\[4\] Eclipse Foundation. *Cyclone DDS.* Available: [https://projects.eclipse.org/projects/iot.cyclonedds](https://projects.eclipse.org/projects/iot.cyclonedds)

### **XR & Spatial Computing**

\[5\] Khronos Group. *OpenXR Specification.* Available: [https://www.khronos.org/openxr](https://www.khronos.org/openxr)

\[6\] Open Geospatial Consortium. *OGC GeoPose 1.0 Data Exchange Standard.* Available: [https://www.ogc.org/standards/geopose](https://www.ogc.org/standards/geopose)

### **Geospatial Standards**

\[7\] Open Geospatial Consortium. *CityGML Standard.* Available: [https://www.ogc.org/standards/citygml](https://www.ogc.org/standards/citygml)

\[8\] Geohash. *Wikipedia Entry.* Available: [https://en.wikipedia.org/wiki/Geohash](https://en.wikipedia.org/wiki/Geohash)

### **SLAM, SfM & AI World Models**

\[9\] Mur-Artal, R., Montiel, J. M. M., & Tardós, J. D. (2015). *ORB-SLAM: A Versatile and Accurate Monocular SLAM System.* IEEE Transactions on Robotics, 31(5), 1147–1163.

\[10\] Schönberger, J. L., & Frahm, J.-M. (2016). *Structure-from-Motion Revisited.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 4104–4113.

\[11\] Sarlin, P.-E., Unagar, A., Larsson, M., et al. (2020). *From Coarse to Fine: Robust Hierarchical Localization at Large Scale.* In IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 12716–12725.

\[12\] Google Research. *ARCore Geospatial API & Visual Positioning Service.* Developer Documentation. Available: [https://developers.google.com/ar](https://developers.google.com/ar)


## **Appendix A: Core Profile 1.0**

*The Core profile defines the fundamental data structures for SpatialDDS. It includes pose graphs, 3D geometry tiles, anchors, transforms, and generic blob transport. This is the minimal interoperable baseline for exchanging world models across devices and services.*


See [`../idl/core.idl`](../idl/core.idl).

## **Appendix B: Discovery Profile 1.0**

*The Discovery profile defines the lightweight announce messages and manifests that allow services, coverage areas, and spatial content or experiences to be discovered at runtime. It enables SpatialDDS deployments to remain decentralized while still providing structured service discovery.*


See [`../idl/discovery.idl`](../idl/discovery.idl).

## **Appendix C: Anchor Registry Profile 1.0**

*The Anchors profile defines durable GeoAnchors and the Anchor Registry. Anchors act as persistent world-locked reference points, while the registry makes them discoverable and maintainable across sessions, devices, and services.*


See [`../idl/anchors.idl`](../idl/anchors.idl).

## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The VIO profile carries raw and fused IMU/magnetometer samples. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **VIO / Inertial Extension 1.0**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

See [`../idl/vio.idl`](../idl/vio.idl).

### **SLAM Frontend Extension 1.0**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

See [`../idl/slam_frontend.idl`](../idl/slam_frontend.idl).

### **Semantics / Perception Extension 1.0**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).* 

See [`../idl/semantics.idl`](../idl/semantics.idl).

### **AR + Geo Extension 1.0**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

See [`../idl/argeo.idl`](../idl/argeo.idl).


## **Appendix E: Provisional Extension Examples**

The following examples illustrate how provisional extensions might be used in practice. They are not normative and are provided only to show how Neural and Agent profiles could appear on the wire.

### **Example: Neural Extension (Provisional)**

*This example shows how a service might publish metadata for a Gaussian splat field covering part of a city block.*

See [`../idl/examples/neural_example.idl`](../idl/examples/neural_example.idl).

### **Example: Agent Extension (Provisional)**

*This example shows how an AI planner could issue a navigation task and later update its status.*

See [`../idl/examples/agent_example.idl`](../idl/examples/agent_example.idl).

