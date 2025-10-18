// SPDX-License-Identifier: MIT
// SpatialDDS Specification 1.4 (© Open AR Cloud Initiative)

### **2.3.1 Topic Identity & QoS (Normative)**

SpatialDDS topics are identified by a structured **name**, a **type**, a **version**, and a declared **Quality-of-Service (QoS) profile**.  Together these define both *what* a stream carries and *how* it behaves on the wire.

#### Topic Naming Pattern

Each topic follows this pattern:
```
spatialdds/<domain>/<stream>/<type>/<version>
```
| Segment | Meaning | Example |
|----------|----------|----------|
| `<domain>` | Logical app domain | `perception` |
| `<stream>` | Sensor or stream ID | `cam_front` |
| `<type>` | Registered data type | `video_frame` |
| `<version>` | Schema or message version | `v1` |

##### Example
```json
{
  "name": "spatialdds/perception/radar_1/radar_tensor/v1",
  "type": "radar_tensor",
  "version": "v1",
  "qos_profile": "RADAR_RT"
}
```

#### Registered Types (v1)

| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Large, reliable transfers |
| `video_frame` | Encoded video/image | Real-time camera streams |
| `radar_tensor` | N-D float/int tensor | Structured radar data |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation |
| `desc_array` | Feature descriptor sets | Vector or embedding batches |

These registered types ensure consistent topic semantics without altering wire framing.  New types can be registered additively through this table or extensions.

#### Standard QoS Profiles (v1)

QoS profiles define delivery guarantees and timing expectations for each topic type.

| Profile | Reliability | Ordering | Typical Deadline | Use Case |
|----------|--------------|----------|------------------|-----------|
| `GEOM_TILE` | Reliable | Ordered | 200 ms | 3D geometry, large tile data |
| `VIDEO_LIVE` | Best-effort | Ordered | 33 ms | Live video feeds |
| `VIDEO_ARCHIVE` | Reliable | Ordered | 200 ms | Replay or stored media |
| `RADAR_RT` | Partial | Ordered | 20 ms | Real-time radar tensors |
| `SEG_MASK_RT` | Best-effort | Ordered | 33 ms | Live segmentation masks |
| `DESC_BATCH` | Reliable | Ordered | 100 ms | Descriptor or feature batches |

##### Notes

* Each topic advertises its `qos_profile` during discovery. 
* Profiles capture trade-offs between latency, reliability, and throughput. 
* Implementations may tune low-level DDS settings, but the profile name is canonical. 
* Mixing unrelated data (e.g., radar + video) in a single QoS lane is discouraged.

#### Discovery and Manifest Integration

Every `Announce.topics[]` entry and manifest topic reference SHALL include:
- `type` — one of the registered type values  
- `version` — the schema or message version  
- `qos_profile` — one of the standard or extended QoS names  

Consumers use these three keys to match and filter streams without inspecting payload bytes.  Brokers and routers SHOULD isolate lanes by `(topic, stream_id, qos_profile)` to avoid head-of-line blocking.

#### Implementation Guidance (Non-Normative)

* No change to on-wire framing — this metadata lives at the discovery layer.  
* Named QoS profiles simplify cross-vendor interoperability and diagnostics.  
* For custom types, follow the same naming pattern and document new QoS presets.  
* All examples and tables herein are **additive**; legacy 1.3 compatibility language has been removed.
