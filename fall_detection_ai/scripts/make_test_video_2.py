"""Tạo video test với human-like silhouette mà YOLO có thể detect."""
import cv2
import numpy as np
from pathlib import Path

out_dir = Path(__file__).parent.parent / "datasets" / "raw" / "videos"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "test_standing.mp4"

fps = 30.0
duration = 15.0
width, height = 640, 480
total_frames = int(fps * duration)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))


def draw_human(img, x, y, w=80, h=200, color=(180, 180, 200)):
    """Vẽ human silhouette tại (x, y) là top-left bbox."""
    # Head
    head_cx = x + w // 2
    head_cy = y + 25
    cv2.circle(img, (head_cx, head_cy), 22, color, -1)
    # Neck
    cv2.rectangle(img, (head_cx - 8, y + 47), (head_cx + 8, y + 60), color, -1)
    # Body
    cv2.rectangle(img, (x + 15, y + 60), (x + w - 15, y + h - 35), color, -1)
    # Arms
    cv2.rectangle(img, (x, y + 65), (x + 12, y + h - 50), color, -1)
    cv2.rectangle(img, (x + w - 12, y + 65), (x + w, y + h - 50), color, -1)
    # Legs
    cv2.rectangle(img, (x + 20, y + h - 35), (x + 38, y + h), color, -1)
    cv2.rectangle(img, (x + w - 38, y + h - 35), (x + w - 20, y + h), color, -1)


def draw_human_lying(img, x, y, color=(180, 180, 200)):
    """Human lying ngang."""
    # Head on the left
    cv2.circle(img, (x + 25, y), 22, color, -1)
    cv2.rectangle(img, (x + 47, y - 8), (x + 60, y + 8), color, -1)
    cv2.rectangle(img, (x + 60, y - 15), (x + 200, y + 15), color, -1)
    cv2.rectangle(img, (x + 70, y - 25), (x + 80, y - 15), color, -1)
    cv2.rectangle(img, (x + 70, y + 15), (x + 80, y + 25), color, -1)
    cv2.rectangle(img, (x + 180, y - 25), (x + 200, y - 15), color, -1)
    cv2.rectangle(img, (x + 180, y + 15), (x + 200, y + 25), color, -1)


for i in range(total_frames):
    frame = np.full((height, width, 3), 60, dtype=np.uint8)
    # Floor
    cv2.line(frame, (0, 410), (width, 410), (80, 80, 90), 3)
    # Background detail (helps YOLO)
    cv2.rectangle(frame, (0, 0), (width, 50), (40, 40, 50), -1)

    t = i / fps
    cx = int(320 + 10 * np.sin(t * 0.5))

    if t < 4:
        # Standing still
        x = cx - 40
        y = 200
        draw_human(frame, x, y)
    elif t < 6:
        # Walking
        x = cx - 40 + int((t - 4) * 30)
        y = 200
        draw_human(frame, x, y)
    elif t < 8:
        # Falling
        progress = (t - 6) / 2
        if progress < 0.5:
            # tilting
            x = cx - 40
            y = 200 + int(60 * progress * 2)
            cv2.save_xform = frame
            # rotated rectangle - approximate by drawing rotated
            angle = int(45 * progress * 2)
            M = cv2.getRotationMatrix2D((x + 40, y + 100), -angle, 1.0)
            temp = np.zeros_like(frame)
            draw_human(temp, x, y)
            rotated = cv2.warpAffine(temp, M, (width, height))
            mask = (rotated.sum(axis=2) > 0)
            frame[mask] = rotated[mask]
        else:
            # Almost horizontal
            x = cx - 100
            y = 360
            draw_human_lying(frame, x, y)
    else:
        # Lying on floor
        x = cx - 100
        y = 360
        draw_human_lying(frame, x, y)

    cv2.putText(frame, f"t={t:.2f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
    writer.write(frame)

writer.release()
print(f"Created {out_path}")