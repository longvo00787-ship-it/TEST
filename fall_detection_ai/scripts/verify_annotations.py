"""
Verify annotations - check format và số lượng classes.
"""
import argparse
from pathlib import Path
from collections import Counter


def verify(images_dir: str, labels_dir: str, num_classes: int = 2):
    images_dir = Path(images_dir)
    labels_dir = Path(labels_dir)

    image_files = sorted([
        f for f in images_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ])

    issues = []
    class_counts = Counter()
    total_labels = 0
    labeled_images = 0

    for img in image_files:
        label = labels_dir / f"{img.stem}.txt"
        if not label.exists():
            issues.append(f"Missing label: {label.name}")
            continue
        labeled_images += 1
        with open(label) as f:
            for ln, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                parts = line.split()
                if len(parts) != 5:
                    issues.append(f"{label.name}:{ln} - expected 5 cols, got {len(parts)}")
                    continue
                cls, xc, yc, w, h = map(float, parts)
                cls = int(cls)
                if cls < 0 or cls >= num_classes:
                    issues.append(f"{label.name}:{ln} - invalid class {cls}")
                for name, v in [("xc", xc), ("yc", yc), ("w", w), ("h", h)]:
                    if v < 0 or v > 1:
                        issues.append(f"{label.name}:{ln} - {name}={v} out of [0,1]")
                class_counts[cls] += 1
                total_labels += 1

    print(f"Total images: {len(image_files)}")
    print(f"Labeled images: {labeled_images}")
    print(f"Total labels: {total_labels}")
    print(f"Class distribution: {dict(class_counts)}")
    if issues:
        print(f"\nIssues ({len(issues)}):")
        for i in issues[:30]:
            print(f"  - {i}")
        if len(issues) > 30:
            print(f"  ... and {len(issues) - 30} more")
    else:
        print("\nAll annotations look good!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--num-classes", type=int, default=2)
    args = parser.parse_args()
    verify(args.images, args.labels, args.num_classes)


if __name__ == "__main__":
    main()