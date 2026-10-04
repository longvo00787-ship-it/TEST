"""
Utility functions - helper chung.
"""
import time
import json
import math
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import numpy as np


def now_ts() -> float:
    return time.time()


def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def bbox_center(bbox: List[float]) -> Tuple[float, float]:
    """bbox = [x1, y1, x2, y2] -> (cx, cy)."""
    x1, y1, x2, y2 = bbox
    return ((x1 + x2) / 2.0, (y1 + y2) / 2.0)


def bbox_size(bbox: List[float]) -> Tuple[float, float]:
    """Return (w, h)."""
    x1, y1, x2, y2 = bbox
    return (x2 - x1, y2 - y1)


def bbox_ratio(bbox: List[float]) -> float:
    """w/h ratio. >1 means wider than tall."""
    w, h = bbox_size(bbox)
    if h <= 1e-6:
        return 0.0
    return w / h


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    if abs(b) < 1e-9:
        return default
    return a / b


def angle_between(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Angle of vector p1->p2 with vertical axis (degrees). 0 = vertical up, 90 = horizontal."""
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    angle = math.degrees(math.atan2(abs(dx), abs(dy) + 1e-9))
    return angle


def euclidean_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)


class FPSCounter:
    """Đếm FPS bằng moving average."""

    def __init__(self, window: int = 30):
        self.window = window
        self.timestamps: List[float] = []

    def tick(self):
        self.timestamps.append(time.time())
        if len(self.timestamps) > self.window:
            self.timestamps = self.timestamps[-self.window:]

    def fps(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self.timestamps) - 1) / elapsed


class Timer:
    """Đo thời gian theo block."""

    def __init__(self):
        self.start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self):
        self.start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self.start) * 1000.0


def write_json(path: Path, data: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    return p