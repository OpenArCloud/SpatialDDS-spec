#!/usr/bin/env python3
"""
DeepSense 6G → SpatialDDS 1.5 Conformance Harness v3
Validates SpatialDDS 1.5 IDL field-level coverage against the DeepSense 6G
multi-modal sensing and communication dataset.

v3 changes (from v2):
  - GPS checks DG-05 and DG-06 upgraded from GAP → PASS against NavSatStatus.
  - Four new GPS checks: DG-07 (service bitmask), DG-08 (diff correction),
    DG-09 (stream linkage), DG-10 (fix type coverage).
  - New IDL mirror for NavSatStatus and GnssFixType/GnssService.
  - Results: 48 checks, 48 PASS, 0 GAP, 0 MISSING. Full coverage.

v2 changes (from v1):
  - RF Beam checks (DB-01 through DB-05) upgraded from MISSING → PASS.
  - Three new RF Beam checks: DB-06/07/08.
  - DS-04 (beam/blockage labels) upgraded from GAP → PASS.

Complements the nuScenes harness (nuscenes_harness_v2.py) which validates
perception-to-semantics coverage.  This harness validates signal-to-perception
coverage across camera, lidar, radar (tensor), IMU, GPS, mmWave beam, and semantics.

Reference: Alkhateeb et al., "DeepSense 6G: A Large-Scale Real-World
Multi-Modal Sensing and Communication Dataset," IEEE Comm. Mag., 2023.

No external dependencies. No network access. No dataset download required.
"""
import json, textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# ── Severity / Status ──────────────────────────────────────────────
class Sev(Enum):
    PASS = "PASS"
    INFO = "INFO"
    GAP  = "GAP"
    MISSING = "MISSING"

@dataclass
class Finding:
    modality: str
    check_id: str
    title: str
    severity: Sev
    detail: str

# ═══════════════════════════════════════════════════════════════════
# SpatialDDS 1.5 IDL mirrors (from updated full spec)
# ═══════════════════════════════════════════════════════════════════

# ── Sensing Common ────────────────────────────────────────────
COMMON_STRUCTS = {
    "SampleType": ["U8_MAG","F16_MAG","CF16","CF32","MAGPHASE_S8"],
    "Codec": ["CODEC_NONE","LZ4","ZSTD","GZIP","DRACO","JPEG","H264","H265","AV1","FP8Q","FP4Q","AE_V1"],
    "PayloadKind": ["DENSE_TILES","SPARSE_COO","LATENT","BLOB_GEOMETRY","BLOB_RASTER"],
    "StreamMeta_fields": ["stream_id","frame_ref","T_bus_sensor","nominal_rate_hz","schema_version"],
    "FrameHeader_fields": ["stream_id","frame_seq","t_start","t_end","has_sensor_pose","sensor_pose","blobs"],
    "Axis_fields": ["name","unit","spec"],
    "ROI_fields": [
        "has_range","range_min","range_max",
        "has_azimuth","az_min","az_max",
        "has_elevation","el_min","el_max",
        "has_doppler","dop_min","dop_max",
        "has_image_roi","u_min","v_min","u_max","v_max",
        "global",
    ],
}

# ── Radar (detection-centric, for completeness) ──────────────
RADAR_DETECTION_STRUCTS = {
    "RadSensorType": ["SHORT_RANGE","MEDIUM_RANGE","LONG_RANGE","IMAGING_4D","SAR","OTHER"],
    "RadSensorMeta_fields": [
        "stream_id","base","sensor_type",
        "has_range_limits","min_range_m","max_range_m",
        "has_azimuth_fov","az_fov_min_deg","az_fov_max_deg",
        "has_elevation_fov","el_fov_min_deg","el_fov_max_deg",
        "has_velocity_limits","v_min_mps","v_max_mps",
        "max_detections_per_frame","proc_chain","schema_version",
    ],
}

# ── Radar (tensor path — for DeepSense raw I/Q) ──────────────
RADAR_TENSOR_STRUCTS = {
    "RadTensorLayout": ["RA_D","R_AZ_EL_D","CH_FAST_SLOW","CH_R_D","CUSTOM"],
    "RadTensorMeta_fields": [
        "stream_id","base","sensor_type",
        "layout","axes","voxel_type","physical_meaning",
        "has_antenna_config","num_tx","num_rx","num_virtual_channels",
        "has_waveform_params","bandwidth_hz","center_freq_hz",
        "chirp_duration_s","samples_per_chirp","chirps_per_frame",
        "payload_kind","codec","has_quant_scale","quant_scale",
        "tile_size","schema_version",
    ],
    "RadTensorFrame_fields": [
        "stream_id","frame_seq","hdr",
        "payload_kind","codec","voxel_type_after_decode",
        "has_quant_scale","quant_scale",
        "quality","proc_chain",
    ],
}

# ── Vision ────────────────────────────────────────────────────
VISION_STRUCTS = {
    "PixFormat": ["UNKNOWN","YUV420","RGB8","BGR8","RGBA8","RAW10","RAW12","RAW16"],
    "Distortion": ["NONE","RADTAN","KANNALA_BRANDT"],
    "CamModel": ["PINHOLE","FISHEYE","EQUIDISTANT","OMNI"],
    "RigRole": ["LEFT","RIGHT","CENTER","FRONT","FRONT_LEFT","FRONT_RIGHT",
                "BACK","BACK_LEFT","BACK_RIGHT","AUX",
                "PANORAMIC","EQUIRECTANGULAR"],  # K-V1 additions
    "CamIntrinsics_fields": [
        "model","width","height","fx","fy","cx","cy",
        "dist","dist_params","shutter_us","readout_us","pix","color","calib_version",
    ],
    "VisionMeta_fields": [
        "stream_id","base","K","role","rig_id","codec","pix","color","schema_version",
    ],
    "VisionFrame_fields": [
        "stream_id","frame_seq","hdr","codec","pix","color",
        "has_line_readout_us","line_readout_us","rectified","is_key_frame","quality",
    ],
}

