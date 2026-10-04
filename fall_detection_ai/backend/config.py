"""
Configuration module - cấu hình tập trung cho toàn hệ thống.
"""
import os
from pathlib import Path
from typing import Optional

# Project root (fall_detection_ai/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Backend paths
BACKEND_ROOT = PROJECT_ROOT / "backend"
MODELS_DIR = PROJECT_ROOT / "models"
RUNS_DIR = PROJECT_ROOT / "runs"
DATASETS_DIR = PROJECT_ROOT / "datasets"
CONFIGS_DIR = PROJECT_ROOT / "configs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Ensure dirs exist
for d in [MODELS_DIR, RUNS_DIR, DATASETS_DIR, CONFIGS_DIR, SCRIPTS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Dataset subdirs
DATASET_RAW = DATASETS_DIR / "raw" / "videos"
DATASET_PROCESSED = DATASETS_DIR / "processed"
DATASET_ANNOTATIONS = DATASETS_DIR / "annotations"
DATASET_TRAIN = DATASETS_DIR / "train"
DATASET_VAL = DATASETS_DIR / "val"
DATASET_TEST = DATASETS_DIR / "test"

for d in [DATASET_RAW, DATASET_PROCESSED, DATASET_ANNOTATIONS,
          DATASET_TRAIN, DATASET_VAL, DATASET_TEST]:
    d.mkdir(parents=True, exist_ok=True)

# Database
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{PROJECT_ROOT}/fall_detection.db")

# Model paths
DEFAULT_DETECT_MODEL = "yolov8n.pt"  # Pretrained YOLO
POSE_MODEL = "yolov8n-pose.pt"
TRAINED_MODEL_PATH = RUNS_DIR / "detect" / "train" / "weights" / "best.pt"

# Detection thresholds
PERSON_CONF_THRESHOLD = 0.4
POSE_CONF_THRESHOLD = 0.3
TRACKER_CONFIG = "bytetrack.yaml"

# Fall detection params
FALL_WINDOW_SECONDS = 1.5  # temporal window for fall analysis
FALL_VERTICAL_DROP_RATIO = 0.3  # bbox height drop ratio triggers fast transition
FALL_HORIZONTAL_RATIO = 1.3  # width/height ratio for horizontal posture
FALL_PROB_THRESHOLD = 0.65  # threshold to confirm fall
ALERT_CONFIRM_FRAMES = 3  # consecutive frames needed to confirm fall

# Camera / video
WEBCAM_INDEX = 0
VIDEO_OUTPUT_DIR = RUNS_DIR / "video_outputs"
VIDEO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


def get_device():
    """Auto-detect best device."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


def model_exists(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0