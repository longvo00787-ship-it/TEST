"""
Split dataset thành train/val/test.
"""
import argparse
import random
import shutil
from pathlib import Path
from tqdm import tqdm


def split_dataset(images_dir: str, labels_dir: str, output_dir: str,
                  train_ratio: float = 0.7, val_ratio: float = 0.2, test_ratio: float = 0.1,
                  seed: int = 42):
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6

    images_dir = Path(images_dir)
    labels_dir = Path(labels_dir)
    output_dir = Path(output_dir)

    image_files = sorted([
        f for f in images_dir.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ])
    print(f"Found {len(image_files)} images")

    random.Random(seed).shuffle(image_files)

    n = len(image_files)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)
    train_files = image_files[:n_train]
    val_files = image_files[n_train:n_train + n_val]
    test_files = image_files[n_train + n_val:]

    splits = {
        "train": train_files,
        "val": val_files,
        "test": test_files,
    }

    for split, files in splits.items():
        img_out = output_dir / split / "images"
        lbl_out = output_dir / split / "labels"
        img_out.mkdir(parents=True, exist_ok=True)
        lbl_out.mkdir(parents=True, exist_ok=True)
        for img in tqdm(files, desc=split):
            shutil.copy2(img, img_out / img.name)
            label = labels_dir / f"{img.stem}.txt"
            if label.exists():
                shutil.copy2(label, lbl_out / label.name)
        print(f"  {split}: {len(files)} files")

    print(f"Done. Split summary:")
    for split, files in splits.items():
        print(f"  {split}: {len(files)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images", required=True)
    parser.add_argument("--labels", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--train", type=float, default=0.7)
    parser.add_argument("--val", type=float, default=0.2)
    parser.add_argument("--test", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    split_dataset(args.images, args.labels, args.output, args.train, args.val, args.test, args.seed)


if __name__ == "__main__":
    main()