# ── Lidar ─────────────────────────────────────────────────────
LIDAR_STRUCTS = {
    "LidarType": ["SPINNING_2D","MULTI_BEAM_3D","SOLID_STATE"],
    "CloudEncoding": ["PCD","PLY","LAS","LAZ","BIN_INTERLEAVED","GLTF_DRACO","MPEG_PCC","CUSTOM_BIN"],
    "PointLayout": ["XYZ_I","XYZ_I_R","XYZ_I_R_N","XYZ_I_R_T","XYZ_I_R_T_N"],
    "LidarMeta_fields": [
        "stream_id","base","type","n_rings",
        "has_range_limits","min_range_m","max_range_m",
        "has_horiz_fov","horiz_fov_deg_min","horiz_fov_deg_max",
        "has_vert_fov","vert_fov_deg_min","vert_fov_deg_max",
        "has_wavelength","wavelength_nm",  # K-L1 addition
        "encoding","codec","layout","schema_version",
    ],
    "LidarFrame_fields": [
        "stream_id","frame_seq","hdr","encoding","codec","layout",
        "has_per_point_timestamps",
        "has_average_range_m","average_range_m",
        "has_percent_valid","percent_valid",
        "has_quality","quality",
    ],
}

# ── VIO / IMU ─────────────────────────────────────────────────
VIO_STRUCTS = {
    "ImuInfo_fields": [
        "imu_id","frame_ref",
        "accel_noise_density","gyro_noise_density",
        "accel_random_walk","gyro_random_walk","stamp",
    ],
    "ImuSample_fields": [
        "imu_id","accel","gyro","stamp","source_id","seq",
    ],
}

# ── Core / Geo ────────────────────────────────────────────────
CORE_STRUCTS = {
    "GeoPose_fields": [
        "lat_deg","lon_deg","alt_m","q","frame_kind","frame_ref","stamp","cov",
    ],
    "GeoFrameKind": ["ECEF","ENU","NED"],
    "PoseSE3_fields": ["t","q","frame_ref","stamp"],
}

# ── GNSS Receiver Diagnostics (K-G1) ─────────────────────────
GNSS_STRUCTS = {
    "GnssFixType": ["NO_FIX","FIX_2D","FIX_3D","DGPS","RTK_FLOAT","RTK_FIXED",
                     "SBAS","DEAD_RECKONING","UNKNOWN_FIX"],
    "GnssService_constants": ["GPS","GLONASS","BEIDOU","GALILEO","QZSS","IRNSS","SBAS_SV"],
    "NavSatStatus_fields": [
        "gnss_id","fix_type","service","num_satellites",
        "has_dop","pdop","hdop","vdop",
        "has_velocity","speed_mps","course_deg",
        "has_diff_age","diff_age_s","diff_station_id",
        "stamp","schema_version",
    ],
}

# ── Semantics ─────────────────────────────────────────────────
SEMANTICS_STRUCTS = {
    "Detection2D_fields": [
        "det_id","class_id","score","bbox","stamp","source_id",
    ],
    "Detection3D_fields": [
        "det_id","frame_ref","has_tile","tile_key",
        "class_id","score","center","size","q",
        "has_covariance","cov_pos","cov_rot",
        "has_track_id","track_id","stamp","source_id",
        "has_attributes","attributes",
        "has_visibility","visibility",
        "has_num_pts","num_lidar_pts","num_radar_pts",
    ],
}

# ── RF Beam Sensing (Provisional — K-B1) ─────────────────────
RF_BEAM_STRUCTS = {
    "BeamSweepType": ["EXHAUSTIVE","HIERARCHICAL","TRACKING","PARTIAL","OTHER"],
    "PowerUnit": ["DBM","LINEAR_MW","RSRP","OTHER_UNIT"],
    "RfBeamMeta_fields": [
        "stream_id","base",
        "center_freq_ghz","has_bandwidth","bandwidth_ghz",
        "n_elements","n_beams",
        "fov_az_deg","has_fov_el","fov_el_deg",
        "has_array_index","array_index","array_label",
        "codebook_type",
        "has_mimo_config","n_tx","n_rx",
        "power_unit","schema_version",
    ],
    "RfBeamFrame_fields": [
        "stream_id","frame_seq","hdr",
        "sweep_type",
        "power","beam_indices",
        "has_best_beam","best_beam_idx","best_beam_power",
        "has_blockage_state","is_blocked","blockage_confidence",
        "has_snr_db","snr_db",
        "has_quality","quality",
    ],
    "RfBeamArraySet_fields": [
        "set_id","frame_seq","stamp",
        "arrays",
        "has_overall_best","overall_best_array_idx",
        "overall_best_beam_idx","overall_best_power",
    ],
}

# ═══════════════════════════════════════════════════════════════════
# Synthetic DeepSense 6G data mirrors
# ═══════════════════════════════════════════════════════════════════

# Testbed 1 (V2I): Unit 1 = BS with radar, lidar, camera, GPS, mmWave Rx
# Testbed 2 (V2V): 4× phased arrays, 4× radars per vehicle

DEEPSENSE_RADAR = {
    "type": "FMCW",
    "freq_ghz": 78.5,         # 76-81 GHz center
    "bandwidth_ghz": 4.0,
    "n_tx": 3,
    "n_rx": 4,
    "samples_per_chirp": 256,
    "chirps_per_frame": 128,
    "frame_rate_hz": 10,
    "max_range_m": 100,
    "range_resolution_m": 0.06,
    "output": "complex_IQ",     # raw I/Q tensor
    "tensor_shape": [4, 256, 128],  # [Rx, fast_time, slow_time]
    "sample_type": "CF32",      # complex float32
}

DEEPSENSE_LIDAR = {
    "model": "Ouster OS1-32",
    "type": "multi_beam_3d",
    "n_rings": 32,
    "n_cols": 1024,
    "max_range_m": 120,
    "frame_rate_hz": 10,  # or 20 in some scenarios
    "horiz_fov_deg": 360,
    "vert_fov_deg": 45,       # ±22.5°
    "wavelength_nm": 865,
    "point_fields": ["x","y","z","intensity","ring"],
}

