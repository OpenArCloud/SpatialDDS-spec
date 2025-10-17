## 4.7 Typed Topics Registry (Normative)

**Rationale.** To avoid overloading a single “blob” channel with heterogeneous media (e.g., geometry tiles, video frames, radar tensors, segmentation masks, descriptor arrays), SpatialDDS standardizes a small set of **typed topics**. The **on-wire message framing remains unchanged**. Interoperability is achieved via shared **topic naming**, **discovery metadata**, and **QoS profiles**.

### 4.7.1 Topic Naming
Topics SHOULD follow:
```
spatialdds/<domain>/<stream>/<type>/<version>
```
Where:
- `<domain>` is a logical app domain (e.g., `mapping`, `perception`, `ar`)
- `<stream>` is a producer-meaningful stream id (e.g., `cam_front`, `radar_1`)
- `<type>` is one of the registered values in §4.7.2
- `<version>` is a semantic guard (e.g., `v1`)

**Examples**
- `spatialdds/perception/cam_front/video_frame/v1`
- `spatialdds/mapping/tiles/geometry_tile/v1`

> Note: This section does **not** alter message headers or chunk framing. Existing `ChunkHeader + bytes` remains the on-wire format.

### 4.7.2 Registered Types (v1)
A topic MUST carry **exactly one** registered type value from the table below.

| Type (string)     | Canonical Suffix | Notes (payload examples)                      |
|-------------------|------------------|-----------------------------------------------|
| `geometry_tile`   | `geometry_tile`  | 3D tiles, GLB, 3D Tiles content               |
| `video_frame`     | `video_frame`    | Encoded frames (AV1/H.264/JPEG/etc.)          |
| `radar_tensor`    | `radar_tensor`   | N-D tensors, fixed/float layouts              |
| `seg_mask`        | `seg_mask`       | Binary/RLE/PNG masks; frame-aligned           |
| `desc_array`      | `desc_array`     | Feature descriptors (e.g., ORB/NetVLAD batches)|

### 4.7.3 QoS Profiles (Normative Names)
Implementations MUST expose the following **named profiles**, mapped to their underlying transport/DDS QoS. These names are used in discovery (§4.7.4).

| Profile         | Reliability | Ordering | Deadline | Reassembly Window | Typical Chunk Size |
|-----------------|-------------|----------|----------|-------------------|--------------------|
| `GEOM_TILE`     | Reliable    | Ordered  | 200 ms   | 2 s               | L/XL               |
| `VIDEO_LIVE`    | Best-effort | Ordered  | 33 ms    | 100 ms            | S/M                |
| `VIDEO_ARCHIVE` | Reliable    | Ordered  | 200 ms   | 1 s               | M                  |
| `RADAR_RT`      | Partial     | Ordered  | 20 ms    | 150 ms            | M                  |
| `SEG_MASK_RT`   | Best-effort | Ordered  | 33 ms    | 150 ms            | S/M                |
| `DESC_BATCH`    | Reliable    | Ordered  | 100 ms   | 500 ms            | S/M                |

> “Partial” reliability: implementations MAY drop late in-window chunks while acknowledging first/last to meet deadline constraints.

### 4.7.4 Discovery (Required)
Each producer MUST announce, **per topic**, the following **topic-level** metadata (e.g., via the existing discovery/announce channel):
- `type` — one of the registered values in §4.7.2 (e.g., `video_frame`)
- `version` — the type version (e.g., `v1`)
- `qos_profile` — one of the names in §4.7.3 (e.g., `VIDEO_LIVE`)

This requirement is **topic-level** only; it does **not** introduce per-message fields and does **not** change the on-wire layout.

### 4.7.5 Conformance
- A topic MUST NOT mix different `type` values.
- Consumers MAY rely on `qos_profile` to select latency/reliability behavior without parsing payload bytes.
- Brokers/routers SHOULD isolate lanes by `(topic, stream_id, qos_profile)` to avoid head-of-line blocking across types.

### 4.7.6 Informative Guidance (non-normative)
Producers MAY attach **topic-level** metadata to assist subscribers (does not affect wire format):
- `video_frame`: `codec`, `width`, `height`, `frame_rate_hint`
- `geometry_tile`: `lod`, `content_type` (e.g., `application/3d-tiles+glb`)
- `radar_tensor`: `shape`, `dtype`, `layout`
- `seg_mask`: `width`, `height`, `encoding` (e.g., `rle`, `png`)
- `desc_array`: `descriptor_type`, `dim`, `count`

These keys are **advisory** and may be extended; normative interoperability derives from `type`, `version`, and `qos_profile`.
