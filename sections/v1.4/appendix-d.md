## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The **Sensing Common** module supplies reusable sensing metadata, ROI negotiation structures, and codec/payload descriptors that the specialized sensor profiles build upon. The VIO profile carries raw and fused IMU/magnetometer samples. The Vision profile shares camera metadata, encoded frames, and optional feature tracks for perception pipelines. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The Radar profile streams radar tensors, derived detections, and optional ROI control. The Lidar profile transports compressed point clouds, associated metadata, and optional detections for mapping and perception workloads. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **Geometry Primitives**

*Stable frame references shared across profiles.*

```idl
{{include:idl/v1.4/geometry.idl}}
```

### **Sensing Common Extension**

*Shared base types, enums, and ROI negotiation utilities reused by all sensing profiles (radar, lidar, vision).* 

```idl
{{include:idl/v1.4/common.idl}}
```

#### Axis Encoding (Normative)

The `Axis` struct embeds a discriminated union to ensure only one encoding is transmitted on the wire.

```idl
enum AxisEncoding { CENTERS = 0, LINSPACE = 1 };
@appendable struct Linspace { double start; double step; uint32 count; };
@appendable union AxisSpec switch (AxisEncoding) {
  case CENTERS:  sequence<double, 65535> centers;
  case LINSPACE: Linspace lin;
};
@appendable struct Axis { string name; string unit; AxisSpec spec; };
```

* `CENTERS` — Explicit sample positions carried as `double` values.
* `LINSPACE` — Uniform grid defined by `start + i * step` for `i ∈ [0, count‑1]`.
* Negative `step` indicates descending axes.
* `count` MUST be ≥ 1 and `step * (count – 1) + start` yields the last coordinate.

The legacy `start`, `step`, `centers`, and `has_centers` fields are removed to eliminate ambiguity.

### **VIO / Inertial Extension**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
{{include:idl/v1.4/vio.idl}}
```

### **Vision Extension**

*Camera intrinsics, video frames, and keypoints/tracks for perception and analytics pipelines. ROI semantics follow Sensing Common (NaN=open; axes use the CENTERS/LINSPACE union encoding).*

```idl
{{include:idl/v1.4/vision.idl}}
```

### **SLAM Frontend Extension**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

```idl
{{include:idl/v1.4/slam_frontend.idl}}
```

### **Semantics / Perception Extension**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).*

```idl
{{include:idl/v1.4/semantics.idl}}
```

### **Radar Extension**

*Radar tensor metadata, frame indices, ROI negotiation, and derived detection sets. ROI semantics follow Sensing Common (NaN=open; axes use the CENTERS/LINSPACE union encoding).*

```idl
{{include:idl/v1.4/rad.idl}}
```

### **Lidar Extension**

*Lidar metadata, compressed point cloud frames, and detections. ROI semantics follow Sensing Common (NaN=open; axes use the CENTERS/LINSPACE union encoding).*

```idl
{{include:idl/v1.4/lidar.idl}}
```

### **AR + Geo Extension**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
{{include:idl/v1.4/argeo.idl}}
```
