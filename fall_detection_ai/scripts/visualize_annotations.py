"""
Visualize YOLO annotations - kiểm tra labels trước khi train.
"""
import argparse
import cv2
import numpy as np
from pathlib import Path


CLASS_NAMES = {0: "person", 1: "fall"}
COLORS = {0: (0, 255, 0), 1: (0, 0, 255)}


def draw_box(img, x1, y1, x2, y2, label, color):
    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
    cv2.putText(img, label, (int(x1), int(max(y1 - 6, 12))),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


def visualize(images_dir: str, labels_dir: str, output_dir: str = None, num_samples: int = 20):
    images_dir = Path(images_dir)
    labels_dir = Path(labels_dir)
    if output_dir:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    image_files = sorted([
        f for f in images_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ])
    if num_samples:
        image_files = image_files[:num_samples]

    for img_path in image_files:
        img = cv2.imread(str(img_path))
        if img is None:
            continue
        h, w = img.shape[:2]
        label_path = labels_dir / f"{img_path.stem}.txt"
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) != 5:
                        continue
                    cls, xc, yc, bw, bh = map(float, parts)
                    cls = int(cls)
                    xc *= w; yc *= h; bw *= w; bh *= h
                    x1 = xc - bw / 2; y1 = yc - bh / 2
                    x2 = xc + bw / 2; y2 = yc + bh / 2
                    label = CLASS_NAMES.get(cls, f"cls{cls}")
                    color = COLORS.get(cls, (255, 255, 0))
                    draw_box(img, x1, y1, x2, y2, label, color)

        if out_dir:
            cv2.imwrite(str(out_dir / img_path.name), img)
        else:
            cv2.imshow("annotation", img)
            cv2.waitKey(0)

    if not out_dir:
        cv2.destroyAllWindows()
    else:
        print(f"Saved {len(image_files)} visualizations to {out_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--num", type=int, default=20)
    args = parser.parse_args()
    visualize(args.images, args.labels, args.output, args.num)


if __name__ == "__main__":
    main()