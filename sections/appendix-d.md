## **Appendix D: Extension Profiles**

*These extensions provide domain-specific capabilities beyond the Core profile. The VIO profile carries raw and fused IMU/magnetometer samples. The SLAM Frontend profile adds features and keyframes for SLAM and SfM pipelines. The Semantics profile allows 2D and 3D object detections to be exchanged for AR, robotics, and analytics use cases. The AR+Geo profile adds GeoPose, frame transforms, and geo-anchoring structures, which allow clients to align local coordinate systems with global reference frames and support persistent AR content.*

### **VIO / Inertial Extension 1.0**

*Raw IMU/mag samples, 9-DoF bundles, and fused state outputs.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS VIO/Inertial 1.2

module spatial {
  module vio {

    typedef spatial::core::Time Time;

    // IMU calibration
    @appendable struct ImuInfo {
      @key string imu_id;
      string frame_id;
      double accel_noise_density;    // (m/s^2)/√Hz
      double gyro_noise_density;     // (rad/s)/√Hz
      double accel_random_walk;      // (m/s^3)/√Hz
      double gyro_random_walk;       // (rad/s^2)/√Hz
      Time   stamp;
    };

    // Raw IMU sample
    @appendable struct ImuSample {
      @key string imu_id;
      double accel[3];               // m/s^2
      double gyro[3];                // rad/s
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    // Magnetometer
    @appendable struct MagnetometerSample {
      @key string mag_id;
      double mag[3];                 // microtesla
      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
    };

    // Convenience raw 9-DoF bundle
    @appendable struct SensorFusionSample {
      @key string fusion_id;         // e.g., device id
      double accel[3];               // m/s^2
      double gyro[3];                // rad/s
      double mag[3];                 // microtesla
      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
    };

    // Fused state (orientation ± position)
    enum FusionMode { ORIENTATION_3DOF = 0, ORIENTATION_6DOF = 1, POSE_6DOF = 2 };
    enum FusionSourceKind { EKF = 0, AHRS = 1, VIO = 2, IMU_ONLY = 3, MAG_AIDED = 4, AR_PLATFORM = 5 };

    @appendable struct FusedState {
      @key string fusion_id;
      FusionMode       mode;
      FusionSourceKind source_kind;

      double q[4];                   // quaternion (w,x,y,z)
      boolean has_position;
      double t[3];                   // meters, in frame_id

      double gravity[3];             // m/s^2 (NaN if unknown)
      double lin_accel[3];           // m/s^2 (NaN if unknown)
      double gyro_bias[3];           // rad/s (NaN if unknown)
      double accel_bias[3];          // m/s^2 (NaN if unknown)

      double cov_orient[9];          // 3x3 covariance (NaN if unknown)
      double cov_pos[9];             // 3x3 covariance (NaN if unknown)

      Time   stamp;
      string frame_id;
      string source_id;
      uint64 seq;
      double quality;                // 0..1
    };

  }; // module vio
};
```

### **SLAM Frontend Extension 1.0**

*Per-keyframe features, matches, landmarks, tracks, and camera calibration.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS SLAM Frontend 1.2

module spatial {
  module slam_frontend {

    // Reuse core: Time, etc.
    typedef spatial::core::Time Time;

    // Camera calibration
    enum DistortionModelKind { NONE = 0, RADTAN = 1, EQUIDISTANT = 2, KANNALA_BRANDT = 3 };

    @appendable struct CameraInfo {
      @key string camera_id;
      uint32 width;  uint32 height;   // pixels
      double fx; double fy;           // focal (px)
      double cx; double cy;           // principal point (px)
      DistortionModelKind dist_kind;
      sequence<double, 8> dist;       // model params (bounded)
      string frame_id;                // camera frame
      Time   stamp;                   // calib time (or 0 if static)
    };

    // 2D features & descriptors per keyframe
    @appendable struct Feature2D {
      double u; double v;     // pixel coords
      float  scale;           // px
      float  angle;           // rad [0,2π)
      float  score;           // detector response
    };

    @appendable struct KeyframeFeatures {
      @key string node_id;                  // keyframe id
      string camera_id;
      string desc_type;                     // "ORB32","BRISK64","SPT256Q",...
      uint32 desc_len;                      // bytes per descriptor
      boolean row_major;                    // layout hint
      sequence<Feature2D, 4096> keypoints;  // ≤4096
      sequence<uint8, 1048576> descriptors; // ≤1 MiB packed bytes
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    // Optional cross-frame matches
    @appendable struct FeatureMatch {
      string node_id_a;  uint32 idx_a;
      string node_id_b;  uint32 idx_b;
      float  score;      // similarity or distance
    };

    @appendable struct MatchSet {
      @key string match_id;                // e.g., "kf_12<->kf_18"
      sequence<FeatureMatch, 8192> matches;
      Time   stamp;
      string source_id;
    };

    // Sparse 3D landmarks & tracks (optional)
    @appendable struct Landmark {
      @key string lm_id;
      string map_id;
      double p[3];
      double cov[9];                       // 3x3 pos covariance; NaN if unknown
      sequence<uint8, 4096> desc;          // descriptor bytes
      string desc_type;
      Time   stamp;
      string source_id;
      uint64 seq;
    };

    @appendable struct TrackObs {
      string node_id;                      // observing keyframe
      double u; double v;                  // pixel coords
    };

    @appendable struct Tracklet {
      @key string track_id;
      string lm_id;                        // optional link to Landmark
      sequence<TrackObs, 64> obs;          // ≤64 obs
      string source_id;
      Time   stamp;
    };

  }; // module slam_frontend
};
```

### **Semantics / Perception Extension 1.0**

*2D detections tied to keyframes; 3D oriented boxes in world frames (optionally tiled).*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS Semantics 1.2

module spatial {
  module semantics {