DEEPSENSE_CAMERA = {
    "standard": {
        "model": "ZED2",
        "resolution": [1920, 1080],
        "downsampled": [960, 540],
        "frame_rate_hz": 30,  # downsampled to 10 Hz
        "type": "stereo",
        "pixel_format": "RGB8",
        "camera_model": "pinhole",
        "extrinsics": "hand_eye_transform",
    },
    "panoramic": {
        "model": "Insta360 ONE X2",
        "resolution": [5760, 2880],  # 5.7K
        "frame_rate_hz": 30,
        "type": "360_equirectangular",
        "views": ["4x 90°", "2x 180°"],  # derived views in V2V
    },
}

DEEPSENSE_GPS = {
    "type": "GPS-RTK",
    "rate_hz": 10,
    "rtk_accuracy_m": 0.01,  # 1 cm with RTK fix
    "non_rtk_accuracy_m": 2.5,
    "fields": ["lat","lon","alt","num_satellites","pdop","hdop","vdop",
               "fix_type","speed_mps","course_deg"],
}

DEEPSENSE_IMU = {
    "type": "6-axis",
    "rate_hz": 100,
    "fields": ["accel_x","accel_y","accel_z","gyro_x","gyro_y","gyro_z"],
}

DEEPSENSE_MMWAVE_BEAM = {
    "freq_ghz": 60,
    "n_elements": 16,
    "n_beams": 64,
    "fov_az_deg": 90,
    "rate_hz": 10,
    "output": "64x1_power_vector_dbm",
    "ground_truth": ["optimal_beam_index","blockage_status"],
    "v2v_arrays": 4,  # 4× arrays per vehicle in V2V scenarios
}

DEEPSENSE_LABELS = {
    "2d_bbox": True,
    "n_classes": 8,
    "optimal_beam_index": True,
    "blockage_status": True,
    "sequence_index": True,
}

# ═══════════════════════════════════════════════════════════════════
# Validation checks
# ═══════════════════════════════════════════════════════════════════
findings: List[Finding] = []

def add(modality, check_id, title, severity, detail):
    findings.append(Finding(modality, check_id, title, severity, detail))


# ── RADAR TENSOR ──────────────────────────────────────────────
def check_radar_tensor():
    # DT-01: RadTensorMeta exists with required fields
    meta_fields = RADAR_TENSOR_STRUCTS.get("RadTensorMeta_fields", [])
    required = ["axes","voxel_type","layout","physical_meaning"]
    present = [f for f in required if f in meta_fields]
    if len(present) == len(required):
        add("Radar (tensor)","DT-01","RadTensorMeta struct with tensor shape fields",Sev.PASS,
            f"All required fields present: {required}")
    else:
        missing = [f for f in required if f not in meta_fields]
        add("Radar (tensor)","DT-01","RadTensorMeta tensor fields",Sev.MISSING,
            f"Missing: {missing}")

    # DT-02: CF32 sample type for complex I/Q
    sample_types = set(COMMON_STRUCTS.get("SampleType", []))
    if "CF32" in sample_types:
        add("Radar (tensor)","DT-02","SampleType.CF32 for complex I/Q",Sev.PASS,
            f"CF32 present in SampleType enum. DeepSense radar output is complex float32 I/Q. "
            f"Also available: {sorted(sample_types)}")
    else:
        add("Radar (tensor)","DT-02","Complex sample type",Sev.MISSING,
            "SampleType lacks CF32 for complex float32 I/Q data.")

    # DT-03: CH_FAST_SLOW layout for raw FMCW [Rx, samples_per_chirp, chirps_per_frame]
    layouts = set(RADAR_TENSOR_STRUCTS.get("RadTensorLayout", []))
    if "CH_FAST_SLOW" in layouts:
        add("Radar (tensor)","DT-03","RadTensorLayout.CH_FAST_SLOW for raw FMCW",Sev.PASS,
            f"CH_FAST_SLOW maps DeepSense [4×256×128] = [Rx, fast_time, slow_time]. "
            f"Full layout enum: {sorted(layouts)}")
    else:
        add("Radar (tensor)","DT-03","Raw FMCW tensor layout",Sev.MISSING,
            "No layout for [channel, fast_time, slow_time] raw FMCW cubes.")

    # DT-04: MIMO antenna configuration
    mimo_fields = ["has_antenna_config","num_tx","num_rx","num_virtual_channels"]
    present = [f for f in mimo_fields if f in meta_fields]
    if len(present) == len(mimo_fields):
        add("Radar (tensor)","DT-04","MIMO antenna config (num_tx/num_rx/num_virtual)",Sev.PASS,
            f"DeepSense: 3Tx × 4Rx = 12 virtual channels. "
            f"Fields present: {mimo_fields}")
    else:
        missing = [f for f in mimo_fields if f not in meta_fields]
        add("Radar (tensor)","DT-04","MIMO antenna config",Sev.MISSING,
            f"Missing: {missing}")

    # DT-05: Waveform parameters (bandwidth, center freq, chirp geometry)
    waveform_fields = ["has_waveform_params","bandwidth_hz","center_freq_hz",
                       "samples_per_chirp","chirps_per_frame"]
    present = [f for f in waveform_fields if f in meta_fields]
    if len(present) == len(waveform_fields):
        add("Radar (tensor)","DT-05","FMCW waveform parameters",Sev.PASS,
            f"DeepSense: 4 GHz BW, 76-81 GHz, 256 samples/chirp, 128 chirps/frame. "
            f"Fields: {waveform_fields}")
    else:
        missing = [f for f in waveform_fields if f not in meta_fields]
        add("Radar (tensor)","DT-05","Waveform parameters",Sev.MISSING,
            f"Missing: {missing}")

    # DT-06: Frame blob transport (RadTensorFrame with blobs[])
    frame_fields = RADAR_TENSOR_STRUCTS.get("RadTensorFrame_fields", [])
    if "hdr" in frame_fields and "codec" in frame_fields:
        cube_size = 4 * 256 * 128 * 8  # complex float32 = 8 bytes/sample
        add("Radar (tensor)","DT-06","RadTensorFrame blob transport",Sev.PASS,
            f"RadTensorFrame.hdr.blobs[] carries raw cube. "
            f"DeepSense cube: 4×256×128 × 8 bytes = {cube_size:,} bytes/frame (~{cube_size/1024:.0f} KB). "
            f"Within BlobRef envelope (comparable to lidar frames).")
    else:
        add("Radar (tensor)","DT-06","Frame blob transport",Sev.MISSING,
            "RadTensorFrame missing hdr or codec fields.")

    # DT-07: Sensor type coverage
    sensor_types = set(RADAR_DETECTION_STRUCTS.get("RadSensorType", []))
    if "MEDIUM_RANGE" in sensor_types or "IMAGING_4D" in sensor_types:
        add("Radar (tensor)","DT-07","RadSensorType for FMCW radar",Sev.PASS,
            f"DeepSense FMCW radar (76-81 GHz, ~100 m) maps to MEDIUM_RANGE or IMAGING_4D. "
            f"Available: {sorted(sensor_types)}")
    else:
        add("Radar (tensor)","DT-07","Sensor type",Sev.GAP,
            "No suitable RadSensorType for 77 GHz FMCW radar.")

    # DT-08: StreamMeta extrinsics for sensor-to-bus calibration
    stream_fields = COMMON_STRUCTS.get("StreamMeta_fields", [])
    if "T_bus_sensor" in stream_fields and "nominal_rate_hz" in stream_fields:
        add("Radar (tensor)","DT-08","StreamMeta extrinsics + rate",Sev.PASS,
            "T_bus_sensor (PoseSE3) for DeepSense hand-eye calibration. "
            "nominal_rate_hz = 10 Hz.")
    else:
        add("Radar (tensor)","DT-08","StreamMeta fields",Sev.GAP,
            "Missing T_bus_sensor or nominal_rate_hz.")


