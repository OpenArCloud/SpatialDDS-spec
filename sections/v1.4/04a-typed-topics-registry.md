## 4.7 Typed Topics Registry

The Typed Topics Registry prevents overloading one "blob" channel for many kinds of media. Instead, every SpatialDDS stream declares a **type**, **version**, and **QoS profile**. No change to wire framing is required; only metadata differs.

## Naming Pattern
```
spatialdds/<domain>/<stream>/<type>/<version>
```
| Segment | Meaning | Example |
|----------|----------|----------|
| `<domain>` | Logical app domain | `perception` |
| `<stream>` | Source or sensor id | `cam_front` |
| `<type>` | Data category | `video_frame` |
| `<version>` | Schema version | `v1` |

## Registered Type Values (v1)
| Type | Typical Payload | Notes |
|------|------------------|-------|
| `geometry_tile` | 3D tile data (GLB, 3D Tiles) | Usually reliable, large chunks |
| `video_frame` | Encoded video/image | High-rate, best-effort or reliable |
| `radar_tensor` | N-D float/int tensor | Fixed layout radar data |
| `seg_mask` | Binary or PNG mask | Frame-aligned segmentation |
| `desc_array` | Feature descriptor sets | Batches of vectors or embeddings |

### Example (topic URI + metadata)
```json
{
  "name": "spatialdds/perception/radar_1/radar_tensor/v1",
  "type": "radar_tensor",
  "version": "v1",
  "qos_profile": "RADAR_RT"
}
```

## Implementation Tips
* Each topic advertises its `type`, `version`, and `qos_profile` during discovery.  
* Consumers can filter or auto-subscribe by type without parsing payloads.  
* Brokers should route streams by `(topic, stream_id, qos_profile)` to avoid blocking between types.  
* New data types can be registered without wire changes; add to this registry with brief documentation.
