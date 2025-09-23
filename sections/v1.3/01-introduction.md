## **1. Introduction (Informative)**

SpatialDDS is a protocol framework for exchanging live spatial data between devices, edge services, and digital twin backends. It
provides a common publish/subscribe fabric so that localization, mapping, perception, and content systems can cooperate while
remaining independently deployed.

### **1.1 Purpose**

SpatialDDS exists to make real-world spatial computing interoperable. It defines:

* **A shared data plane** based on the Object Management Group (OMG) Data Distribution Service (DDS) that applications can use to
  publish and subscribe to typed spatial data with deterministic Quality of Service (QoS).
* **A catalog of profiles** that bundle schema definitions for specific capabilities such as pose graphs, anchors, discovery
  manifests, and domain extensions.
* **A resolver-friendly identifier scheme** so that anchors, services, and content packs can be referenced consistently across
  transports and organizations.

These building blocks enable robotics fleets, AR clients, twin simulators, perception services, and AI agents to communicate using
well-defined semantics rather than bespoke integrations.

### **1.2 Scope**

The SpatialDDS 1.3 specification covers:

* Core schemas for pose graphs, geometry tiles, anchor definitions, discovery announcements, and manifest metadata.
* Identifier formats, resolver endpoints, and manifest requirements that allow resources to be located reliably.
* Normative behavior for discovery exchanges, baseline transports, and conformance profiles.
* Security, privacy, and authentication considerations for deployments spanning devices, enterprise networks, and public cloud
  services.

The specification does **not** prescribe rendering engines, proprietary content formats, commercial service SLAs, or internal
implementations of localization, mapping, or semantic understanding algorithms. Such components can interoperate through the
standardized interfaces defined here while remaining implementation-specific.

### **1.3 Key principles**

* **Interoperability first.** SpatialDDS is modular so that independently built systems can exchange world-state data without
  custom adapters. Wherever possible it aligns with adjacent standards such as OGC GeoPose, 3D Tiles, and Khronos OpenXR.
* **Modularity through profiles.** Implementers adopt only the profile sets that match their use case. Core functionality is
  separated from discovery, anchors, and optional extensions to avoid unnecessary coupling.
* **Global identity.** Stable identifiers expressed as `spatialdds://` URIs allow anchors, services, and content to be referenced
  across transports and over time, while resolver manifests provide rich metadata when needed.
* **Wire efficiency.** Schemas are compact and typed. Heavy payloads—geometry, feature blobs, neural assets—are transmitted out of
  band and referenced by identifier, keeping the data plane lean.
* **AI-ready, domain-neutral.** SpatialDDS is motivated by AR, robotics, and digital twins but does not privilege any one domain.
  AI agents, sensors, and enterprise systems can all publish and subscribe using the same vocabulary.

### **1.4 Document roadmap**

*Section 2* introduces the normative profiles that scope SpatialDDS deployments and how optional capabilities can be combined.
*Section 3* specifies identifiers and the URI scheme used throughout the protocol. *Section 4* describes manifest structures and
validation requirements, while *Section 5* formalizes discovery exchanges and resolver behavior. *Section 6* captures transport
expectations and QoS classes, *Section 7* outlines security and privacy considerations, and *Section 8* defines conformance
criteria. *Section 9* aggregates informative appendices, example schemas, and background material.
