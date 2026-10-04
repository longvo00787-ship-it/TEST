"""
Inference pipeline - tích hợp tất cả:
YOLO Detect -> Tracking -> Pose -> Feature -> Posture -> Temporal Fall Detection -> Alert
"""
import time
import threading
from collections import deque
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

from backend.config import get_device
from backend.detection.yolo_detector import YOLODetector
from backend.tracking.person_tracker import PersonTracker
from backend.pose.feature_extractor import extract_features
from backend.fall_detection.temporal_detector import TemporalFallDetector
from backend.fall_detection.ml_classifier import MLFallClassifier
from backend.classification.posture import classify_posture
from backend.utils.helpers import FPSCounter, Timer


class FallDetectionEngine:
    """Main pipeline."""

    def __init__(
        self,
        detect_weights: Optional[str] = None,
        pose_weights: Optional[str] = None,
        use_ml: bool = False,
        device: str = "auto",
    ):
        if device == "auto":
            device = get_device()

        self.device = device
        self.detector = YOLODetector(detect_weights, pose_weights, device=device)
        self.tracker = PersonTracker()
        self.temporal = TemporalFallDetector(fps=30.0)
        self.ml = MLFallClassifier() if use_ml else None

        self.fps_counter = FPSCounter(window=30)
        self.last_frame_ts: Optional[float] = None
        self.method = "yolo+rule_based" + ("+ml" if use_ml else "")

        # Per-person previous features (for delta)
        self.prev_features: Dict[int, Dict[str, float]] = {}

        # Stats
        self.total_detections = 0
        self.total_fall_events = 0
        self.false_alarm_count = 0
        self.latencies: deque = deque(maxlen=200)
        self.inference_times: deque = deque(maxlen=200)
        self.last_inference_ms: float = 0.0
        self.last_fps: float = 0.0

        # Reentrancy lock
        self._lock = threading.Lock()

    @property
    def model_loaded(self) -> bool:
        return self.detector.is_loaded

    @property
    def pose_loaded(self) -> bool:
        return self.detector.pose_loaded

    def reset(self):
        with self._lock:
            self.tracker.reset()
            self.temporal.reset()
            self.prev_features.clear()

    def process_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        Xử lý 1 frame, trả kết quả đầy đủ cho dashboard.
        """
        now = time.time()
        with Timer() as t:
            results = self._process_internal(frame, now)
        self.last_inference_ms = t.elapsed_ms
        self.inference_times.append(t.elapsed_ms)
        self.fps_counter.tick()
        self.last_fps = self.fps_counter.fps()
        return results

    def _process_internal(self, frame: np.ndarray, now: float) -> Dict[str, Any]:
        # 1. YOLO detect + tracking + pose
        if not self.detector.is_loaded:
            return {
                "timestamp": now,
                "fps": self.last_fps,
                "inference_ms": self.last_inference_ms,
                "detections": [],
                "fall_event": False,
                "alert_latency": None,
                "model_loaded": False,
                "pose_loaded": self.detector.pose_loaded,
                "method": self.method,
            }

        with self._lock:
            combined = self.detector.detect_and_pose(frame, track=True)
            persons_det = combined["persons"]

            # 2. Update tracker
            self.tracker.update(persons_det)

            # 3. Per-person: extract features + temporal analysis
            output_persons = []
            fall_event_global = False
            alert_latency = None

            for p in persons_det:
                pid = p.get("person_id", -1)
                if pid < 0:
                    continue
                bbox = p["bbox"]
                kps = p.get("keypoints", [])
                prev = self.prev_features.get(pid)

                feats = extract_features(bbox, kps, prev_features=prev, fps=self.last_fps or 30.0)
                self.prev_features[pid] = feats

                # 4. Posture
                posture, post_conf = classify_posture(feats)

                # 5. Temporal fall
                result = self.temporal.update(pid, feats, now)
                fall_prob = result["fall_probability"]
                is_fall = result["fall_event"]
                latency = result["alert_latency"]

                # 6. ML fusion (optional)
                if self.ml and self.ml.is_loaded:
                    signals = result.get("signals", {})
                    ml_feats = {
                        "height_drop_ratio": signals.get("height_drop_ratio", 0.0),
                        "max_vy": signals.get("max_vy", 0.0),
                        "max_speed": signals.get("max_speed", 0.0),
                        "max_ratio": signals.get("max_ratio", 0.0),
                        "angle_change": signals.get("angle_change", 0.0),
                        "posture_change_count": 0.0,
                        "bbox_ratio_mean": feats.get("bbox_ratio", 1.0),
                        "bbox_h_mean": feats.get("bbox_h", 1.0),
                        "body_angle_mean": feats.get("body_angle", 90.0),
                        "torso_angle_mean": feats.get("torso_angle", 90.0),
                        "max_ay": abs(feats.get("ay", 0.0)),
                        "dh_ratio": abs(feats.get("dh_ratio", 0.0)),
                        "dratio": abs(feats.get("dratio", 0.0)),
                        "fall_score": fall_prob,
                    }
                    ml_prob = self.ml.predict_proba(ml_feats)
                    # Weighted fusion
                    fall_prob = 0.6 * fall_prob + 0.4 * ml_prob

                # Count fall events
                if is_fall:
                    fall_event_global = True
                    self.total_fall_events += 1
                    if latency is not None:
                        self.latencies.append(latency)
                        alert_latency = latency

                self.total_detections += 1

                output_persons.append({
                    "person_id": pid,
                    "bbox": bbox,
                    "confidence": float(p.get("confidence", 0.0)),
                    "posture": posture,
                    "posture_confidence": float(post_conf),
                    "fall_probability": float(fall_prob),
                    "fall_event": bool(is_fall),
                    "alert_latency": float(latency) if latency is not None else None,
                })

            return {
                "timestamp": now,
                "fps": self.last_fps,
                "inference_ms": self.last_inference_ms,
                "detections": output_persons,
                "fall_event": fall_event_global,
                "alert_latency": float(alert_latency) if alert_latency is not None else None,
                "model_loaded": True,
                "pose_loaded": self.detector.pose_loaded,
                "method": self.method,
            }

    def get_stats(self) -> Dict[str, Any]:
        lats = list(self.latencies)
        return {
            "total_detections": self.total_detections,
            "total_fall_events": self.total_fall_events,
            "false_alarms": self.false_alarm_count,
            "fps": self.last_fps,
            "inference_ms": self.last_inference_ms,
            "avg_inference_ms": float(np.mean(self.inference_times)) if self.inference_times else 0.0,
            "avg_alert_latency": float(np.mean(lats)) if lats else None,
            "min_alert_latency": float(np.min(lats)) if lats else None,
            "max_alert_latency": float(np.max(lats)) if lats else None,
            "model_loaded": self.model_loaded,
            "pose_loaded": self.pose_loaded,
            "method": self.method,
            "device": self.device,
        }