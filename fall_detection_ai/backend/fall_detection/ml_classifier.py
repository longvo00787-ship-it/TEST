"""
ML-based Fall Classifier - Optional method B.
Train Random Forest / XGBoost từ feature sequences đã được label.

Features được trích từ temporal window:
- height_drop_ratio
- max_vy
- max_speed
- max_ratio
- angle_change
- posture transition count
- bbox_ratio mean
- bbox_h mean
- body_angle mean
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import joblib

from backend.config import RUNS_DIR
import os

MODELS_DIR = Path(os.getenv("MODELS_DIR", "./models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)


FEATURE_COLUMNS = [
    "height_drop_ratio",
    "max_vy",
    "max_speed",
    "max_ratio",
    "angle_change",
    "posture_change_count",
    "bbox_ratio_mean",
    "bbox_h_mean",
    "body_angle_mean",
    "torso_angle_mean",
    "max_ay",
    "dh_ratio",
    "dratio",
    "fall_score",
]


class MLFallClassifier:
    """Wrapper cho ML model (RandomForest / XGBoost)."""

    def __init__(self, model_path: Optional[str] = None, model_type: str = "rf"):
        self.model = None
        self.model_type = model_type
        self.model_path = model_path or str(MODELS_DIR / "fall_classifier.joblib")
        if Path(self.model_path).exists():
            try:
                self.model = joblib.load(self.model_path)
            except Exception as e:
                print(f"[MLFallClassifier] load fail: {e}")

    @property
    def is_loaded(self) -> bool:
        return self.model is not None

    def predict_proba(self, features: Dict[str, float]) -> float:
        """Trả về xác suất fall (0-1)."""
        if not self.is_loaded:
            return 0.0
        x = np.array([[features.get(c, 0.0) for c in FEATURE_COLUMNS]])
        try:
            if hasattr(self.model, "predict_proba"):
                proba = self.model.predict_proba(x)[0]
                # class 1 = fall
                if len(proba) > 1:
                    return float(proba[1])
                return float(proba[0])
            else:
                pred = self.model.predict(x)[0]
                return float(pred)
        except Exception as e:
            print(f"[MLFallClassifier] predict error: {e}")
            return 0.0

    def train(self, X: np.ndarray, y: np.ndarray, save: bool = True):
        """Train classifier. X shape: (n_samples, n_features), y: 0/1."""
        if self.model_type == "xgb":
            try:
                from xgboost import XGBClassifier
                self.model = XGBClassifier(
                    n_estimators=200, max_depth=6, learning_rate=0.1,
                    use_label_encoder=False, eval_metric="logloss"
                )
            except ImportError:
                from sklearn.ensemble import RandomForestClassifier
                self.model = RandomForestClassifier(n_estimators=200, max_depth=10)
                self.model_type = "rf"
        else:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=200, max_depth=10)

        self.model.fit(X, y)

        if save:
            joblib.dump(self.model, self.model_path)
        return self.model