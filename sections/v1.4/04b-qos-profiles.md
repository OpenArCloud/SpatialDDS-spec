## 4.6 QoS Profiles

Quality of Service (QoS) defines the **timing and reliability** behavior for SpatialDDS topics. Rather than tuning low-level DDS parameters, developers choose from a few **named profiles**.

Each profile is a preset describing how reliably and quickly messages move between nodes.

## Core Profiles (v1)
| Name | Reliability | Ordering | Typical Deadline | Use Case |
|------|--------------|-----------|------------------|-----------|
| `GEOM_TILE` | Reliable | Ordered | 200 ms | 3D geometry, large tile data |
| `VIDEO_LIVE` | Best-effort | Ordered | 33 ms | Live camera streams |
| `VIDEO_ARCHIVE` | Reliable | Ordered | 200 ms | Replay or recorded streams |
| `RADAR_RT` | Partial | Ordered | 20 ms | Real-time radar tensors |
| `SEG_MASK_RT` | Best-effort | Ordered | 33 ms | Live segmentation masks |
| `DESC_BATCH` | Reliable | Ordered | 100 ms | Descriptor or feature batches |

### Example (topic metadata)
```json
{ "name": "spatialdds/perception/cam_front/video_frame/v1", "type": "video_frame", "version": "v1", "qos_profile": "VIDEO_LIVE" }
```

## Developer Notes
* Each topic declares its `qos_profile` directly in discovery metadata.  
* Profiles express trade-offs between latency, reliability, and throughput.  
* Applications should avoid mixing unrelated flows (e.g., radar + video) under the same QoS.  
* Implementations may fine-tune underlying DDS policies, but the **profile name is canonical** for interoperability.