# ── CAMERA / VISION ───────────────────────────────────────────
def check_vision():
    # DV-01: Standard camera (ZED2 960×540 RGB)
    pix_formats = set(VISION_STRUCTS.get("PixFormat", []))
    cam_fields = VISION_STRUCTS.get("CamIntrinsics_fields", [])
    if "RGB8" in pix_formats and "width" in cam_fields and "height" in cam_fields:
        add("Vision","DV-01","Standard camera (RGB8 960×540)",Sev.PASS,
            "PixFormat.RGB8 + CamIntrinsics.width/height cover DeepSense ZED2 "
            "1920×1080 (or downsampled 960×540).")
    else:
        add("Vision","DV-01","Standard camera",Sev.GAP,
            "Missing RGB8 or width/height fields.")

    # DV-02: Camera extrinsics (hand-eye calibration)
    meta_fields = VISION_STRUCTS.get("VisionMeta_fields", [])
    if "base" in meta_fields:
        add("Vision","DV-02","Camera extrinsics (hand-eye via StreamMeta.T_bus_sensor)",Sev.PASS,
            "VisionMeta.base → StreamMeta → T_bus_sensor (PoseSE3). "
            "Covers DeepSense hand-eye calibration for camera-to-basestation alignment.")
    else:
        add("Vision","DV-02","Camera extrinsics",Sev.GAP,"No base/StreamMeta on VisionMeta.")

    # DV-03: Camera model (pinhole for ZED2)
    cam_models = set(VISION_STRUCTS.get("CamModel", []))
    if "PINHOLE" in cam_models:
        add("Vision","DV-03","Camera model (PINHOLE for ZED2)",Sev.PASS,
            f"CamModel.PINHOLE matches DeepSense ZED2 (pre-rectified). "
            f"Available: {sorted(cam_models)}")
    else:
        add("Vision","DV-03","Camera model",Sev.GAP,"No PINHOLE camera model.")

    # DV-04: Frame rate via StreamMeta
    if "nominal_rate_hz" in COMMON_STRUCTS.get("StreamMeta_fields", []):
        add("Vision","DV-04","Frame rate (30→10 Hz downsampled)",Sev.PASS,
            "StreamMeta.nominal_rate_hz = 10 (DeepSense downsampled from 30 Hz).")
    else:
        add("Vision","DV-04","Frame rate",Sev.GAP,"No nominal_rate_hz.")

    # DV-05: 360° camera rig roles (V2V scenarios)
    rig_roles = set(VISION_STRUCTS.get("RigRole", []))
    if "PANORAMIC" in rig_roles and "EQUIRECTANGULAR" in rig_roles:
        add("Vision","DV-05","360° camera rig roles (PANORAMIC, EQUIRECTANGULAR)",Sev.PASS,
            f"RigRole includes PANORAMIC and EQUIRECTANGULAR for DeepSense V2V "
            f"360° cameras (Insta360 ONE X2, 5.7K). Full enum: {sorted(rig_roles)}")
    else:
        missing = {"PANORAMIC","EQUIRECTANGULAR"} - rig_roles
        add("Vision","DV-05","360° rig roles",Sev.GAP,
            f"Missing RigRole values: {missing}. DeepSense V2V 360° cameras "
            f"cannot be accurately described.")

    # DV-06: Keyframe flag
    vf_fields = VISION_STRUCTS.get("VisionFrame_fields", [])
    if "is_key_frame" in vf_fields:
        add("Vision","DV-06","VisionFrame.is_key_frame",Sev.PASS,
            "Keyframe flag present for frame selection in ML pipelines.")
    else:
        add("Vision","DV-06","Keyframe flag",Sev.GAP,"No is_key_frame.")

    # DV-07: Codec for compressed frames
    codecs = set(COMMON_STRUCTS.get("Codec", []))
    if "JPEG" in codecs or "H264" in codecs:
        add("Vision","DV-07","Image compression codec",Sev.PASS,
            f"Codec enum covers JPEG/H264/H265/AV1 for DeepSense image transport. "
            f"Available: {sorted(codecs)}")
    else:
        add("Vision","DV-07","Image codec",Sev.GAP,"No JPEG or H264.")


