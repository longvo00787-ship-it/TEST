"""
Pose feature extraction - tính các đặc trưng từ keypoints & bbox.
"""
import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from backend.utils.helpers import (
    bbox_center, bbox_size, bbox_ratio, angle_between, euclidean_distance
)


KP_INDEX = {
    "nose": 0, "left_eye": 1, "right_eye": 2, "left_ear": 3, "right_ear": 4,
    "left_shoulder": 5, "right_shoulder": 6, "left_elbow": 7, "right_elbow": 8,
    "left_wrist": 9, "right_wrist": 10, "left_hip": 11, "right_hip": 12,
    "left_knee": 13, "right_knee": 14, "left_ankle": 15, "right_ankle": 16,
}


def kp_by_name(keypoints: List[Dict[str, Any]], name: str) -> Optional[Tuple[float, float, float]]:
    for kp in keypoints:
        if kp["name"] == name:
            return (kp["x"], kp["y"], kp.get("conf", 1.0))
    return None


def midpoint(p1, p2):
    if p1 is None or p2 is None:
        return None
    return ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0, min(p1[2], p2[2]))


def extract_features(
    bbox: List[float],
    keypoints: Optional[List[Dict[str, Any]]] = None,
    prev_features: Optional[Dict[str, float]] = None,
    fps: float = 30.0,
) -> Dict[str, float]:
    """
    Trích xuất features từ bbox + keypoints cho 1 person tại 1 frame.
    Returns dict of features (chuẩn hóa kích thước).
    """
    feats: Dict[str, float] = {}

    x1, y1, x2, y2 = bbox
    cx, cy = bbox_center(bbox)
    w, h = bbox_size(bbox)
    ratio = bbox_ratio(bbox)  # w/h

    feats["bbox_w"] = float(w)
    feats["bbox_h"] = float(h)
    feats["bbox_ratio"] = float(ratio)
    feats["bbox_area"] = float(w * h)
    feats["center_x"] = float(cx)
    feats["center_y"] = float(cy)
    feats["top_y"] = float(y1)
    feats["bottom_y"] = float(y2)

    # Pose-based features
    feats["body_angle"] = 90.0  # default horizontal
    feats["torso_angle"] = 90.0
    feats["has_pose"] = 0.0

    if keypoints:
        ls = kp_by_name(keypoints, "left_shoulder")
        rs = kp_by_name(keypoints, "right_shoulder")
        lh = kp_by_name(keypoints, "left_hip")
        rh = kp_by_name(keypoints, "right_hip")
        nose = kp_by_name(keypoints, "nose")
        lk = kp_by_name(keypoints, "left_knee")
        rk = kp_by_name(keypoints, "right_knee")
        la = kp_by_name(keypoints, "left_ankle")
        ra = kp_by_name(keypoints, "right_ankle")

        shoulders = midpoint(ls, rs)
        hips = midpoint(lh, rh)
        knees = midpoint(lk, rk)
        ankles = midpoint(la, ra)

        if shoulders and hips:
            torso_angle = angle_between(hips[:2], shoulders[:2])
            feats["torso_angle"] = float(torso_angle)

        if nose and (lh or rh):
            hip_pt = lh or rh
            head_to_hip = angle_between(hip_pt[:2], nose[:2])
            feats["body_angle"] = float(head_to_hip)

        feats["has_pose"] = 1.0
        feats["shoulder_y"] = float(shoulders[1]) if shoulders else 0.0
        feats["hip_y"] = float(hips[1]) if hips else 0.0
        feats["knee_y"] = float(knees[1]) if knees else 0.0
        feats["ankle_y"] = float(ankles[1]) if ankles else 0.0

        # Hip height normalized to bbox height
        if hips and h > 0:
            feats["hip_rel_y"] = float((hips[1] - y1) / h)
        else:
            feats["hip_rel_y"] = 0.5

        # Torso length
        if shoulders and hips:
            torso_len = euclidean_distance(shoulders[:2], hips[:2])
            feats["torso_len"] = float(torso_len)
            feats["torso_len_norm"] = float(torso_len / max(h, 1.0))
        else:
            feats["torso_len"] = 0.0
            feats["torso_len_norm"] = 0.0

    # Displacement / velocity
    if prev_features:
        dt = 1.0 / max(fps, 1e-3)
        dy = feats["center_y"] - prev_features.get("center_y", feats["center_y"])
        dx = feats["center_x"] - prev_features.get("center_x", feats["center_x"])
        feats["vy"] = float(dy / dt)
        feats["vx"] = float(dx / dt)
        feats["speed"] = float(math.sqrt(dx * dx + dy * dy) / dt)

        # Acceleration
        prev_vy = prev_features.get("vy", 0.0)
        feats["ay"] = float((feats["vy"] - prev_vy) / dt)

        # Height change
        prev_h = prev_features.get("bbox_h", feats["bbox_h"])
        feats["dh"] = float(feats["bbox_h"] - prev_h)
        feats["dh_ratio"] = float(feats["dh"] / max(prev_h, 1.0))

        # Ratio change
        prev_ratio = prev_features.get("bbox_ratio", feats["bbox_ratio"])
        feats["dratio"] = float(feats["bbox_ratio"] - prev_ratio)
    else:
        feats["vy"] = 0.0
        feats["vx"] = 0.0
        feats["speed"] = 0.0
        feats["ay"] = 0.0
        feats["dh"] = 0.0
        feats["dh_ratio"] = 0.0
        feats["dratio"] = 0.0

    return feats