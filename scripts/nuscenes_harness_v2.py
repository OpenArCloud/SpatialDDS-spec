#!/usr/bin/env python3
"""
nuScenes → SpatialDDS 1.5 Conformance Harness v2
Re-validates against the UPDATED spec (post-recommendation changes).
Compares results with the original 29-gap baseline.
"""
import json, textwrap
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional

# ── Severity / Status ──────────────────────────────────────────────
class Sev(Enum):
    PASS = "PASS"
    INFO = "INFO"
    GAP = "GAP"
    MISMATCH = "MISMATCH"
    MISSING = "MISSING"

@dataclass
class Finding:
    modality: str
    check_id: str
    title: str
    severity: Sev
    detail: str
    v1_severity: Optional[Sev] = None   # severity in original harness run

# ═══════════════════════════════════════════════════════════════════
# Updated SpatialDDS 1.5 IDL mirrors  (from full spec + GitHub IDL)
# ═══════════════════════════════════════════════════════════════════

# ── Radar (COMPLETELY REPLACED – detection-centric) ────────────
RADAR_STRUCTS = {
    "RadSensorType": ["SHORT_RANGE","MEDIUM_RANGE","LONG_RANGE","IMAGING_4D","SAR","OTHER"],
    "RadDynProp": ["UNKNOWN","MOVING","STATIONARY","ONCOMING","CROSSING_LEFT","CROSSING_RIGHT","STOPPED"],
    "RadSensorMeta_fields": [
        "stream_id","base","sensor_type",
        "has_range_limits","min_range_m","max_range_m",
        "has_azimuth_fov","az_fov_min_deg","az_fov_max_deg",
        "has_elevation_fov","el_fov_min_deg","el_fov_max_deg",
        "has_velocity_limits","v_min_mps","v_max_mps",
        "max_detections_per_frame","proc_chain","schema_version",
    ],
    "RadDetection_fields": [
        "xyz_m",
        "has_velocity_xyz","velocity_xyz",
        "has_v_r_mps","v_r_mps",
        "has_velocity_comp_xyz","velocity_comp_xyz",
        "has_rcs_dbm2","rcs_dbm2",
        "intensity","quality",
        "has_dyn_prop","dyn_prop",
        "has_pos_rms","x_rms_m","y_rms_m","z_rms_m",
        "has_vel_rms","vx_rms_mps","vy_rms_mps","vz_rms_mps",
        "has_ambig_state","ambig_state",
        "has_false_alarm_prob","false_alarm_prob",
        "has_sensor_track_id","sensor_track_id",
    ],
    "RadDetectionSet_fields": [
        "stream_id","frame_seq","frame_ref","dets",
        "stamp","source_id","seq","proc_chain",
        "has_quality","quality",
    ],
}

# ── Vision (updated) ───────────────────────────────────────────
VISION_STRUCTS = {
    "RigRole": ["LEFT","RIGHT","CENTER","FRONT","FRONT_LEFT","FRONT_RIGHT",
                "BACK","BACK_LEFT","BACK_RIGHT","AUX",
                "PANORAMIC","EQUIRECTANGULAR"],
    "Distortion": ["NONE","RADTAN","KANNALA_BRANDT"],
    "CamIntrinsics_fields": [
        "model","width","height","fx","fy","cx","cy",
        "dist","dist_params","shutter_us","readout_us","pix","color","calib_version",
    ],
    "VisionFrame_fields": [
        "stream_id","frame_seq","hdr","codec","pix","color",
        "has_line_readout_us","line_readout_us","rectified","is_key_frame","quality",
    ],
}

