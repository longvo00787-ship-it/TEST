"""
Fall Detection Evaluation - đánh giá hệ thống phát hiện té ngã (rule-based + ML).
Đánh giá trên video clips đã gán nhãn:
- true_positive: có fall, detect được fall
- false_positive: không fall, detect fall (false alarm)
- false_negative: có fall, không detect (missed)
- true_negative: không fall, không detect
"""
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

import cv2
import numpy as np

from backend.config import get_device
from backend.inference import FallDetectionEngine
from backend.database.models import EvaluationResult, init_db, SessionLocal
from backend.utils.helpers import FPSCounter


def evaluate_fall_detection(
    weights: Optional[str] = None,
    annotations_file: Optional[str] = None,
    device: str = "auto",
) -> Dict[str, Any]:
    """
    annotations_file: JSON file chứa labels.
    Format:
    [
      {"video_path": "datasets/raw/videos/clip1.mp4", "fall_at_frame": 120, "duration_frames": 300},
      ...
    ]
    """
    if device == "auto":
        device = get_device()

    if not annotations_file or not Path(annotations_file).exists():
        # Không có labels -> trả về cấu trúc rỗng nhưng có ghi chú
        return {
            "success": False,
            "error": "No annotations file. Provide a JSON file with {video_path, fall_at_frame} entries.",
            "metrics": None,
        }

    with open(annotations_file, "r") as f:
        annotations = json.load(f)

    engine = FallDetectionEngine(detect_weights=weights, device=device)
    if not engine.model_loaded:
        return {"success": False, "error": "Model not loaded"}

    tp, fp, fn, tn = 0, 0, 0, 0
    per_video_results: List[Dict[str, Any]] = []
    latencies: List[float] = []

    for ann in annotations:
        vp = ann.get("video_path")
        if not vp or not Path(vp).exists():
            continue
        fall_at = ann.get("fall_at_frame", -1)  # -1 = no fall
        duration = ann.get("duration_frames", 0)

        cap = cv2.VideoCapture(vp)
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

        # Process video
        cap = cv2.VideoCapture(vp)
        detected_fall = False
        detected_frame = -1
        latency = None
        fps_counter = FPSCounter()

        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            res = engine.process_frame(frame)
            fps_counter.tick()
            if res["fall_event"]:
                if not detected_fall:
                    detected_fall = True
                    detected_frame = frame_idx
                    if res["alert_latency"] is not None:
                        latency = res["alert_latency"]
                        latencies.append(latency)
                elif latency is None and res["alert_latency"] is not None:
                    latency = res["alert_latency"]
                    latencies.append(latency)

            frame_idx += 1
            if duration and frame_idx > duration:
                break
        cap.release()

        ground_truth_fall = fall_at >= 0
        if ground_truth_fall and detected_fall:
            tp += 1
            outcome = "true_positive"
        elif not ground_truth_fall and not detected_fall:
            tn += 1
            outcome = "true_negative"
        elif not ground_truth_fall and detected_fall:
            fp += 1
            outcome = "false_positive"
        else:
            fn += 1
            outcome = "false_negative"

        per_video_results.append({
            "video": vp,
            "ground_truth_fall": ground_truth_fall,
            "detected_fall": detected_fall,
            "detected_frame": detected_frame,
            "fall_at_frame": fall_at,
            "outcome": outcome,
            "alert_latency": latency,
        })

    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    avg_latency = float(np.mean(latencies)) if latencies else None

    metrics = {
        "accuracy": float(accuracy),
        "precision": float(precision),
        "recall": float(recall),
        "f1_score": float(f1),
        "true_positive": int(tp),
        "false_positive": int(fp),
        "true_negative": int(tn),
        "false_negative": int(fn),
        "avg_alert_latency": avg_latency,
        "num_videos": int(total),
        "per_video": per_video_results,
    }

    # Save to DB
    init_db()
    db = SessionLocal()
    try:
        ev = EvaluationResult(
            model_name=Path(weights).name if weights else "yolov8n",
            method="rule_based",
            precision=metrics["precision"],
            recall=metrics["recall"],
            f1_score=metrics["f1_score"],
            accuracy=metrics["accuracy"],
            false_positive=metrics["false_positive"],
            false_negative=metrics["false_negative"],
            avg_latency=avg_latency,
            num_samples=total,
            notes=json.dumps(per_video_results, default=str)[:5000],
        )
        db.add(ev)
        db.commit()
    finally:
        db.close()

    return {"success": True, "metrics": metrics}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", default=None)
    parser.add_argument("--annotations", default=None)
    parser.add_argument("--device", default="auto")
    args = parser.parse_args()
    res = evaluate_fall_detection(args.weights, args.annotations, args.device)
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()