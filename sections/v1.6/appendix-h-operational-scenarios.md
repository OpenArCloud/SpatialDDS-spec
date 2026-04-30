## **Appendix H: SpatialDDS as a Grounding Layer for World Models (Informative)**

### **H.1 The Grounding Problem**

AI world models — whether learned latent dynamics (JEPA, Cosmos), foundation models for robotics (RT-2, π₀, Octo), digital twins, or planning agents — require structured, real-time observations of the physical world. The model needs to know what exists, where it is, how it's moving, and what the spatial context is.

Today, the infrastructure for connecting world models to physical reality is bespoke. Each deployment builds custom sensor pipelines, coordinate frame management, and data ingestion. The model architecture is advancing rapidly; the grounding infrastructure is not.

SpatialDDS provides this grounding layer: typed, discoverable, multi-source spatial observations on a real-time bus. Every SpatialDDS profile answers a question a world model asks:

| World Model Question | SpatialDDS Profile | Key Types |
|---|---|---|
| What objects exist and where? | `spatial.semantics` | `Detection3D`, `Detection3DSet` |
| What does it look like from here? | `spatial.sensing.vision` | `VisionFrame`, `CamIntrinsics` |
| What's the 3D structure? | `spatial.sensing.lidar` | `LidarFrame`, `LidarMeta` |
| What RF environment is here? | `spatial.sensing.radio` | `RadioScan` |
| Where am I in the world? | `spatial.core` + `spatial.argeo` | `GeoPose`, `GeoAnchor` |
| What zones exist, what's their state? | `spatial.events` | `SpatialZone`, `ZoneState` |
| What just happened? | `spatial.events` | `SpatialEvent` |
| What data sources exist? | `spatial.discovery` | `Announce`, `CoverageQuery` |
| What does this agent intend to do? | `spatial.core` | `PlannedTrajectory` |
| Which observations refer to the same thing? | `spatial.core` | `EntityBinding` |

### **H.2 Integration Patterns**

SpatialDDS does not prescribe how world models consume spatial data. Instead, it defines typed messages that bridge naturally into existing ML and robotics ecosystems:

**Recording bridge (SpatialDDS → MCAP/Parquet).** A recorder subscribes to SpatialDDS topics and writes them as MCAP files or Parquet tables. Offline training pipelines (LeRobot, Open X-Embodiment) ingest these recordings as episodes. SpatialDDS's typed messages preserve spatial semantics through the recording: coordinate frames, timestamps, uncertainties, and source provenance survive the round trip.

**Gymnasium bridge (SpatialDDS → Gym observation space).** A thin adapter wraps a SpatialDDS subscription as a Gymnasium observation space. RL agents receive structured spatial observations (detections, poses, zone states) at each step. SpatialDDS's discovery profile provides the observation-space manifest: what types are available, at what rates, with what spatial coverage.

**Inference service bridge (Model → SpatialDDS).** A world-model inference server subscribes to SpatialDDS sensor streams, runs prediction, and publishes results back to the bus as `PlannedTrajectory` or `Detection3D` predictions. The model is a SpatialDDS participant, not an external system.

### **H.3 What SpatialDDS Does Not Do**

SpatialDDS is not an AI middleware. It does not define:

- Episode structure or step indexing (use Open X-Embodiment, LeRobot, or application-specific formats).
- Action spaces or action vectors (use Gymnasium, Isaac Lab, or application-specific formats).
- Latent representations or tokenized embeddings (internal to the model).
- Reward functions or value estimates (internal to the training pipeline).
- Model weights, checkpoints, or training configuration (use ONNX, safetensors, or framework-native formats).

These concerns belong to the AI/ML ecosystem and are best served by existing, purpose-built formats. SpatialDDS's role is to provide the real-time spatial observations that these systems consume and the spatial predictions they produce — the grounding layer between the physical world and the world model.

### **H.4 Relationship to Factor Graphs and Scene Graphs**

SpatialDDS's pose-graph types (`Node`, `Edge`, `MapMeta`, `MapAlignment`) carry the inputs and outputs of factor graph inference. The Node/Edge structure is a pose graph — one specific application of factor graphs. Full factor graph interchange (arbitrary variable and factor types) is a separate concern best served by a dedicated interchange format.

Similarly, SpatialDDS does not impose a scene graph. Scene graphs are deterministic hierarchical representations of entity state (parent-child transforms, component attachment). They belong in the consumer (digital twin, game engine, BIM system), not on the bus. `EntityBinding` provides the minimal cross-topic correlation that consumers need to build their own scene graphs from SpatialDDS streams.

The layering is:

- **Factor graphs:** inside the optimizer (GTSAM, Ceres).
- **SpatialDDS:** carries observations and inferred state.
- **Scene graphs:** inside the consumer (Unity, Omniverse, twin).
