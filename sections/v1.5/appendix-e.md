## **Appendix E: Provisional Extension Examples**

These provisional extensions are intentionally minimal and subject to breaking changes in future versions. Implementers SHOULD treat all struct layouts as unstable and MUST NOT assume wire compatibility across spec revisions.

### **Example: Neural Extension (Provisional)**

This profile describes neural scene representations — such as NeRFs, Gaussian splats, and neural SDFs — and provides a request/reply pattern for view synthesis. A mapping service might publish a `NeuralFieldMeta` describing a Gaussian splat covering part of a city block, and an AR client could request novel views from arbitrary camera poses.

The profile intentionally avoids prescribing model internals. `model_format` is a freeform string that identifies the training framework and version; model weights ride as blobs. This keeps the schema stable across the rapid evolution of neural representation research while giving consumers enough metadata to discover fields, check coverage, and request renders.

`NeuralFieldMeta` follows the same static-meta pattern as `RadSensorMeta` and `LidarMeta`: publish once with RELIABLE + TRANSIENT_LOCAL QoS so late joiners receive the current state. `ViewSynthesisRequest` and `ViewSynthesisResponse` follow the request/reply pattern used by `SnapshotRequest` and `SnapshotResponse`.

```idl
{{include:idl/v1.5/examples/neural_example.idl}}
```

**Example JSON (Informative)**
```json
{
  "field_id": "splat/downtown-sf-block-7",
  "rep_type": "GAUSSIAN_SPLAT",
  "model_format": "inria-3dgs-v1",
  "frame_ref": {
    "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10",
    "fqn": "earth-fixed"
  },
  "has_extent": true,
  "extent": {
    "min_xyz": [-122.420, 37.790, -5.0],
    "max_xyz": [-122.410, 37.800, 50.0]
  },
  "has_quality": true,
  "quality": 0.85,
  "checkpoint": "epoch-30000",
  "model_blobs": [
    { "blob_id": "gs-weights-001", "role": "weights", "checksum": "sha256:a1b2c3..." },
    { "blob_id": "gs-pointcloud-001", "role": "point_cloud", "checksum": "sha256:d4e5f6..." }
  ],
  "supported_outputs": ["RGB", "DEPTH", "NORMALS"],
  "has_render_time_ms": true,
  "render_time_ms": 12.5,
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "schema_version": "spatial.neural/1.5"
}
```

### **Example: Agent Extension (Provisional)**

This profile provides lightweight task coordination for AI agents and planners operating over the SpatialDDS bus. It covers two layers:

- **Single-task lifecycle.** A planner publishes `TaskRequest` messages describing spatial tasks — navigate to a location, observe a region, build a map — and agents claim and report progress via `TaskStatus`.
- **Fleet coordination.** Agents advertise availability and capabilities via `AgentStatus`. When multiple agents can handle a task, they may publish `TaskOffer` bids. The coordinator selects an agent via `TaskAssignment`. If an agent cannot finish, it publishes `TaskHandoff` with continuation context so the next agent picks up where it left off.

The design is deliberately minimal. Task-specific parameters are carried as freeform JSON in `params` fields, avoiding premature schema commitment for the wide variety of agent capabilities in robotics, drone fleets, AR-guided workflows, and AI services. Spatial targeting reuses the existing `PoseSE3`, `FrameRef`, and `SpatialUri` types so tasks can reference any addressable resource on the bus.

The profile defines **what information agents and coordinators exchange**, not **how allocation decisions are made**. A round-robin dispatcher, a market-based auction, a centralized optimizer, and a human dispatcher all consume the same typed messages. The allocation algorithm is an application-layer concern.

```idl
{{include:idl/v1.5/examples/agent_example.idl}}
```

**Example JSON (Informative)**

