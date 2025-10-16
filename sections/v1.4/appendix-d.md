## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The VIO profile carries raw and fused IMU/magnetometer samples. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The Radar profile streams radar tensors, derived detections, and optional ROI control. The Lidar profile transports compressed point clouds, associated metadata, and optional detections for mapping and perception workloads. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **VIO / Inertial Extension**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
{{include:idl/v1.4/vio.idl}}
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

*Radar tensor metadata, frame indices, ROI negotiation, and derived detection sets.*

```idl
{{include:idl/v1.4/rad.idl}}
```

### **Lidar Extension**

*Lidar metadata, compressed point cloud frames, and optional detections.*

```idl
{{include:idl/v1.4/lidar.idl}}
```

### **AR + Geo Extension**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
{{include:idl/v1.4/argeo.idl}}
```