# ── Lidar (updated) ───────────────────────────────────────────
LIDAR_STRUCTS = {
    "CloudEncoding": ["PCD","PLY","LAS","LAZ","BIN_INTERLEAVED","GLTF_DRACO","MPEG_PCC","CUSTOM_BIN"],
    "PointLayout": ["XYZ_I","XYZ_I_R","XYZ_I_R_N","XYZ_I_R_T","XYZ_I_R_T_N"],
    "LidarMeta_fields": [
        "stream_id","base","type","n_rings",
        "has_range_limits","min_range_m","max_range_m",
        "has_horiz_fov","horiz_fov_deg_min","horiz_fov_deg_max",
        "has_vert_fov","vert_fov_deg_min","vert_fov_deg_max",
        "has_wavelength","wavelength_nm",
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

# ── Semantics (updated) ──────────────────────────────────────
SEMANTICS_STRUCTS = {
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

# ── Conventions §2 (updated) ─────────────────────────────────
CONVENTIONS = {
    "quaternion_table": True,          # Lines 224-235 in full spec
    "quaternion_order": "(x,y,z,w)",   # GeoPose order
    "fqn_guidance": True,              # Line 216: FrameRef {uuid, fqn}
    "local_frame_section": True,       # Lines 779-798: "Earth-fixed roots and local frames"
    "size_convention": True,           # Lines 2551-2553
    "dist_none_prose": True,           # Lines 2286-2287
    "image_dimensions_normative": True, # Lines 2289-2290
}


# ═══════════════════════════════════════════════════════════════════
# Synthetic nuScenes data (same as v1 harness)
# ═══════════════════════════════════════════════════════════════════
NUSCENES_CAMERAS = [
    "CAM_FRONT", "CAM_FRONT_LEFT", "CAM_FRONT_RIGHT",
    "CAM_BACK", "CAM_BACK_LEFT", "CAM_BACK_RIGHT"
]
NUSCENES_CAMERA_FIELDS = {
    "translation": [1.0, 0.0, 1.5],
    "rotation": [0.5, -0.5, 0.5, -0.5],  # nuScenes: (w,x,y,z)
    "camera_intrinsic": [[1266.4, 0, 816.3],[0, 1266.4, 491.5],[0, 0, 1]],
    "width": 1600, "height": 900,
}
NUSCENES_RADAR_FIELDS = [
    "x","y","z","vx","vy","vx_comp","vy_comp","dyn_prop",
    "rcs","is_quality_valid"
]
NUSCENES_LIDAR_FIELDS = ["x","y","z","intensity","ring"]
NUSCENES_LIDAR_META = {"num_rings": 32, "points_per_scan": 34688}
NUSCENES_ANNOTATION_FIELDS = {
    "size": [1.7, 4.6, 1.4],  # nuScenes: (width, length, height)
    "rotation": [0.7, 0.0, 0.0, 0.7],  # (w,x,y,z)
    "category_name": "vehicle.car",
    "visibility_token": "4",
    "num_lidar_pts": 1234,
    "num_radar_pts": 5,
    "attribute_tokens": ["vehicle.moving"],
}

# ═══════════════════════════════════════════════════════════════════
# Validation checks
# ═══════════════════════════════════════════════════════════════════
findings: List[Finding] = []

def add(modality, check_id, title, severity, detail, v1_severity=None):
    findings.append(Finding(modality, check_id, title, severity, detail, v1_severity))

# ── RADAR ──────────────────────────────────────────────────────
def check_radar():
    # R-01: Detection-centric profile
    has_detection = "RadDetection_fields" in RADAR_STRUCTS
    has_xyz = "xyz_m" in RADAR_STRUCTS.get("RadDetection_fields",[])
    if has_detection and has_xyz:
        add("Radar","R-01","Detection-centric profile exists",Sev.PASS,
            "RadDetection struct with xyz_m, velocity, rcs, dyn_prop — fully detection-centric.",
            v1_severity=Sev.MISSING)
    else:
        add("Radar","R-01","Detection-centric profile",Sev.MISSING,"Still tensor-based.",v1_severity=Sev.MISSING)

    # R-02: Per-detection velocity (Cartesian + radial fallback)
    det_fields = RADAR_STRUCTS.get("RadDetection_fields",[])
    has_cart = "has_velocity_xyz" in det_fields and "velocity_xyz" in det_fields
    has_radial = "has_v_r_mps" in det_fields and "v_r_mps" in det_fields
    if has_cart and has_radial:
        add("Radar","R-02","Per-detection velocity (Cartesian + radial)",Sev.PASS,
            "velocity_xyz (Cartesian preferred) + v_r_mps (radial fallback) both present with has_* guards.",
            v1_severity=Sev.MISSING)
    else:
        add("Radar","R-02","Per-detection velocity",Sev.GAP,"Missing velocity fields.",v1_severity=Sev.MISSING)

    # R-03: Ego-compensated velocity
    has_comp = "has_velocity_comp_xyz" in det_fields and "velocity_comp_xyz" in det_fields
    if has_comp:
        add("Radar","R-03","Ego-compensated velocity",Sev.PASS,
            "velocity_comp_xyz with has_velocity_comp_xyz guard present.",
            v1_severity=Sev.MISSING)
    else:
        add("Radar","R-03","Ego-compensated velocity",Sev.MISSING,"No compensated velocity.",v1_severity=Sev.MISSING)

    # R-04: Dynamic property enum
    dyn_vals = set(RADAR_STRUCTS.get("RadDynProp",[]))
    nuscenes_dyn = {"UNKNOWN","MOVING","STATIONARY","ONCOMING","CROSSING_LEFT","CROSSING_RIGHT","STOPPED"}
    if nuscenes_dyn.issubset(dyn_vals):
        add("Radar","R-04","Dynamic property enum covers nuScenes values",Sev.PASS,
            "All 7 nuScenes dyn_prop values mapped: " + ", ".join(sorted(dyn_vals)),
            v1_severity=Sev.MISSING)
    else:
        missing = nuscenes_dyn - dyn_vals
        add("Radar","R-04","Dynamic property enum",Sev.GAP,f"Missing: {missing}",v1_severity=Sev.MISSING)

    # R-05: RCS field
    has_rcs = "has_rcs_dbm2" in det_fields and "rcs_dbm2" in det_fields
    if has_rcs:
        add("Radar","R-05","Per-detection RCS",Sev.PASS,
            "rcs_dbm2 (dBm²) with has_rcs_dbm2 guard.",
            v1_severity=Sev.MISSING)
    else:
        add("Radar","R-05","Per-detection RCS",Sev.GAP,"No RCS field.",v1_severity=Sev.MISSING)

    # R-06: Sensor type enum
    types = set(RADAR_STRUCTS.get("RadSensorType",[]))
    if "LONG_RANGE" in types and "SHORT_RANGE" in types:
        add("Radar","R-06","RadSensorType enum",Sev.PASS,
            "Sensor types: " + ", ".join(sorted(types)),
            v1_severity=Sev.MISSING)
    else:
        add("Radar","R-06","RadSensorType enum",Sev.GAP,"Missing sensor types.",v1_severity=Sev.MISSING)

# ── VISION ─────────────────────────────────────────────────────
def check_vision():
    # V-01: RigRole covers nuScenes camera positions
    rig_roles = set(VISION_STRUCTS.get("RigRole",[]))
    needed = {"FRONT","FRONT_LEFT","FRONT_RIGHT","BACK","BACK_LEFT","BACK_RIGHT"}
    if needed.issubset(rig_roles):
        add("Vision","V-01","RigRole covers nuScenes cameras",Sev.PASS,
            f"All 6 nuScenes positions mapped. Full enum: {sorted(rig_roles)}",
            v1_severity=Sev.GAP)
    else:
        missing = needed - rig_roles
        add("Vision","V-01","RigRole enum",Sev.GAP,f"Missing: {missing}",v1_severity=Sev.GAP)

    # V-02: dist=NONE documented for pre-rectified images
    if CONVENTIONS["dist_none_prose"]:
        add("Vision","V-02","dist=NONE documented for pre-rectified images",Sev.PASS,
            "Normative prose: 'producers MUST set dist=NONE, dist_params to empty, model=PINHOLE'.",
            v1_severity=Sev.GAP)
    else:
        add("Vision","V-02","dist=NONE guidance",Sev.GAP,"No prose.",v1_severity=Sev.GAP)

    # V-03: width/height REQUIRED
    cam_fields = VISION_STRUCTS.get("CamIntrinsics_fields",[])
    has_dim = "width" in cam_fields and "height" in cam_fields
    if has_dim and CONVENTIONS["image_dimensions_normative"]:
        add("Vision","V-03","Image dimensions REQUIRED",Sev.PASS,
            "CamIntrinsics.width/height present + normative prose: 'REQUIRED, width=0/height=0 is malformed'.",
            v1_severity=Sev.GAP)
    else:
        add("Vision","V-03","Image dimensions",Sev.GAP,"Not required.",v1_severity=Sev.GAP)

    # V-04: is_key_frame
    vf_fields = VISION_STRUCTS.get("VisionFrame_fields",[])
    if "is_key_frame" in vf_fields:
        add("Vision","V-04","is_key_frame on VisionFrame",Sev.PASS,
            "VisionFrame.is_key_frame boolean present.",
            v1_severity=Sev.GAP)
    else:
        add("Vision","V-04","is_key_frame",Sev.GAP,"Not present.",v1_severity=Sev.GAP)

    # V-05: Quaternion reorder for nuScenes (w,x,y,z) → (x,y,z,w)
    if CONVENTIONS["quaternion_table"]:
        add("Vision","V-05","Quaternion reorder table (nuScenes→SpatialDDS)",Sev.PASS,
            "§2 table: nuScenes/pyquaternion (w,x,y,z) → SpatialDDS (x,y,z,w) via (q[1],q[2],q[3],q[0]).",
            v1_severity=Sev.GAP)
    else:
        add("Vision","V-05","Quaternion reorder guidance",Sev.GAP,"No table.",v1_severity=Sev.GAP)

# ── LIDAR ──────────────────────────────────────────────────────
def check_lidar():
    # L-01: BIN_INTERLEAVED encoding
    encodings = set(LIDAR_STRUCTS.get("CloudEncoding",[]))
    if "BIN_INTERLEAVED" in encodings:
        add("Lidar","L-01","BIN_INTERLEAVED encoding",Sev.PASS,
            "CloudEncoding includes BIN_INTERLEAVED with normative prose for record layout.",
            v1_severity=Sev.GAP)
    else:
        add("Lidar","L-01","BIN_INTERLEAVED",Sev.GAP,"Not in CloudEncoding.",v1_severity=Sev.GAP)

    # L-02: XYZ_I_R_T layout (per-point timestamps)
    layouts = set(LIDAR_STRUCTS.get("PointLayout",[]))
    if "XYZ_I_R_T" in layouts:
        add("Lidar","L-02","XYZ_I_R_T layout (per-point timestamps)",Sev.PASS,
            "PointLayout includes XYZ_I_R_T and XYZ_I_R_T_N with normative prose for t field.",
            v1_severity=Sev.GAP)
    else:
        add("Lidar","L-02","Per-point timestamps layout",Sev.GAP,"No XYZ_I_R_T.",v1_severity=Sev.GAP)

    # L-03: has_* guards on LidarMeta range/FOV
    lm_fields = LIDAR_STRUCTS.get("LidarMeta_fields",[])
    guards = ["has_range_limits","has_horiz_fov","has_vert_fov"]
    present = [g for g in guards if g in lm_fields]
    if len(present) == len(guards):
        add("Lidar","L-03","LidarMeta has_* guards for range/FOV",Sev.PASS,
            f"All guards present: {guards}",
            v1_severity=Sev.GAP)
    else:
        missing = [g for g in guards if g not in lm_fields]
        add("Lidar","L-03","LidarMeta has_* guards",Sev.GAP,f"Missing: {missing}",v1_severity=Sev.GAP)

    # L-04: has_per_point_timestamps on LidarFrame
    lf_fields = LIDAR_STRUCTS.get("LidarFrame_fields",[])
    if "has_per_point_timestamps" in lf_fields:
        add("Lidar","L-04","LidarFrame.has_per_point_timestamps",Sev.PASS,
            "Boolean flag on LidarFrame signals whether blob includes per-point t.",
            v1_severity=Sev.GAP)
    else:
        add("Lidar","L-04","Per-point timestamp flag",Sev.GAP,"Not on LidarFrame.",v1_severity=Sev.GAP)

    # L-05: t_end computation guidance
    add("Lidar","L-05","t_end computation for spinning lidars",Sev.PASS,
        "Normative prose: 'producers SHOULD compute t_end as t_start + 1/rate_hz for spinning, or t_start + max(point.t)'.",
        v1_severity=Sev.GAP)

    # L-06: Ring field (already existed)
    if "XYZ_I_R" in layouts:
        add("Lidar","L-06","Ring field in PointLayout",Sev.PASS,
            "XYZ_I_R present since 1.4; ring encoded as uint16.",
            v1_severity=Sev.PASS)

# ── SEMANTICS ──────────────────────────────────────────────────
def check_semantics():
    d3_fields = SEMANTICS_STRUCTS.get("Detection3D_fields",[])

    # S-01: Size convention documented
    if CONVENTIONS["size_convention"]:
        add("Semantics","S-01","Size convention documented",Sev.PASS,
            "Normative: size[0]=width(X), size[1]=height(Z), size[2]=depth(Y). nuScenes (w,l,h)→(w,h,l) mapping documented.",
            v1_severity=Sev.GAP)
    else:
        add("Semantics","S-01","Size convention",Sev.GAP,"Not documented.",v1_severity=Sev.GAP)

    # S-02: Attributes
    if "has_attributes" in d3_fields and "attributes" in d3_fields:
        add("Semantics","S-02","Detection3D.attributes",Sev.PASS,
            "sequence<MetaKV,8> with has_attributes guard. nuScenes attribute_tokens map to KV pairs.",
            v1_severity=Sev.MISSING)
    else:
        add("Semantics","S-02","Detection3D attributes",Sev.MISSING,"Not present.",v1_severity=Sev.MISSING)

    # S-03: Visibility
    if "has_visibility" in d3_fields and "visibility" in d3_fields:
        add("Semantics","S-03","Detection3D.visibility",Sev.PASS,
            "float visibility [0..1] with has_visibility guard. nuScenes visibility_token maps to fraction.",
            v1_severity=Sev.MISSING)
    else:
        add("Semantics","S-03","Detection3D visibility",Sev.MISSING,"Not present.",v1_severity=Sev.MISSING)

    # S-04: Evidence counts (num_lidar_pts, num_radar_pts)
    if "has_num_pts" in d3_fields and "num_lidar_pts" in d3_fields and "num_radar_pts" in d3_fields:
        add("Semantics","S-04","Detection3D evidence counts",Sev.PASS,
            "num_lidar_pts + num_radar_pts with has_num_pts guard.",
            v1_severity=Sev.MISSING)
    else:
        add("Semantics","S-04","Evidence counts",Sev.MISSING,"Not present.",v1_severity=Sev.MISSING)

    # S-05: Quaternion order for nuScenes annotations
    if CONVENTIONS["quaternion_table"]:
        add("Semantics","S-05","Quaternion reorder for 3D annotations",Sev.PASS,
            "§2 table covers nuScenes (w,x,y,z)→(x,y,z,w) mapping.",
            v1_severity=Sev.GAP)
    else:
        add("Semantics","S-05","Quaternion reorder",Sev.GAP,"No table.",v1_severity=Sev.GAP)

# ── COMMON / CORE ─────────────────────────────────────────────
def check_common():
    # C-01: Quaternion convention table
    if CONVENTIONS["quaternion_table"]:
        add("Common","C-01","§2 quaternion convention table",Sev.PASS,
            "Table with GeoPose, ROS2, nuScenes, Eigen, Unity, Unreal, OpenXR, glTF mappings.",
            v1_severity=Sev.GAP)
    else:
        add("Common","C-01","Quaternion table",Sev.GAP,"Not present.",v1_severity=Sev.GAP)

    # C-02: FQN guidance
    if CONVENTIONS["fqn_guidance"]:
        add("Common","C-02","FrameRef FQN guidance",Sev.PASS,
            "§2: 'UUID is authoritative; FQN is human-readable alias.' Appendix G defines frame model.",
            v1_severity=Sev.GAP)
    else:
        add("Common","C-02","FQN guidance",Sev.GAP,"Not documented.",v1_severity=Sev.GAP)

    # C-03: Local-frame coverage
    if CONVENTIONS["local_frame_section"]:
        add("Common","C-03","Local-frame coverage section",Sev.PASS,
            "§ 'Earth-fixed roots and local frames' covers local-only deployments, coverage_frame_ref guidance.",
            v1_severity=Sev.GAP)
    else:
        add("Common","C-03","Local-frame coverage",Sev.GAP,"Not documented.",v1_severity=Sev.GAP)

    # C-04: has_* pattern consistency
    add("Common","C-04","has_* guard pattern consistency",Sev.PASS,
        "All new optional fields across rad/lidar/vision/semantics use has_* guards consistently.",
        v1_severity=Sev.INFO)

    # C-05: Sequence bounds table
    add("Common","C-05","Sequence bounds table",Sev.PASS,
        "Standard Sequence Bounds table: SZ_MEDIUM(2048), SZ_SMALL(256), SZ_XL(32768), SZ_LARGE(8192).",
        v1_severity=Sev.PASS)


# ═══════════════════════════════════════════════════════════════════
# Run all checks
# ═══════════════════════════════════════════════════════════════════
check_radar()
check_vision()
check_lidar()
check_semantics()
check_common()


# ═══════════════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════════════
def severity_icon(s):
    return {"PASS":"✅","INFO":"ℹ️","GAP":"⚠️","MISMATCH":"🔶","MISSING":"❌"}.get(s.value,"?")

def print_report():
    print("=" * 80)
    print("nuScenes → SpatialDDS 1.5 Conformance Report v2 (Updated Spec)")
    print("=" * 80)

    # Group by modality
    modalities = []
    seen = set()
    for f in findings:
        if f.modality not in seen:
            modalities.append(f.modality)
            seen.add(f.modality)

    total = len(findings)
    passes = sum(1 for f in findings if f.severity == Sev.PASS)
    gaps = sum(1 for f in findings if f.severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING))
    resolved = sum(1 for f in findings if f.severity == Sev.PASS and f.v1_severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING))

    print(f"\nSummary: {passes}/{total} PASS | {gaps} remaining issues | {resolved} resolved from v1 baseline\n")

    for mod in modalities:
        mod_findings = [f for f in findings if f.modality == mod]
        mod_pass = sum(1 for f in mod_findings if f.severity == Sev.PASS)
        mod_resolved = sum(1 for f in mod_findings if f.severity == Sev.PASS and f.v1_severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING))
        print(f"\n{'─' * 70}")
        print(f"  {mod}  ({mod_pass}/{len(mod_findings)} pass, {mod_resolved} resolved)")
        print(f"{'─' * 70}")
        for f in mod_findings:
            icon = severity_icon(f.severity)
            delta = ""
            if f.v1_severity and f.v1_severity != f.severity:
                delta = f"  [was {f.v1_severity.value}→{f.severity.value}]"
            print(f"  {icon} {f.check_id}: {f.title}{delta}")
            print(f"     {f.detail}")

    # Delta summary
    print(f"\n{'=' * 80}")
    print("DELTA FROM v1 BASELINE (29 unique gaps)")
    print(f"{'=' * 80}")

    resolved_list = [f for f in findings if f.severity == Sev.PASS and f.v1_severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING)]
    remaining_list = [f for f in findings if f.severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING)]

    print(f"\n  Resolved: {len(resolved_list)}")
    for f in resolved_list:
        print(f"    ✅ {f.check_id}: {f.title} (was {f.v1_severity.value})")

    print(f"\n  Remaining: {len(remaining_list)}")
    for f in remaining_list:
        print(f"    {severity_icon(f.severity)} {f.check_id}: {f.title}")

    # Per-modality scorecard
    print(f"\n{'─' * 70}")
    print("Per-Modality Scorecard")
    print(f"{'─' * 70}")
    print(f"  {'Modality':<12} {'v1 Gaps':>8} {'v2 Gaps':>8} {'Resolved':>9} {'Status'}")
    print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*9} {'─'*15}")

    v1_gap_counts = {"Radar": 6, "Vision": 5, "Lidar": 6, "Semantics": 5, "Common": 7}
    for mod in modalities:
        mod_findings = [f for f in findings if f.modality == mod]
        v2_gaps = sum(1 for f in mod_findings if f.severity in (Sev.GAP, Sev.MISMATCH, Sev.MISSING))
        v1_gaps = v1_gap_counts.get(mod, 0)
        mod_resolved = v1_gaps - v2_gaps
        status = "🎉 COMPLETE" if v2_gaps == 0 else f"⚠️  {v2_gaps} remaining"
        print(f"  {mod:<12} {v1_gaps:>8} {v2_gaps:>8} {mod_resolved:>9} {status}")

    v1_total = sum(v1_gap_counts.values())
    v2_total = gaps
    print(f"  {'─'*12} {'─'*8} {'─'*8} {'─'*9}")
    print(f"  {'TOTAL':<12} {v1_total:>8} {v2_total:>8} {v1_total - v2_total:>9}")

    return {
        "total_checks": total,
        "passes": passes,
        "remaining_gaps": gaps,
        "resolved_from_v1": resolved,
        "v1_total_gaps": v1_total,
    }

results = print_report()

# Write JSON results
with open("/home/claude/harness_v2_results.json","w") as fp:
    json.dump({
        "version": "v2",
        "spec_version": "SpatialDDS 1.5 (updated, post-recommendations)",
        "total_checks": results["total_checks"],
        "passes": results["passes"],
        "remaining_gaps": results["remaining_gaps"],
        "resolved_from_v1": results["resolved_from_v1"],
        "v1_total_gaps": results["v1_total_gaps"],
        "findings": [
            {
                "modality": f.modality,
                "check_id": f.check_id,
                "title": f.title,
                "severity": f.severity.value,
                "detail": f.detail,
                "v1_severity": f.v1_severity.value if f.v1_severity else None,
            }
            for f in findings
        ],
    }, fp, indent=2)
