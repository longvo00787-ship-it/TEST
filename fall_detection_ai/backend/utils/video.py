"""
Video processing utilities.
- Extract frames
- Process video and save annotated output
- Get video metadata
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Generator, Tuple, Dict, Any


def get_video_info(path: str) -> Dict[str, Any]:
    """Trả về thông tin video."""
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        return {"opened": False}
    info = {
        "opened": True,
        "fps": float(cap.get(cv2.CAP_PROP_FPS)),
        "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        "total_frames": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        "path": path,
    }
    duration = info["total_frames"] / info["fps"] if info["fps"] > 0 else 0
    info["duration_s"] = float(duration)
    cap.release()
    return info


def frame_generator(path: str) -> Generator[Tuple[int, np.ndarray], None, None]:
    """Yield (idx, frame)."""
    cap = cv2.VideoCapture(path)
    idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        yield idx, frame
        idx += 1
    cap.release()


def save_video_output(
    output_path: str,
    frames: list,
    fps: float = 30.0,
    width: int = 640,
    height: int = 480,
):
    """Lưu list frames thành video mp4."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    for f in frames:
        if f.shape[1] != width or f.shape[0] != height:
            f = cv2.resize(f, (width, height))
        writer.write(f)
    writer.release()


def annotate_frame(
    frame: np.ndarray,
    detections: list,
    fps: float = 0.0,
    inference_ms: float = 0.0,
) -> np.ndarray:
    """Vẽ bounding boxes + info lên frame."""
    out = frame.copy()
    for det in detections:
        bbox = det.get("bbox")
        if not bbox or len(bbox) < 4:
            continue
        x1, y1, x2, y2 = [int(v) for v in bbox]
        is_fall = det.get("fall_event", False)
        color = (0, 0, 255) if is_fall else (0, 255, 0)
        cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)

        pid = det.get("person_id", "?")
        posture = det.get("posture", "unknown").upper()
        conf = det.get("confidence", 0.0)
        fall_prob = det.get("fall_probability", 0.0)
        label = f"Person #{pid:02d} {posture} {conf:.0%}"
        cv2.putText(out, label, (x1, max(y1 - 8, 12)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        if is_fall:
            cv2.putText(out, "FALL DETECTED", (x1, min(y2 + 22, out.shape[0] - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # HUD
    if fps > 0:
        cv2.putText(out, f"FPS: {fps:.1f}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    if inference_ms > 0:
        cv2.putText(out, f"Inference: {inference_ms:.1f} ms", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    return out