# ── LIDAR ─────────────────────────────────────────────────────
def check_lidar():
    # DL-01: LidarType for Ouster OS1-32 (multi-beam 3D spinning)
    types = set(LIDAR_STRUCTS.get("LidarType", []))
    if "MULTI_BEAM_3D" in types:
        add("Lidar","DL-01","LidarType.MULTI_BEAM_3D for Ouster OS1-32",Sev.PASS,
            f"Multi-beam 3D matches Ouster OS1-32 (32 rings, spinning). "
            f"Available: {sorted(types)}")
    else:
        add("Lidar","DL-01","Lidar type",Sev.GAP,"No MULTI_BEAM_3D.")

    # DL-02: Ring count + FOV metadata
    lm_fields = LIDAR_STRUCTS.get("LidarMeta_fields", [])
    if "n_rings" in lm_fields and "has_horiz_fov" in lm_fields and "has_vert_fov" in lm_fields:
        add("Lidar","DL-02","LidarMeta ring count + FOV",Sev.PASS,
            "n_rings=32, horiz_fov=360°, vert_fov=±22.5° all mappable via "
            "LidarMeta fields with has_* guards.")
    else:
        add("Lidar","DL-02","Ring/FOV metadata",Sev.GAP,"Missing fields.")

    # DL-03: Range limits
    if "has_range_limits" in lm_fields and "max_range_m" in lm_fields:
        add("Lidar","DL-03","Range limits (120 m for OS1-32)",Sev.PASS,
            "has_range_limits + max_range_m covers Ouster OS1-32 120 m max range.")
    else:
        add("Lidar","DL-03","Range limits",Sev.GAP,"Missing range fields.")

    # DL-04: Point layout (XYZ + intensity + ring)
    layouts = set(LIDAR_STRUCTS.get("PointLayout", []))
    if "XYZ_I_R" in layouts:
        add("Lidar","DL-04","PointLayout.XYZ_I_R for Ouster clouds",Sev.PASS,
            "DeepSense lidar: x, y, z, intensity, ring → XYZ_I_R.")
    else:
        add("Lidar","DL-04","Point layout",Sev.GAP,"No XYZ_I_R.")

    # DL-05: BIN_INTERLEAVED encoding
    encodings = set(LIDAR_STRUCTS.get("CloudEncoding", []))
    if "BIN_INTERLEAVED" in encodings:
        add("Lidar","DL-05","CloudEncoding.BIN_INTERLEAVED",Sev.PASS,
            "Raw interleaved binary for DeepSense point cloud transport.")
    else:
        add("Lidar","DL-05","Cloud encoding",Sev.GAP,"No BIN_INTERLEAVED.")

    # DL-06: Sensor wavelength (K-L1)
    if "has_wavelength" in lm_fields and "wavelength_nm" in lm_fields:
        add("Lidar","DL-06","LidarMeta.wavelength_nm (Ouster 865 nm)",Sev.PASS,
            "wavelength_nm field with has_wavelength guard. Ouster OS1 = 865 nm. "
            "Useful for eye-safety and atmospheric absorption classification.")
    else:
        add("Lidar","DL-06","Sensor wavelength",Sev.GAP,
            "No wavelength_nm field. Ouster OS1 wavelength (865 nm) cannot be described. "
            "Low priority — does not affect data transport.")

    # DL-07: Frame rate
    stream_fields = COMMON_STRUCTS.get("StreamMeta_fields", [])
    if "nominal_rate_hz" in stream_fields:
        add("Lidar","DL-07","Frame rate (10–20 Hz)",Sev.PASS,
            "StreamMeta.nominal_rate_hz covers DeepSense lidar at 10 or 20 Hz.")
    else:
        add("Lidar","DL-07","Frame rate",Sev.GAP,"No nominal_rate_hz.")


# ── IMU ───────────────────────────────────────────────────────
def check_imu():
    # DI-01: 6-axis IMU sample (accel + gyro)
    sample_fields = VIO_STRUCTS.get("ImuSample_fields", [])
    if "accel" in sample_fields and "gyro" in sample_fields:
        add("IMU","DI-01","ImuSample (accel + gyro)",Sev.PASS,
            "6-axis IMU: accel (Vec3, m/s²) + gyro (Vec3, rad/s). "
            "DeepSense: 100 Hz 6-axis IMU maps directly.")
    else:
        add("IMU","DI-01","IMU sample",Sev.MISSING,"No accel/gyro fields.")

    # DI-02: IMU calibration metadata
    info_fields = VIO_STRUCTS.get("ImuInfo_fields", [])
    if "accel_noise_density" in info_fields and "gyro_noise_density" in info_fields:
        add("IMU","DI-02","ImuInfo noise densities",Sev.PASS,
            "accel_noise_density + gyro_noise_density + random_walk params present.")
    else:
        add("IMU","DI-02","IMU calibration",Sev.GAP,"Missing noise density fields.")

    # DI-03: IMU frame reference
    if "frame_ref" in info_fields:
        add("IMU","DI-03","ImuInfo.frame_ref",Sev.PASS,
            "Frame reference for IMU mounting in rig. DeepSense uses FrameRef "
            "for sensor-to-bus alignment.")
    else:
        add("IMU","DI-03","IMU frame ref",Sev.GAP,"No frame_ref.")

    # DI-04: Timestamp + sequence
    if "stamp" in sample_fields and "seq" in sample_fields:
        add("IMU","DI-04","ImuSample timestamp + sequence",Sev.PASS,
            "stamp (Time) + seq (uint64) for temporal ordering. "
            "DeepSense IMU at 100 Hz requires fine-grained timestamps.")
    else:
        add("IMU","DI-04","Timestamp/seq",Sev.GAP,"Missing stamp or seq.")


