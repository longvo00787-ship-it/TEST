"""
Posture classification - phân loại tư thế từ features 1 frame.
Postures: standing, sitting, lying, falling, unknown
"""
from typing import Dict, Any, Tuple
import numpy as np

# Thresholds (chuẩn hóa)
RATIO_STANDING = 0.75   # w/h < 0.75 thường là đứng
RATIO_LYING = 1.3       # w/h > 1.3 thường là nằm
ANGLE_VERTICAL = 35.0   # body angle < 35 -> gần thẳng đứng
ANGLE_HORIZONTAL = 65.0  # body angle > 65 -> gần nằm ngang
HIP_Y_TOP = 0.5         # hip_rel_y < 0.5: hips gần top (standing/sitting)


def classify_posture(features: Dict[str, float]) -> Tuple[str, float]:
    """
    Trả về (posture, confidence).
    Không dựa vào 1 điều kiện duy nhất - combine ratio + body angle + hip relative Y.
    """
    ratio = features.get("bbox_ratio", 1.0)
    body_angle = features.get("body_angle", 90.0)
    torso_angle = features.get("torso_angle", 90.0)
    hip_rel_y = features.get("hip_rel_y", 0.5)
    has_pose = features.get("has_pose", 0.0) > 0.5

    # Nếu không có pose, fallback dựa vào bbox ratio
    if not has_pose:
        if ratio < RATIO_STANDING:
            return ("standing", 0.55)
        if ratio > RATIO_LYING:
            return ("lying", 0.55)
        if 0.75 <= ratio <= 1.3:
            return ("sitting", 0.45)
        return ("unknown", 0.3)

    # Standing: body gần thẳng đứng, ratio < 0.75
    if body_angle < ANGLE_VERTICAL and ratio < RATIO_STANDING and torso_angle > 20:
        return ("standing", 0.9)

    # Lying: body gần nằm ngang, ratio > 1.3
    if body_angle > ANGLE_HORIZONTAL and ratio > RATIO_LYING:
        return ("lying", 0.9)

    # Sitting: torso angle lớn hơn standing một chút, hips thấp
    if 0.6 <= ratio <= 1.2 and torso_angle > 15:
        # Sitting: hip thấp (gần bottom), torso angle trung bình
        if hip_rel_y > 0.55:
            return ("sitting", 0.75)
        if body_angle < 50:
            return ("standing", 0.7)

    # Standing relaxed
    if body_angle < 50 and ratio < 0.9:
        return ("standing", 0.75)

    # Bending/Sitting
    if 35 <= body_angle <= 70:
        return ("sitting", 0.65)

    # Lying subtle
    if ratio > 1.05:
        return ("lying", 0.7)

    return ("unknown", 0.4)