Task Request:
```json
{
  "task_id": "task/survey-block-7",
  "type": "OBSERVE",
  "priority": "HIGH",
  "requester_id": "planner/fleet-coordinator",
  "has_target_pose": true,
  "target_pose": {
    "t": [-122.415, 37.795, 30.0],
    "q": [0.0, 0.0, 0.0, 1.0]
  },
  "has_target_frame": true,
  "target_frame": {
    "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10",
    "fqn": "earth-fixed"
  },
  "has_target_uri": false,
  "params": "{\"sensor\": \"cam_nadir\", \"duration_sec\": 120, \"overlap\": 0.4}",
  "has_deadline": true,
  "deadline": { "sec": 1714074000, "nanosec": 0 },
  "stamp": { "sec": 1714070400, "nanosec": 0 },
  "ttl_sec": 300
}
```

Task Status:
```json
{
  "task_id": "task/survey-block-7",
  "state": "IN_PROGRESS",
  "agent_id": "drone/unit-14",
  "has_progress": true,
  "progress": 0.45,
  "has_result_uri": false,
  "diagnostic": "",
  "stamp": { "sec": 1714071200, "nanosec": 0 }
}
```

**Topic Layout**

| Type | Topic | QoS | Notes |
|---|---|---|---|
| `TaskRequest` | `spatialdds/agent/tasks/task_request/v1` | RELIABLE + TRANSIENT_LOCAL, KEEP_LAST(1) per key | Coordinator publishes tasks. |
| `TaskStatus` | `spatialdds/agent/tasks/task_status/v1` | RELIABLE + VOLATILE, KEEP_LAST(1) per key | Agent reports lifecycle state. |
| `AgentStatus` | `spatialdds/agent/fleet/agent_status/v1` | RELIABLE + TRANSIENT_LOCAL, KEEP_LAST(1) per key | Agent advertises availability. Late joiners see all agents. |
| `TaskOffer` | `spatialdds/agent/fleet/task_offer/v1` | RELIABLE + VOLATILE, KEEP_LAST(1) per key | Optional: agent bids on a task. |
| `TaskAssignment` | `spatialdds/agent/fleet/task_assignment/v1` | RELIABLE + TRANSIENT_LOCAL, KEEP_LAST(1) per key | Coordinator assigns task to agent. |
| `TaskHandoff` | `spatialdds/agent/fleet/task_handoff/v1` | RELIABLE + VOLATILE, KEEP_ALL | Agent requests task transfer with context. |

**QoS defaults for agent topics**

| Topic | Reliability | Durability | History |
|---|---|---|---|
| `task_request` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `task_status` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `agent_status` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `task_offer` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `task_assignment` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `task_handoff` | RELIABLE | VOLATILE | KEEP_ALL |

Agent Status:
```json
{
  "agent_id": "drone/unit-14",
  "name": "Drone Unit 14",
  "state": "IDLE",
  "capable_tasks": ["NAVIGATE", "OBSERVE", "MAP"],
  "has_pose": true,
  "pose": {
    "t": [12.5, -3.2, 1.1],
    "q": [0.0, 0.0, 0.0, 1.0]
  },
  "has_frame_ref": true,
  "frame_ref": {
    "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10",
    "fqn": "facility-west/enu"
  },
  "has_geopose": false,
  "has_battery_pct": true,
  "battery_pct": 0.72,
  "has_payload_kg": true,
  "payload_kg": 0.0,
  "has_payload_capacity_kg": true,
  "payload_capacity_kg": 2.5,
  "has_range_remaining_m": true,
  "range_remaining_m": 4200.0,
  "has_current_task_id": false,
  "has_queue_depth": true,
  "queue_depth": 0,
  "stamp": { "sec": 1714071000, "nanosec": 0 },
  "ttl_sec": 30
}
```

Task Offer:
```json
{
  "offer_id": "offer/unit-14/survey-block-7",
  "task_id": "task/survey-block-7",
  "agent_id": "drone/unit-14",
  "cost": 142.5,
  "has_eta_sec": true,
  "eta_sec": 45.0,
  "has_distance_m": true,
  "distance_m": 310.0,
  "has_battery_pct": true,
  "battery_pct": 0.72,
  "params": "{\"route\": \"direct\", \"estimated_energy_pct\": 0.18}",
  "stamp": { "sec": 1714071005, "nanosec": 0 },
  "ttl_sec": 30
}
```