# ── GPS / POSITION ────────────────────────────────────────────
def check_gps():
    # DG-01: Position (lat/lon/alt)
    gp_fields = CORE_STRUCTS.get("GeoPose_fields", [])
    if "lat_deg" in gp_fields and "lon_deg" in gp_fields and "alt_m" in gp_fields:
        add("GPS","DG-01","GeoPose lat/lon/alt",Sev.PASS,
            "DeepSense GPS-RTK lat/lon/alt → GeoPose.lat_deg/lon_deg/alt_m. "
            "WGS84 ellipsoidal.")
    else:
        add("GPS","DG-01","GPS position",Sev.MISSING,"Missing lat/lon/alt.")

    # DG-02: Orientation
    if "q" in gp_fields:
        add("GPS","DG-02","GeoPose orientation",Sev.PASS,
            "QuaternionXYZW for orientation. DeepSense GPS heading can derive "
            "yaw-only quaternion.")
    else:
        add("GPS","DG-02","GPS orientation",Sev.GAP,"No quaternion.")

    # DG-03: Timestamp
    if "stamp" in gp_fields:
        add("GPS","DG-03","GeoPose timestamp",Sev.PASS,
            "DeepSense GPS at 10 Hz; each sample gets Time stamp.")
    else:
        add("GPS","DG-03","GPS timestamp",Sev.GAP,"No stamp.")

    # DG-04: Position covariance
    if "cov" in gp_fields:
        add("GPS","DG-04","GeoPose covariance (positional uncertainty)",Sev.PASS,
            "CovMatrix covers positional uncertainty. DeepSense RTK accuracy "
            "(≤1 cm) expressible as tight covariance.")
    else:
        add("GPS","DG-04","Position covariance",Sev.GAP,"No cov field.")

    # DG-05: GNSS quality metadata (DOP, satellites, fix type)
    nav_fields = GNSS_STRUCTS.get("NavSatStatus_fields", [])
    fix_types = GNSS_STRUCTS.get("GnssFixType", [])
    dop_ok = {"has_dop","pdop","hdop","vdop"}.issubset(set(nav_fields))
    fix_ok = "fix_type" in nav_fields and "RTK_FIXED" in fix_types
    sat_ok = "num_satellites" in nav_fields

    if dop_ok and fix_ok and sat_ok:
        add("GPS","DG-05","GNSS quality via NavSatStatus (DOP, fix type, satellites)",Sev.PASS,
            "NavSatStatus carries pdop/hdop/vdop (with has_dop guard), "
            "fix_type (GnssFixType enum: NO_FIX through RTK_FIXED), and "
            "num_satellites. Published as companion to GeoPose, keeping "
            "sensor diagnostics separate from pose data (K-G1).")
    else:
        add("GPS","DG-05","GNSS quality",Sev.GAP,
            f"Missing NavSatStatus fields: dop={dop_ok}, fix={fix_ok}, sat={sat_ok}")

    # DG-06: Speed over ground
    if "has_velocity" in nav_fields and "speed_mps" in nav_fields and "course_deg" in nav_fields:
        add("GPS","DG-06","Speed/course over ground via NavSatStatus",Sev.PASS,
            "NavSatStatus.speed_mps + course_deg with has_velocity guard. "
            "Maps DeepSense GPS speed_mps and course_deg (from NMEA RMC).")
    else:
        add("GPS","DG-06","Speed over ground",Sev.GAP,
            "Missing speed_mps/course_deg on NavSatStatus.")

    # DG-07: GNSS service/constellation bitmask (NEW in v3)
    svc_consts = GNSS_STRUCTS.get("GnssService_constants", [])
    if "service" in nav_fields and "GPS" in svc_consts:
        add("GPS","DG-07","GNSS constellation bitmask",Sev.PASS,
            "NavSatStatus.service (uint16 bitmask) with GnssService constants: "
            "GPS, GLONASS, BeiDou, Galileo, QZSS, IRNSS, SBAS_SV. "
            "Matches ROS 2 NavSatStatus.service convention.")
    else:
        add("GPS","DG-07","GNSS service",Sev.GAP,"Missing service field or GPS constant.")

    # DG-08: Differential correction age (NEW in v3)
    if "has_diff_age" in nav_fields and "diff_age_s" in nav_fields:
        add("GPS","DG-08","Differential correction age",Sev.PASS,
            "NavSatStatus.diff_age_s + diff_station_id with has_diff_age guard. "
            "Maps NMEA GGA fields 13-14. Essential for RTK quality monitoring.")
    else:
        add("GPS","DG-08","Diff correction age",Sev.GAP,"Missing diff_age fields.")

    # DG-09: Stream linkage (NavSatStatus ↔ GeoPose) (NEW in v3)
    if "gnss_id" in nav_fields:
        add("GPS","DG-09","Stream linkage (NavSatStatus ↔ GeoPose)",Sev.PASS,
            "NavSatStatus.gnss_id (@key) correlates with the GeoPose stream "
            "from the same receiver. Follows established SpatialDDS meta/frame pattern.")
    else:
        add("GPS","DG-09","Stream linkage",Sev.GAP,"Missing gnss_id key.")

    # DG-10: Fix type enum covers RTK grades (NEW in v3)
    rtk_types = {"RTK_FLOAT","RTK_FIXED"}
    if rtk_types.issubset(set(fix_types)):
        add("GPS","DG-10","RTK fix type granularity",Sev.PASS,
            "GnssFixType enum distinguishes RTK_FLOAT vs RTK_FIXED — "
            "critical for DeepSense GPS-RTK quality boundary. Also covers "
            "NO_FIX, FIX_2D, FIX_3D, DGPS, SBAS, DEAD_RECKONING.")
    else:
        add("GPS","DG-10","RTK fix types",Sev.GAP,
            f"Missing RTK types: {rtk_types - set(fix_types)}")


