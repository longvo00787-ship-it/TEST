"""
YOLO Person Detection & Pose Estimation wrapper.
Sử dụng Ultralytics YOLO để detect người + keypoints.

Hỗ trợ:
- Person detection (yolov8n.pt hoặc best.pt đã train)
- Pose estimation (yolov8n-pose.pt hoặc best-pose.pt đã train)
- Tracking tích hợp (ByteTrack mặc định)
"""
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from backend.config import (
    DEFAULT_DETECT_MODEL, POSE_MODEL, TRAINED_MODEL_PATH,
    PERSON_CONF_THRESHOLD, POSE_CONF_THRESHOLD, TRACKER_CONFIG
)
from backend.utils.helpers import bbox_center, bbox_size


class YOLODetector:
    """Wrapper cho YOLO detect + tracking + pose."""

    def __init__(
        self,
        detect_weights: Optional[str] = None,
        pose_weights: Optional[str] = None,
        device: str = "cpu",
    ):
        self.device = device
        self.detect_model = None
        self.pose_model = None
        self.detect_weights_used = None
        self.pose_weights_used = None

        if not ULTRALYTICS_AVAILABLE:
            return

        # Detect model
        detect_path = detect_weights or self._resolve_detect_weights()
        try:
            self.detect_model = YOLO(detect_path)
            self.detect_weights_used = str(detect_path)
        except Exception as e:
            print(f"[YOLODetector] Cannot load detect model {detect_path}: {e}")
            self.detect_model = None

        # Pose model
        pose_path = pose_weights or self._resolve_pose_weights()
        try:
            self.pose_model = YOLO(pose_path)
            self.pose_weights_used = str(pose_path)
        except Exception as e:
            print(f"[YOLODetector] Cannot load pose model {pose_path}: {e}")
            self.pose_model = None

    def _resolve_detect_weights(self) -> str:
        """Ưu tiên best.pt đã train, fallback pretrained."""
        if TRAINED_MODEL_PATH.exists() and TRAINED_MODEL_PATH.stat().st_size > 0:
            return str(TRAINED_MODEL_PATH)
        return DEFAULT_DETECT_MODEL

    def _resolve_pose_weights(self) -> str:
        trained_pos = TRAINED_MODEL_PATH.parent.parent / "weights" / "best-pose.pt"
        if trained_pos.exists() and trained_pos.stat().st_size > 0:
            return str(trained_pos)
        return POSE_MODEL

    @property
    def is_loaded(self) -> bool:
        return self.detect_model is not None

    @property
    def pose_loaded(self) -> bool:
        return self.pose_model is not None

    def detect_persons(
        self,
        frame: np.ndarray,
        track: bool = True,
        conf: float = PERSON_CONF_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        Detect người + tracking trong 1 frame.
        Returns list of dicts: {person_id, bbox, confidence, class_name}.
        """
        if not self.is_loaded or frame is None:
            return []

        try:
            if track:
                results = self.detect_model.track(
                    frame,
                    persist=True,
                    classes=[0],  # person class in COCO
                    conf=conf,
                    tracker=TRACKER_CONFIG,
                    verbose=False,
                    device=self.device,
                )
            else:
                results = self.detect_model.predict(
                    frame,
                    classes=[0],
                    conf=conf,
                    verbose=False,
                    device=self.device,
                )
        except Exception as e:
            print(f"[detect_persons] error: {e}")
            return []

        detections: List[Dict[str, Any]] = []
        if len(results) == 0:
            return detections

        r = results[0]
        boxes = r.boxes
        if boxes is None or len(boxes) == 0:
            return detections

        for i, box in enumerate(boxes):
            try:
                xyxy = box.xyxy[0].cpu().numpy().tolist()
                conf_val = float(box.conf[0].cpu().numpy())
                cls_id = int(box.cls[0].cpu().numpy()) if box.cls is not None else 0
                cls_name = r.names.get(cls_id, "person") if r.names else "person"

                pid = -1
                if box.id is not None:
                    pid = int(box.id[0].cpu().numpy())

                detections.append({
                    "person_id": pid,
                    "bbox": xyxy,
                    "confidence": conf_val,
                    "class_id": cls_id,
                    "class_name": cls_name,
                })
            except Exception:
                continue

        return detections

    def estimate_pose(
        self,
        frame: np.ndarray,
        person_bboxes: Optional[List[List[float]]] = None,
        conf: float = POSE_CONF_THRESHOLD,
    ) -> List[Dict[str, Any]]:
        """
        Pose estimation. Trả về keypoints cho từng người.

        Returns: list of {keypoints: [{x, y, conf, name}, ...], bbox}
        keypoint name tham chiếu COCO pose indices:
        0:nose 1:l_eye 2:r_eye 3:l_ear 4:r_ear
        5:l_shoulder 6:r_shoulder 7:l_elbow 8:r_elbow
        9:l_wrist 10:r_wrist 11:l_hip 12:r_hip
        13:l_knee 14:r_knee 15:l_ankle 16:r_ankle
        """
        if not self.pose_loaded or frame is None:
            return []

        try:
            results = self.pose_model.predict(
                frame,
                conf=conf,
                verbose=False,
                device=self.device,
            )
        except Exception as e:
            print(f"[estimate_pose] error: {e}")
            return []

        if len(results) == 0:
            return []
        r = results[0]

        persons = []
        if r.keypoints is None or r.keypoints.xy is None or len(r.keypoints.xy) == 0:
            return persons

        kp_names = [
            "nose", "left_eye", "right_eye", "left_ear", "right_ear",
            "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
            "left_wrist", "right_wrist", "left_hip", "right_hip",
            "left_knee", "right_knee", "left_ankle", "right_ankle",
        ]

        n = len(r.keypoints.xy)
        for i in range(n):
            try:
                xy = r.keypoints.xy[i].cpu().numpy()  # (17, 2)
                kpconf = (r.keypoints.conf[i].cpu().numpy()
                          if r.keypoints.conf is not None else np.ones(len(xy)))
                bbox = (r.boxes.xyxy[i].cpu().numpy().tolist()
                        if r.boxes is not None and i < len(r.boxes) else None)

                kps = []
                for j in range(len(xy)):
                    kps.append({
                        "name": kp_names[j] if j < len(kp_names) else f"k{j}",
                        "x": float(xy[j][0]),
                        "y": float(xy[j][1]),
                        "conf": float(kpconf[j]) if j < len(kpconf) else 1.0,
                    })

                persons.append({
                    "keypoints": kps,
                    "bbox": bbox,
                })
            except Exception:
                continue

        return persons

    def detect_and_pose(
        self, frame: np.ndarray, track: bool = True
    ) -> Dict[str, Any]:
        """Combined: detect persons with tracking, then estimate pose cho mỗi người.

        Returns dict:
        {
          'persons': [
            {'person_id', 'bbox', 'confidence', 'keypoints': [...]}
          ]
        }
        """
        persons = self.detect_persons(frame, track=track)

        # Match pose với person bằng IoU
        pose_results = self.estimate_pose(frame)

        # Nếu có pose, gán vào person bằng IoU max
        for person in persons:
            person["keypoints"] = []
            best_iou = 0.0
            best_pose = None
            pb = person["bbox"]
            for pr in pose_results:
                if pr["bbox"] is None:
                    continue
                iou = self._iou(pb, pr["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_pose = pr
            if best_pose and best_iou > 0.3:
                person["keypoints"] = best_pose["keypoints"]

        return {"persons": persons}

    @staticmethod
    def _iou(b1, b2) -> float:
        x1 = max(b1[0], b2[0])
        y1 = max(b1[1], b2[1])
        x2 = min(b1[2], b2[2])
        y2 = min(b1[3], b2[3])
        inter = max(0, x2 - x1) * max(0, y2 - y1)
        a1 = max(0, b1[2] - b1[0]) * max(0, b1[3] - b1[1])
        a2 = max(0, b2[2] - b2[0]) * max(0, b2[3] - b2[1])
        union = a1 + a2 - inter
        if union <= 0:
            return 0.0
        return inter / union