Task Assignment:
```json
{
  "task_id": "task/survey-block-7",
  "agent_id": "drone/unit-14",
  "coordinator_id": "planner/fleet-coordinator",
  "has_offer_id": true,
  "offer_id": "offer/unit-14/survey-block-7",
  "has_params_override": false,
  "stamp": { "sec": 1714071010, "nanosec": 0 }
}
```

Task Handoff:
```json
{
  "task_id": "task/survey-block-7",
  "handoff_id": "handoff/unit-14/survey-block-7/001",
  "from_agent_id": "drone/unit-14",
  "reason": "battery below 15%",
  "has_progress": true,
  "progress": 0.63,
  "has_last_pose": true,
  "last_pose": {
    "t": [45.2, 12.8, 30.0],
    "q": [0.0, 0.0, 0.38, 0.92]
  },
  "has_last_frame": true,
  "last_frame": {
    "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10",
    "fqn": "earth-fixed"
  },
  "context": "{\"waypoints_remaining\": [[50.1, 15.0, 30.0], [55.3, 18.2, 30.0]], \"images_captured\": 147}",
  "has_preferred_agent_id": false,
  "stamp": { "sec": 1714072800, "nanosec": 0 }
}
```

### **Example: RF Beam Sensing Extension (Provisional)**

This profile provides typed transport for phased-array beam power measurements used in ISAC research. It defines static array metadata (`RfBeamMeta`), per-sweep power vectors (`RfBeamFrame`), and multi-array batches (`RfBeamArraySet`). The design follows the Meta/Frame pattern used elsewhere in the sensing profiles and is intentionally provisional.

```idl
{{include:idl/v1.5/examples/rf_beam_example.idl}}
```

### **Integration Notes (Informative)**

Discovery integration: Neural and agent services advertise via `Announce` with `ServiceKind::OTHER`. To signal neural or agent capabilities, services SHOULD include feature flags in `caps.features` such as `neural.field_meta`, `neural.view_synth`, or `agent.tasking`.

Topic naming: following `spatialdds/<domain>/<stream>/<type>/<version>`:

| Message | Suggested Topic Pattern |
|---|---|
| `NeuralFieldMeta` | `spatialdds/neural/<field_id>/field_meta/v1` |
| `ViewSynthesisRequest` | `spatialdds/neural/<field_id>/view_synth_req/v1` |
| `ViewSynthesisResponse` | Uses `reply_topic` from request |
| `TaskRequest` | `spatialdds/agent/tasks/task_request/v1` |
| `TaskStatus` | `spatialdds/agent/tasks/task_status/v1` |
| `AgentStatus` | `spatialdds/agent/fleet/agent_status/v1` |
| `TaskOffer` | `spatialdds/agent/fleet/task_offer/v1` |
| `TaskAssignment` | `spatialdds/agent/fleet/task_assignment/v1` |
| `TaskHandoff` | `spatialdds/agent/fleet/task_handoff/v1` |

QoS suggestions (informative):

| Message | Reliability | Durability | History |
|---|---|---|---|
| `NeuralFieldMeta` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `ViewSynthesisRequest` | RELIABLE | VOLATILE | KEEP_ALL |
| `ViewSynthesisResponse` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `TaskRequest` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `TaskStatus` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `AgentStatus` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `TaskOffer` | RELIABLE | VOLATILE | KEEP_LAST(1) per key |
| `TaskAssignment` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `TaskHandoff` | RELIABLE | VOLATILE | KEEP_ALL |

Profile matrix: `spatial.neural/1.5`, `spatial.agent/1.5`, and `spatial.sensing.rf_beam/1.5` remain in Appendix E as provisional and are not listed in the Profile Matrix in §3.5. When promoted to stable in a future version, they move to Appendix D and enter the matrix. (`spatial.mapping/1.5` and `spatial.events/1.5` are stable Appendix D extensions and are already listed in the matrix.)