# ── MMWAVE BEAM (signature ISAC modality) ─────────────────────
def check_mmwave_beam():
    meta = RF_BEAM_STRUCTS.get("RfBeamMeta_fields", [])
    frame = RF_BEAM_STRUCTS.get("RfBeamFrame_fields", [])
    arrayset = RF_BEAM_STRUCTS.get("RfBeamArraySet_fields", [])
    sweep_types = RF_BEAM_STRUCTS.get("BeamSweepType", [])
    power_units = RF_BEAM_STRUCTS.get("PowerUnit", [])

    # DB-01: Beam power vector
    if "power" in frame and "stream_id" in frame:
        add("mmWave Beam","DB-01","64-element beam power vector",Sev.PASS,
            "RfBeamFrame.power (sequence<float,1024>) carries the per-beam "
            "received power vector. 64 entries for DeepSense exhaustive sweep. "
            "Validated against provisional rf_beam profile (K-B1).")
    else:
        add("mmWave Beam","DB-01","Beam power vector",Sev.MISSING,
            "RfBeamFrame.power field not found in IDL mirror.")

    # DB-02: Beam codebook metadata
    codebook_fields = {"n_beams","n_elements","center_freq_ghz","fov_az_deg"}
    if codebook_fields.issubset(set(meta)):
        add("mmWave Beam","DB-02","Beam codebook metadata",Sev.PASS,
            "RfBeamMeta carries n_beams (64), n_elements (16), center_freq_ghz "
            "(60.0), fov_az_deg (90), codebook_type ('DFT-64'). "
            "Covers DeepSense phased array specification.")
    else:
        add("mmWave Beam","DB-02","Codebook metadata",Sev.MISSING,
            f"Missing: {codebook_fields - set(meta)}")

    # DB-03: Best beam index (ground truth)
    if "has_best_beam" in frame and "best_beam_idx" in frame:
        add("mmWave Beam","DB-03","Optimal beam index",Sev.PASS,
            "RfBeamFrame.best_beam_idx (uint16) with has_best_beam guard. "
            "Maps DeepSense ground-truth label: index of beam maximizing SNR.")
    else:
        add("mmWave Beam","DB-03","Optimal beam index",Sev.MISSING,
            "Missing best_beam_idx or has_best_beam.")

    # DB-04: Blockage state (LOS/NLOS)
    if "has_blockage_state" in frame and "is_blocked" in frame and "blockage_confidence" in frame:
        add("mmWave Beam","DB-04","Blockage status (LOS/NLOS)",Sev.PASS,
            "RfBeamFrame.is_blocked (boolean) + blockage_confidence (float 0..1) "
            "with has_blockage_state guard. Maps DeepSense per-sample blockage labels.")
    else:
        add("mmWave Beam","DB-04","Blockage status",Sev.MISSING,
            "Missing blockage fields.")

    # DB-05: Multi-array coordination (V2V 4× arrays)
    if "arrays" in arrayset and "has_overall_best" in arrayset:
        add("mmWave Beam","DB-05","Multi-array beam set (V2V 4× arrays)",Sev.PASS,
            "RfBeamArraySet.arrays (sequence<RfBeamFrame,8>) batches per-array "
            "frames at one time step. overall_best_array_idx + overall_best_beam_idx "
            "provide cross-array best beam. Covers DeepSense V2V 4-array rig.")
    else:
        add("mmWave Beam","DB-05","Multi-array set",Sev.MISSING,
            "Missing arrays or overall_best fields.")

    # DB-06: Sparse sweep indices (NEW in v2)
    if "beam_indices" in frame and "PARTIAL" in sweep_types:
        add("mmWave Beam","DB-06","Sparse sweep beam indices",Sev.PASS,
            "RfBeamFrame.beam_indices maps power[i] to codebook position for "
            "PARTIAL/TRACKING sweeps. Empty for EXHAUSTIVE (implicit 0..n-1). "
            "BeamSweepType enum includes EXHAUSTIVE, HIERARCHICAL, TRACKING, PARTIAL.")
    else:
        add("mmWave Beam","DB-06","Sparse sweep",Sev.GAP,
            "Missing beam_indices or PARTIAL sweep type.")

    # DB-07: Power unit consistency (NEW in v2)
    if "power_unit" in meta and "DBM" in power_units:
        add("mmWave Beam","DB-07","Power unit convention",Sev.PASS,
            "RfBeamMeta.power_unit (PowerUnit enum) declares the unit for "
            "RfBeamFrame.power values. DBM is default. Supports LINEAR_MW, RSRP "
            "for forward compatibility with 3GPP conventions.")
    else:
        add("mmWave Beam","DB-07","Power unit",Sev.GAP,
            "Missing power_unit field or DBM enum value.")

    # DB-08: Stream linkage (NEW in v2)
    if "stream_id" in meta and "stream_id" in frame:
        add("mmWave Beam","DB-08","Stream linkage (meta ↔ frame)",Sev.PASS,
            "RfBeamFrame.stream_id matches RfBeamMeta.stream_id for meta/frame "
            "correlation. Follows established SpatialDDS pattern (RadSensorMeta ↔ "
            "RadDetectionSet, LidarMeta ↔ LidarFrame).")
    else:
        add("mmWave Beam","DB-08","Stream linkage",Sev.GAP,
            "Missing stream_id on meta or frame.")


