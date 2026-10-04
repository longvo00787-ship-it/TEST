"""Tạo một test video giả lập để test pipeline."""
import cv2
import numpy as np
from pathlib import Path

# Tạo video 10s, 30fps, 640x480 với 1 person "di chuyển"
out_dir = Path(__file__).parent.parent / "datasets" / "raw" / "videos"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "test_synthetic.mp4"

fps = 30.0
duration = 10.0
width, height = 640, 480
total_frames = int(fps * duration)

fourcc = cv2.VideoWriter_fourcc(*"mp4v")
writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

for i in range(total_frames):
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    # Background gradient
    frame[:, :] = [40, 30, 20]

    t = i / fps
    # Person standing at start, then falls at t=5s
    if t < 5:
        # Standing person
        cx = int(320 + 20 * np.sin(t))
        # bbox w=80, h=200
        x1 = cx - 40
        y1 = 200
        x2 = cx + 40
        y2 = 400
        # body
        cv2.rectangle(frame, (x1, y1), (x2, y2), (180, 180, 200), -1)
        # head
        cv2.circle(frame, (cx, y1 - 20), 20, (220, 220, 230), -1)
    elif t < 7:
        # Falling - rotate
        progress = (t - 5) / 2
        cx = int(320 + 30 * progress)
        cy = int(300 + 80 * progress)
        # tilted rectangle
        angle_deg = int(90 * progress)
        rect_w, rect_h = int(180 * progress + 80), int(180 - 100 * progress + 50)
        rect = ((cx, cy), (rect_w, rect_h), angle_deg)
        box = cv2.boxPoints(rect)
        cv2.fillPoly(frame, [box.astype(int)], (180, 180, 200))
        # head
        head_pos = (cx - int(60 * progress), cy - int(30 * (1 - progress)))
        cv2.circle(frame, head_pos, 15, (220, 220, 230), -1)
    else:
        # Lying
        cx = int(380 + 5 * (t - 7))
        cy = int(380)
        rect = ((cx, cy), (180, 60), 0)
        box = cv2.boxPoints(rect)
        cv2.fillPoly(frame, [box.astype(int)], (180, 180, 200))
        cv2.circle(frame, (cx - 80, cy), 12, (220, 220, 230), -1)

    # Text
    cv2.putText(frame, f"t={t:.2f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    writer.write(frame)

writer.release()
print(f"Created {out_path}")
print(f"Duration: {duration}s, FPS: {fps}")