## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The VIO profile carries raw and fused IMU/magnetometer samples. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **VIO / Inertial Extension 1.0**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
{{include:idl/vio.idl}}
```

### **SLAM Frontend Extension 1.0**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

```idl
{{include:idl/slam_frontend.idl}}
```

### **Semantics / Perception Extension 1.0**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).*

```idl
{{include:idl/semantics.idl}}
```

### **AR + Geo Extension 1.0**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
{{include:idl/argeo.idl}}
```
