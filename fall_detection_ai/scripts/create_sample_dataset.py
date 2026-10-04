"""Create sample dataset để test pipeline."""
import os
from pathlib import Path

# Tạo thư mục
root = Path(__file__).parent.parent / "datasets" / "sample"
img_dir = root / "images"
lbl_dir = root / "labels"
img_dir.mkdir(parents=True, exist_ok=True)
lbl_dir.mkdir(parents=True, exist_ok=True)

# Tạo 5 fake images và labels (chỉ để test verify/visualize scripts)
import numpy as np
import cv2

for i in range(5):
    img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    cv2.imwrite(str(img_dir / f"img_{i:03d}.jpg"), img)
    # bbox normalized: [class, xc, yc, w, h]
    with open(lbl_dir / f"img_{i:03d}.txt", "w") as f:
        if i < 3:
            f.write("0 0.5 0.5 0.2 0.4\n")  # person
        else:
            f.write("1 0.5 0.5 0.4 0.3\n")  # fall

print(f"Created sample at {root}")
print(f"Images: {len(list(img_dir.glob('*.jpg')))}")
print(f"Labels: {len(list(lbl_dir.glob('*.txt')))}")