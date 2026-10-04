"""
YOLO Training Pipeline.
Sử dụng Ultralytics YOLO API để train.

Ví dụ:
    python -m backend.training.train_yolo --data datasets/data.yaml --model yolov8n.pt --epochs 50
"""
import argparse
import shutil
import time
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False

from backend.config import (
    RUNS_DIR, DATASETS_DIR, CONFIGS_DIR, get_device
)
from backend.database.models import TrainingJob, init_db, SessionLocal


def create_default_data_yaml() -> Path:
    """Tạo data.yaml mặc định nếu chưa có - trỏ vào datasets/."""
    yaml_path = DATASETS_DIR / "data.yaml"
    if yaml_path.exists():
        return yaml_path

    content = f"""# YOLO dataset config
path: {DATASETS_DIR.resolve()}
train: train/images
val: val/images
test: test/images

# Classes
names:
  0: person
  1: fall

# Number of classes
nc: 2
"""
    yaml_path.write_text(content, encoding="utf-8")
    return yaml_path


def train_yolo(
    data: str,
    model: str = "yolov8n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    lr: float = 0.001,
    device: str = "auto",
    project: str = "fall_detection",
    name: str = "train",
    save_period: int = 10,
    patience: int = 20,
) -> Dict[str, Any]:
    """Train YOLO và lưu job vào DB."""
    if not ULTRALYTICS_AVAILABLE:
        return {"success": False, "error": "ultralytics not installed"}

    if device == "auto":
        device = get_device()

    init_db()
    db = SessionLocal()
    job = TrainingJob(
        status="running",
        model_name=model,
        epochs=epochs,
        batch_size=batch,
        imgsz=imgsz,
        learning_rate=lr,
        device=device,
        data_yaml=data,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    start_ts = time.time()
    try:
        yolo = YOLO(model)
        results = yolo.train(
            data=data,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            project=str(RUNS_DIR / project),
            name=name,
            save_period=save_period,
            patience=patience,
            lr0=lr,
            verbose=True,
        )

        # Lấy metrics thực tế từ results
        save_path = Path(results.save_dir)
        results_csv = save_path / "results.csv"
        final_map50 = None
        final_map50_95 = None
        final_precision = None
        final_recall = None

        if results_csv.exists():
            try:
                import pandas as pd
                df = pd.read_csv(results_csv)
                df.columns = [c.strip() for c in df.columns]
                if "metrics/mAP50(B)" in df.columns:
                    final_map50 = float(df["metrics/mAP50(B)"].iloc[-1])
                if "metrics/mAP50-95(B)" in df.columns:
                    final_map50_95 = float(df["metrics/mAP50-95(B)"].iloc[-1])
                if "metrics/precision(B)" in df.columns:
                    final_precision = float(df["metrics/precision(B)"].iloc[-1])
                if "metrics/recall(B)" in df.columns:
                    final_recall = float(df["metrics/recall(B)"].iloc[-1])
            except Exception as e:
                print(f"[train] cannot parse results.csv: {e}")

        weights_dir = save_path / "weights"
        best_path = weights_dir / "best.pt"
        last_path = weights_dir / "last.pt"
        weights_path = str(best_path if best_path.exists() else last_path)

        # Copy best.pt to runs/detect/train/weights/best.pt để app dùng
        canonical_weights = RUNS_DIR / "detect" / "train" / "weights" / "best.pt"
        canonical_weights.parent.mkdir(parents=True, exist_ok=True)
        if best_path.exists():
            shutil.copy2(best_path, canonical_weights)

        job.status = "completed"
        job.finished_at = time.time() if False else None  # datetime
        from datetime import datetime
        job.finished_at = datetime.utcnow()
        job.final_map50 = final_map50
        job.final_map50_95 = final_map50_95
        job.final_precision = final_precision
        job.final_recall = final_recall
        job.weights_path = weights_path
        job.log = f"Training completed in {time.time() - start_ts:.1f}s"
        db.commit()

        return {
            "success": True,
            "job_id": job.id,
            "weights_path": weights_path,
            "final_map50": final_map50,
            "final_map50_95": final_map50_95,
            "final_precision": final_precision,
            "final_recall": final_recall,
            "duration_s": time.time() - start_ts,
        }

    except Exception as e:
        from datetime import datetime
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        job.log = str(e)
        db.commit()
        return {"success": False, "error": str(e), "job_id": job.id}
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=str, default=None)
    parser.add_argument("--model", type=str, default="yolov8n.pt")
    parser.add_argument("--epochs", type=int, default=50)
    parser.add_argument("--imgsz", type=int, default=640)
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--lr", type=float, default=0.001)
    parser.add_argument("--device", type=str, default="auto")
    parser.add_argument("--name", type=str, default="train")
    parser.add_argument("--patience", type=int, default=20)
    args = parser.parse_args()

    data_yaml = args.data or str(create_default_data_yaml())
    print(f"Training YOLO: model={args.model}, data={data_yaml}, epochs={args.epochs}")
    result = train_yolo(
        data=data_yaml,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        lr=args.lr,
        device=args.device,
        name=args.name,
        patience=args.patience,
    )
    print(result)


if __name__ == "__main__":
    main()