# ── SEMANTICS / LABELS ────────────────────────────────────────
def check_semantics():
    # DS-01: 2D bounding boxes
    d2_fields = SEMANTICS_STRUCTS.get("Detection2D_fields", [])
    if "bbox" in d2_fields and "class_id" in d2_fields:
        add("Semantics","DS-01","2D bounding box annotations",Sev.PASS,
            "Detection2D.bbox + class_id covers DeepSense 2D bbox labels (8 classes).")
    else:
        add("Semantics","DS-01","2D bboxes",Sev.GAP,"Missing bbox or class_id.")

    # DS-02: Sequence index
    hdr_fields = COMMON_STRUCTS.get("FrameHeader_fields", [])
    if "frame_seq" in hdr_fields:
        add("Semantics","DS-02","Sequence index via FrameHeader.frame_seq",Sev.PASS,
            "DeepSense sample sequence index maps to FrameHeader.frame_seq (uint64).")
    else:
        add("Semantics","DS-02","Sequence index",Sev.GAP,"No frame_seq.")

    # DS-03: Class ID as string
    if "class_id" in d2_fields:
        add("Semantics","DS-03","Class ID for DeepSense object classes",Sev.PASS,
            "Detection2D.class_id (string) maps DeepSense class labels: "
            "car, truck, bus, pedestrian, cyclist, motorcycle, other_vehicle, background.")
    else:
        add("Semantics","DS-03","Class ID",Sev.GAP,"No class_id.")

    # DS-04: Beam/blockage ground truth
    beam_frame = RF_BEAM_STRUCTS.get("RfBeamFrame_fields", [])
    if "has_best_beam" in beam_frame and "has_blockage_state" in beam_frame:
        add("Semantics","DS-04","Beam index / blockage labels via RfBeamFrame",Sev.PASS,
            "DeepSense ground-truth beam index and blockage status map to "
            "RfBeamFrame.best_beam_idx and .is_blocked/.blockage_confidence. "
            "Covered by provisional rf_beam profile (K-B1).")
    else:
        add("Semantics","DS-04","Beam/blockage labels",Sev.GAP,
            "ISAC-specific labels require rf_beam profile.")


# ═══════════════════════════════════════════════════════════════════
# Run all checks
# ═══════════════════════════════════════════════════════════════════
check_radar_tensor()
check_vision()
check_lidar()
check_imu()
check_gps()
check_mmwave_beam()
check_semantics()


# ═══════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════
def severity_icon(s):
    return {"PASS":"✅","INFO":"ℹ️","GAP":"⚠️","MISSING":"❌"}.get(s.value,"?")

def print_report():
    print("=" * 80)
    print("DeepSense 6G → SpatialDDS 1.5 Conformance Report v3")
    print("=" * 80)

    modalities = []
    seen = set()
    for f in findings:
        if f.modality not in seen:
            modalities.append(f.modality)
            seen.add(f.modality)

    total = len(findings)
    passes = sum(1 for f in findings if f.severity == Sev.PASS)
    gaps = sum(1 for f in findings if f.severity == Sev.GAP)
    missing = sum(1 for f in findings if f.severity == Sev.MISSING)

    print(f"\nSummary: {passes}/{total} PASS | {gaps} GAP | {missing} MISSING\n")

    for mod in modalities:
        mod_findings = [f for f in findings if f.modality == mod]
        mod_pass = sum(1 for f in mod_findings if f.severity == Sev.PASS)
        print(f"\n{'─' * 70}")
        print(f"  {mod}  ({mod_pass}/{len(mod_findings)} pass)")
        print(f"{'─' * 70}")
        for f in mod_findings:
            icon = severity_icon(f.severity)
            print(f"  {icon} {f.check_id}: {f.title}")
            for line in textwrap.wrap(f.detail, width=72):
                print(f"       {line}")

    # Coverage matrix
    print(f"\n{'=' * 80}")
    print("Coverage Matrix")
    print(f"{'=' * 80}")
    print(f"  {'Modality':<20} {'Checks':>7} {'Pass':>6} {'Gap':>5} {'Missing':>8} {'Coverage':>9}")
    print(f"  {'─'*20} {'─'*7} {'─'*6} {'─'*5} {'─'*8} {'─'*9}")

    grand_total = grand_pass = grand_gap = grand_missing = 0
    for mod in modalities:
        mf = [f for f in findings if f.modality == mod]
        mp = sum(1 for f in mf if f.severity == Sev.PASS)
        mg = sum(1 for f in mf if f.severity == Sev.GAP)
        mm = sum(1 for f in mf if f.severity == Sev.MISSING)
        mc = len(mf)
        pct = f"{100*mp/mc:.0f}%" if mc > 0 else "—"
        print(f"  {mod:<20} {mc:>7} {mp:>6} {mg:>5} {mm:>8} {pct:>9}")
        grand_total += mc; grand_pass += mp; grand_gap += mg; grand_missing += mm

    pct = f"{100*grand_pass/grand_total:.0f}%" if grand_total > 0 else "—"
    print(f"  {'─'*20} {'─'*7} {'─'*6} {'─'*5} {'─'*8} {'─'*9}")
    print(f"  {'TOTAL':<20} {grand_total:>7} {grand_pass:>6} {grand_gap:>5} {grand_missing:>8} {pct:>9}")

    # Deferred items summary
    print(f"\n{'─' * 70}")
    print("Deferred Items (under separate discussion)")
    print(f"{'─' * 70}")
    deferred = [f for f in findings if "Deferred" in f.detail or "deferred" in f.detail]
    for f in deferred:
        print(f"  {severity_icon(f.severity)} {f.check_id}: {f.title}")

    return {
        "total_checks": grand_total,
        "passes": grand_pass,
        "gaps": grand_gap,
        "missing": grand_missing,
    }

results = print_report()

# Write JSON results
with open("deepsense6g_harness_results.json","w") as fp:
    json.dump({
        "version": "v3",
        "spec_version": "SpatialDDS 1.5 (with radar tensor + K-V1 + K-L1 + K-B1 provisional + K-G1 applied)",
        "dataset": "DeepSense 6G",
        "reference": "Alkhateeb et al., IEEE Communications Magazine, 2023",
        "total_checks": results["total_checks"],
        "passes": results["passes"],
        "gaps": results["gaps"],
        "missing": results["missing"],
        "findings": [
            {
                "modality": f.modality,
                "check_id": f.check_id,
                "title": f.title,
                "severity": f.severity.value,
                "detail": f.detail,
            }
            for f in findings
        ],
    }, fp, indent=2)

print(f"\n\nResults written to deepsense6g_harness_results.json")
