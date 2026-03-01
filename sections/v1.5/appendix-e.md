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
    "pose": { "t": [12.5, -3.2, 1.1], "q": [0.0, 0.0, 0.0, 1.0] },
    "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "facility-west/enu" },
    "cov": { "type": "COV_NONE" },
    "stamp": { "sec": 1714071000, "nanosec": 0 }
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
    "pose": { "t": [45.2, 12.8, 30.0], "q": [0.0, 0.0, 0.38, 0.92] },
    "frame_ref": { "uuid": "ae6f0a3e-7a3e-4b1e-9b1f-0e9f1b7c1a10", "fqn": "earth-fixed" },
    "cov": { "type": "COV_NONE" },
    "stamp": { "sec": 1714072800, "nanosec": 0 }
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

### **Example: Radio Fingerprint Extension (Provisional)**

This profile provides typed transport for radio-environment observations used by radio-assisted localization and indoor positioning pipelines. It targets commodity radios (WiFi, BLE, UWB, cellular) and closes the "radio via freeform metadata only" gap by introducing schema-enforced observation structs.

The profile defines transport only. It does not define positioning, trilateration, filtering, or sensor-fusion algorithms.

**Module ID:** `spatial.sensing.radio/1.5`  
**Dependency:** `spatial.sensing.common@1.x`  
**Status:** Provisional (K-R1 maturity gate)

#### **Overview**

`RadioSensorMeta` follows the static Meta pattern (RELIABLE + TRANSIENT_LOCAL) and publishes sensor capabilities. `RadioScan` is the streaming message carrying per-scan observations. Each scan is a snapshot of visible transmitters for one radio technology at one scan instant/window.

#### **Relationship to `sensing.rf_beam`**

`sensing.rf_beam` covers phased-array mmWave beam power vectors and ISAC-style beam management.  
`sensing.radio` covers commodity radio fingerprints and ranging observations (WiFi/BLE/UWB/cellular).  
They are complementary and may be published together by the same node.

| Profile | Scope | Typical Frequency | Key Measurement |
|---|---|---|---|
| `sensing.rf_beam` | mmWave phased arrays (28/60/140 GHz) | 10 Hz per sweep | Per-beam power vector |
| `sensing.radio` | WiFi/BLE/UWB/cellular | 0.1–10 Hz per scan | Per-transmitter RSSI/RTT/AoA/Range |

#### **IDL (Provisional)**

```idl
{{include:idl/v1.5/examples/radio_example.idl}}
```

#### **Observation Semantics (Normative)**

`measurement_kind` determines the unit and interpretation of `RadioObservation.value`.

| Kind | Value Units | Typical Source |
|---|---|---|
| `RSSI` | dBm | WiFi and BLE scans |
| `RTT_NS` | nanoseconds | WiFi FTM, UWB TWR |
| `AOA_DEG` | degrees | UWB/BLE AoA |
| `RANGE_M` | meters | Derived range |
| `RSRP` | dBm | Cellular |
| `CSI_REF` | n/a (`value` unused) | CSI blob reference workflows |

A single `RadioScan` MAY include mixed `measurement_kind` values.

#### **Identifier Conventions (Normative)**

| RadioType | Identifier Format | Example |
|---|---|---|
| `WIFI` | BSSID, lowercase colon-separated hex | `aa:bb:cc:dd:ee:ff` |
| `BLE` | UUID (uppercase with hyphens) or MAC | `12345678-1234-1234-1234-123456789ABC` |
| `UWB` | Short address or session ID | `0x1A2B` |
| `CELLULAR` | MCC-MNC-LAC-CID | `310-260-12345-67890` |

Consumers performing fingerprint matching SHOULD normalize identifiers before comparison.

#### **Scan Timing and Aggregation (Normative)**

- `stamp` MUST represent the midpoint of the scan window.
- If `has_scan_duration == true`, `scan_duration_s` MUST report the full scan-window duration.
- If `has_aggregation_window == true`, `aggregation_window_s` reports the total time window used to aggregate observations from multiple scans.
- Producers publishing raw scans SHOULD leave `has_aggregation_window = false`.

#### **Privacy Considerations (Normative Guidance)**

Radio identifiers can expose device/network identity. Producers in privacy-sensitive deployments SHOULD:
- anonymize or hash identifiers where permitted,
- avoid publishing SSIDs unless explicitly needed, and
- document identifier handling and retention policy.

#### **Topic Patterns**

| Topic | Message Type | QoS |
|---|---|---|
| `spatialdds/<scene>/radio/<sensor_id>/scan/v1` | `RadioScan` | `RADIO_SCAN_RT` |
| `spatialdds/<scene>/radio/<sensor_id>/meta/v1` | `RadioSensorMeta` | RELIABLE + TRANSIENT_LOCAL |

#### **Example JSON (Informative)**

WiFi scan:
```json
{
  "sensor_id": "hololens2-wifi-01",
  "radio_type": "WIFI",
  "scan_seq": 42,
  "stamp": { "sec": 1714071012, "nanosec": 500000000 },
  "has_scan_duration": true,
  "scan_duration_s": 2.1,
  "observations": [
    {
      "identifier": "aa:bb:cc:dd:ee:01",
      "measurement_kind": "RSSI",
      "value": -52.0,
      "has_frequency": true,
      "frequency_mhz": 5180.0,
      "has_band": true,
      "band": "BAND_5GHZ",
      "has_ssid": true,
      "ssid": "ETH-WiFi",
      "has_channel": true,
      "channel": 36
    }
  ],
  "has_aggregation_window": true,
  "aggregation_window_s": 4.0,
  "source_id": "lamar-cab-hololens-session-17",
  "schema_version": "spatial.sensing.radio/1.5"
}
```

UWB ranging round:
```json
{
  "sensor_id": "uwb-tag-reader-01",
  "radio_type": "UWB",
  "scan_seq": 5017,
  "stamp": { "sec": 1714071020, "nanosec": 250000000 },
  "observations": [
    {
      "identifier": "0x1A2B",
      "measurement_kind": "RANGE_M",
      "value": 3.21,
      "has_range": true,
      "range_m": 3.21,
      "has_range_std": true,
      "range_std_m": 0.08,
      "has_aoa_azimuth": true,
      "aoa_azimuth_deg": 23.5
    }
  ],
  "source_id": "warehouse-uwb-reader-alpha",
  "schema_version": "spatial.sensing.radio/1.5"
}
```

#### **Maturity Gate (K-R1)**

Promotion to stable requires:
1. At least one conformance dataset exercising WiFi and BLE paths with at least 20 checks passing.
2. At least one independent implementation ingesting reference WiFi/BLE files through `RadioScan`.
3. No breaking IDL changes for six months after initial publication.

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
| `RadioSensorMeta` | `spatialdds/<scene>/radio/<sensor_id>/meta/v1` |
| `RadioScan` | `spatialdds/<scene>/radio/<sensor_id>/scan/v1` |

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
| `RadioSensorMeta` | RELIABLE | TRANSIENT_LOCAL | KEEP_LAST(1) per key |
| `RadioScan` | BEST_EFFORT | VOLATILE | KEEP_LAST(1) |

Profile matrix: `spatial.neural/1.5`, `spatial.agent/1.5`, `spatial.sensing.rf_beam/1.5`, and `spatial.sensing.radio/1.5` are provisional Appendix E profiles. When promoted to stable in a future version, they move to Appendix D.
