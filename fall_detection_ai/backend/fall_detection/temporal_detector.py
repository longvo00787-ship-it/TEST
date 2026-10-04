"""
Temporal Fall Detection - phân tích chuỗi frames để phát hiện té ngã.

KHÔNG dùng:
    if body_horizontal: fall = True

Thay vào đó phân tích:
- Posture transition trong temporal window (0.5-3s)
- Vertical displacement / downward velocity
- Body angle change
- Bounding box aspect ratio change
- Speed / acceleration
- Person remains on ground (lying > X frames sau transition)

Fallback người nằm nghỉ:
- Nếu posture = lying mà KHÔNG có transition (standing->lying nhanh) -> không alert.
"""
from collections import deque
from typing import Dict, Any, List, Optional, Tuple
import time
import numpy as np

from backend.config import (
    FALL_WINDOW_SECONDS, FALL_VERTICAL_DROP_RATIO, FALL_HORIZONTAL_RATIO,
    FALL_PROB_THRESHOLD, ALERT_CONFIRM_FRAMES
)
from backend.classification.posture import classify_posture


class PersonFallState:
    """State machine cho 1 person để phát hiện té ngã theo thời gian."""

    def __init__(self, person_id: int, fps: float = 30.0):
        self.person_id = person_id
        self.fps = fps
        self.history: deque = deque(maxlen=300)
        self.fall_score = 0.0
        self.last_posture = "unknown"
        self.last_fall_time = 0.0
        self.cooldown_until = 0.0  # không fire cùng event liên tục
        self.fall_confirm_frames = 0
        self.is_alerted = False
        self.fall_event_active = False
        self.fall_start_time: Optional[float] = None
        self.fall_detected_time: Optional[float] = None
        self.alert_latency: Optional[float] = None

    def reset_alert(self):
        self.is_alerted = False
        self.fall_event_active = False
        self.fall_start_time = None
        self.fall_detected_time = None
        self.alert_latency = None

    def push(self, features: Dict[str, float], posture: str, ts: float):
        self.history.append({
            "features": features,
            "posture": posture,
            "ts": ts,
        })
        self.last_posture = posture

    def analyze(self) -> Dict[str, Any]:
        """
        Phân tích lịch sử để quyết định fall.
        Trả về dict { fall_prob, posture, fall_event, alert_latency, ... }
        """
        if len(self.history) < 3:
            return {
                "person_id": self.person_id,
                "posture": self.last_posture,
                "fall_probability": 0.0,
                "fall_event": False,
                "alert_latency": None,
            }

        # Lấy cửa sổ thời gian gần nhất
        window_size = max(int(FALL_WINDOW_SECONDS * self.fps), 5)
        window = list(self.history)[-window_size:]

        # 1. Tính các tín hiệu
        postures = [h["posture"] for h in window]
        feats = [h["features"] for h in window]

        current_posture = window[-1]["posture"]
        current_feats = window[-1]["features"]

        # Speed / vy
        vys = [f.get("vy", 0.0) for f in feats]
        speeds = [f.get("speed", 0.0) for f in feats]
        ratios = [f.get("bbox_ratio", 1.0) for f in feats]
        body_angles = [f.get("body_angle", 90.0) for f in feats]
        bbox_hs = [f.get("bbox_h", 1.0) for f in feats]

        max_vy = max(vys) if vys else 0.0  # downward positive (image coords)
        max_speed = max(speeds) if speeds else 0.0
        max_ratio = max(ratios) if ratios else 1.0
        max_body_angle = max(body_angles) if body_angles else 90.0

        # 2. Vertical drop: bbox height giảm nhanh (người collapse xuống)
        h_first = bbox_hs[0]
        h_min = min(bbox_hs)
        height_drop_ratio = (h_first - h_min) / max(h_first, 1.0)

        # 3. Posture transition: từ standing/sitting -> lying
        had_vertical = any(p in ("standing", "sitting") for p in postures[:-2])
        is_horizontal_now = current_posture in ("lying",) or max_ratio > FALL_HORIZONTAL_RATIO

        # 4. Body angle transition
        angle_change = max_body_angle - min(body_angles)

        # 5. Fall probability combining signals
        fall_prob = 0.0

        # Strong signal: rapid vertical drop + horizontal posture
        if height_drop_ratio > FALL_VERTICAL_DROP_RATIO:
            fall_prob += 0.35
        if max_vy > 50:  # px/s downward
            fall_prob += 0.15
        if max_speed > 100:
            fall_prob += 0.10
        if is_horizontal_now:
            fall_prob += 0.25
        if had_vertical and current_posture in ("lying", "falling"):
            fall_prob += 0.20
        if angle_change > 40:
            fall_prob += 0.10

        # Cap 1
        fall_prob = min(fall_prob, 1.0)

        # 6. False positive reduction
        # Nếu posture = lying từ đầu window mà không có transition -> không fall
        all_lying = all(p == "lying" for p in postures)
        all_sitting = all(p in ("sitting", "lying") for p in postures)
        all_standing = all(p == "standing" for p in postures)
        low_movement = max_speed < 30 and abs(max_vy) < 20

        if all_lying and low_movement:
            # Người nằm nghỉ liên tục -> giảm score
            fall_prob *= 0.1
        if all_sitting and low_movement and current_posture in ("sitting", "lying"):
            fall_prob *= 0.2
        if all_standing and current_posture == "standing":
            fall_prob = 0.0

        # 7. Nếu confidence yếu -> giảm score
        if current_feats.get("has_pose", 0.0) < 0.5 and fall_prob < 0.6:
            fall_prob *= 0.7

        # 8. Confirm frames: cần nhiều frames liên tiếp có fall_prob cao
        now = window[-1]["ts"]
        if fall_prob >= FALL_PROB_THRESHOLD:
            self.fall_confirm_frames += 1
            if self.fall_start_time is None:
                self.fall_start_time = now
        else:
            # Nếu posture trở lại vertical thì reset
            if current_posture in ("standing",):
                self.fall_confirm_frames = 0
                self.fall_start_time = None
            self.fall_confirm_frames = max(0, self.fall_confirm_frames - 1)

        # 9. Confirm event
        fall_event = False
        alert_latency = None
        if (self.fall_confirm_frames >= ALERT_CONFIRM_FRAMES
                and not self.is_alerted
                and now > self.cooldown_until):
            self.is_alerted = True
            self.fall_event_active = True
            self.fall_detected_time = now
            self.cooldown_until = now + 10.0  # tránh spam
            fall_event = True
            if self.fall_start_time:
                alert_latency = now - self.fall_start_time
            self.alert_latency = alert_latency

        self.fall_score = fall_prob

        return {
            "person_id": self.person_id,
            "posture": current_posture,
            "fall_probability": float(fall_prob),
            "fall_event": bool(fall_event),
            "alert_latency": float(alert_latency) if alert_latency is not None else None,
            "signals": {
                "height_drop_ratio": float(height_drop_ratio),
                "max_vy": float(max_vy),
                "max_speed": float(max_speed),
                "max_ratio": float(max_ratio),
                "angle_change": float(angle_change),
            }
        }


class TemporalFallDetector:
    """Quản lý PersonFallState cho nhiều người."""

    def __init__(self, fps: float = 30.0):
        self.fps = fps
        self.states: Dict[int, PersonFallState] = {}

    def update(self, person_id: int, features: Dict[str, float], ts: float) -> Dict[str, Any]:
        if person_id not in self.states:
            self.states[person_id] = PersonFallState(person_id, self.fps)
        state = self.states[person_id]
        posture, conf = classify_posture(features)
        state.push(features, posture, ts)
        result = state.analyze()
        result["posture_confidence"] = conf
        return result

    def reset(self):
        self.states.clear()

    def get_state(self, person_id: int) -> Optional[PersonFallState]:
        return self.states.get(person_id)

    def all_states(self) -> Dict[int, PersonFallState]:
        return dict(self.states)