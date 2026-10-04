"""
Extract frames from videos.
"""
import argparse
import cv2
from pathlib import Path
from tqdm import tqdm


def extract(input_dir: str, output_dir: str, fps: float = 5.0, ext: str = "jpg"):
    inp = Path(input_dir)
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    videos = list(inp.glob("*.mp4")) + list(inp.glob("*.avi")) + list(inp.glob("*.mov"))
    print(f"Found {len(videos)} videos")

    for v in videos:
        cap = cv2.VideoCapture(str(v))
        if not cap.isOpened():
            print(f"Cannot open {v}")
            continue
        vf = cap.get(cv2.CAP_PROP_FPS) or 30.0
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        step = max(int(vf / fps), 1)

        idx = 0
        out_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % step == 0:
                fn = out / f"{v.stem}_frame{idx:06d}.{ext}"
                cv2.imwrite(str(fn), frame)
                out_count += 1
            idx += 1
        cap.release()
        print(f"  {v.name}: {out_count} frames extracted")

    print(f"Done. Output: {output_dir}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--fps", type=float, default=5.0)
    parser.add_argument("--ext", type=str, default="jpg")
    args = parser.parse_args()
    extract(args.input, args.output, args.fps, args.ext)


if __name__ == "__main__":
    main()