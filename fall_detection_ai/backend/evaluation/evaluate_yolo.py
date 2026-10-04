"""
YOLO Evaluation Pipeline.
Đánh giá model đã train trên dataset, tính precision, recall, mAP50, mAP50-95.

Lưu kết quả vào DB và xuất plots (confusion matrix, PR curve, training loss).
"""
import argparse
import json
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from backend.config import RUNS_DIR, DATASETS_DIR, get_device
from backend.database.models import EvaluationResult, init_db, SessionLocal


def evaluate_yolo(
    weights: str,
    data: str,
    imgsz: int = 640,
    batch: int = 16,
    device: str = "auto",
    save_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Đánh giá YOLO model. Returns dict metrics."""
    if not ULTRALYTICS_AVAILABLE:
        return {"success": False, "error": "ultralytics not installed"}

    if not Path(weights).exists():
        return {"success": False, "error": f"weights not found: {weights}"}

    if device == "auto":
        device = get_device()

    save_dir = save_dir or str(RUNS_DIR / "val" / f"eval_{int(time.time())}")
    Path(save_dir).mkdir(parents=True, exist_ok=True)

    try:
        yolo = YOLO(weights)
        metrics = yolo.val(
            data=data,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project=save_dir,
            name="val",
            plots=True,
            save_json=True,
        )

        # metrics is a DetMetrics object
        results = {
            "success": True,
            "precision": float(metrics.box.p) if hasattr(metrics.box, "p") else None,
            "recall": float(metrics.box.r) if hasattr(metrics.box, "r") else None,
            "map50": float(metrics.box.map50) if hasattr(metrics.box, "map50") else None,
            "map50_95": float(metrics.box.map) if hasattr(metrics.box, "map") else None,
            "f1_score": (
                2 * (float(metrics.box.p) * float(metrics.box.r)) /
                (float(metrics.box.p) + float(metrics.box.r) + 1e-9)
                if hasattr(metrics.box, "p") and hasattr(metrics.box, "r") else None
            ),
            "num_classes": len(metrics.box.ap_class_index) if hasattr(metrics.box, "ap_class_index") else 0,
            "save_dir": save_dir,
            "weights": weights,
        }

        # Per-class
        try:
            if hasattr(metrics.box, "maps"):
                results["per_class_map50_95"] = [float(m) for m in metrics.box.maps]
        except Exception:
            pass

        # Lưu plots
        plots_src = Path(save_dir) / "val"
        if plots_src.exists():
            for png in plots_src.glob("*.png"):
                dest = RUNS_DIR / "evaluation_plots"
                dest.mkdir(parents=True, exist_ok=True)
                shutil.copy2(png, dest / png.name)

        # Lưu vào DB
        init_db()
        db = SessionLocal()
        try:
            ev = EvaluationResult(
                model_name=Path(weights).name,
                method="yolo",
                precision=results["precision"],
                recall=results["recall"],
                map50=results["map50"],
                map50_95=results["map50_95"],
                f1_score=results["f1_score"],
                num_samples=0,
                notes=json.dumps(results, default=str),
            )
            db.add(ev)
            db.commit()
        finally:
            db.close()

        return results

    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--weights", required=True)
    parser.add_argument("--data", required=True)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--device", type=str, default="auto")
    args = parser.parse_args()

    print(f"Evaluating: weights={args.weights}, data={args.data}")
    res = evaluate_yolo(
        weights=args.weights,
        data=args.data,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
    )
    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()