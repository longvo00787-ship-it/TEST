"""
Auto-annotate images bằng YOLO pretrained - hỗ trợ bootstrap dataset.
Lưu ý: Đây là pre-labeling tool, cần review lại trước khi train.
"""
import argparse
from pathlib import Path
import cv2
from tqdm import tqdm

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False


CLASS_MAP = {
    "person": 0,
    "fall": 1,  # chưa có class fall trong pretrained - user cần label thủ công
}


def auto_annotate(
    images_dir: str,
    labels_dir: str,
    model: str = "yolov8n.pt",
    conf: float = 0.4,
):
    if not ULTRALYTICS_AVAILABLE:
        print("ultralytics not available")
        return

    images_dir = Path(images_dir)
    labels_dir = Path(labels_dir)
    labels_dir.mkdir(parents=True, exist_ok=True)

    yolo = YOLO(model)

    files = sorted([f for f in images_dir.iterdir()
                    if f.suffix.lower() in (".jpg", ".jpeg", ".png")])
    print(f"Annotating {len(files)} images")

    for img_path in tqdm(files):
        results = yolo.predict(str(img_path), conf=conf, classes=[0], verbose=False)
        if len(results) == 0:
            continue
        r = results[0]
        h, w = r.orig_shape
        label_path = labels_dir / f"{img_path.stem}.txt"
        with open(label_path, "w") as f:
            for box in r.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                xc = ((x1 + x2) / 2) / w
                yc = ((y1 + y2) / 2) / h
                bw = (x2 - x1) / w
                bh = (y2 - y1) / h
                f.write(f"0 {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")

    print(f"Done. Labels saved to {labels_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--model", default="yolov8n.pt")
    parser.add_argument("--conf", type=float, default=0.4)
    args = parser.parse_args()
    auto_annotate(args.images, args.labels, args.model, args.conf)


if __name__ == "__main__":
    main()