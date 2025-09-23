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