    typedef spatial::core::Time Time;
    typedef spatial::core::TileKey TileKey;

    // 2D detections per keyframe (image space)
    @appendable struct Detection2D {
      @key string det_id;       // unique per publisher
      string node_id;           // keyframe id
      string camera_id;         // camera
      string class_id;          // ontology label
      float  score;             // [0..1]
      float  bbox[4];           // [u_min,v_min,u_max,v_max] (px)
      boolean has_mask;         // if a pixel mask exists
      string  mask_blob_id;     // BlobChunk ref (role="mask")
      Time   stamp;
      string source_id;
    };

    @appendable struct Detection2DSet {
      @key string set_id;                 // batch id (e.g., node_id + seq)
      string node_id;
      string camera_id;
      sequence<Detection2D, 256> dets;    // ≤256
      Time   stamp;
      string source_id;
    };

    // 3D detections in world/local frame (scene space)
    @appendable struct Detection3D {
      @key string det_id;
      string frame_id;           // e.g., "map" (pose known elsewhere)
      boolean has_tile;
      TileKey tile_key;          // valid when has_tile = true

      string class_id;           // semantic label
      float  score;              // [0..1]

      // Oriented bounding box in frame_id
      double center[3];          // m
      double size[3];            // width,height,depth (m)
      double q[4];               // orientation (w,x,y,z)

      // Uncertainty (optional; NaN if unknown)
      double cov_pos[9];         // 3x3 position covariance
      double cov_rot[9];         // 3x3 rotation covariance

      // Optional instance tracking
      string track_id;

      Time   stamp;
      string source_id;
    };

    @appendable struct Detection3DSet {
      @key string set_id;                 // batch id
      string frame_id;                    // common frame for the set
      boolean has_tile;
      TileKey tile_key;                   // valid when has_tile = true
      sequence<Detection3D, 128> dets;    // ≤128
      Time   stamp;
      string source_id;
    };

  }; // module semantics
};
```

### **AR + Geo Extension 1.0**

*Geo-fixed nodes for easy consumption by AR clients & multi-agent alignment.*

```idl
// SPDX-License-Identifier: MIT
// SpatialDDS AR+Geo 1.2

module spatial {
  module argeo {

    typedef spatial::core::Time Time;
    typedef spatial::core::PoseSE3 PoseSE3;
    typedef spatial::core::GeoPose GeoPose;

    @appendable struct NodeGeo {
      string map_id;
      @key string node_id;      // same id as core::Node
      PoseSE3 pose;             // local pose in map frame
      GeoPose geopose;          // corresponding global pose (WGS84/ECEF/ENU/NED)
      double  cov[36];          // 6x6 covariance in local frame; NaN if unknown
      Time    stamp;
      string  frame_id;         // local frame
      string  source_id;
      uint64  seq;
      uint64  graph_epoch;
    };

  }; // module argeo
};
```
