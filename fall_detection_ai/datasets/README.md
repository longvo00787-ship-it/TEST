# Dataset

## Yêu cầu

Đây là đồ án AI nên cần **dataset thật** để train và đánh giá. Hệ thống hỗ trợ pipeline hoàn chỉnh nhưng không tự tạo dữ liệu giả.

## Cấu trúc

```
datasets/
    raw/videos/          # Video gốc (.mp4, .avi, .mov)
    processed/           # Frames sau khi extract (optional)
    annotations/         # Labels YOLO format
    train/
        images/          # Training images
        labels/          # Training labels
    val/
        images/
        labels/
    test/
        images/
        labels/
    data.yaml            # YOLO config
```

## Dataset gợi ý

Một số dataset public có thể dùng cho fall detection:

1. **UR Fall Detection Dataset** - chứa các clip té ngã với nhiều điều kiện
2. **Fall Dataset (Kaggle)** - https://www.kaggle.com/datasets/uttejkumarkandula/fall-detection-dataset
4. **Multiple Cameras Fall Dataset** - đa camera
5. **Custom dataset** - tự thu thập bằng webcam

## Cách chuẩn bị dataset

### 1. Thu thập video

```bash
# Upload video từ webcam (qua API hoặc frontend)
# Hoặc copy trực tiếp vào datasets/raw/videos/
```

### 2. Extract frames

```bash
python scripts/extract_frames.py --input datasets/raw/videos/ --output datasets/processed/ --fps 5
```

### 3. Annotate

Sử dụng tool annotation (Roboflow, CVAT, LabelImg) hoặc script semi-auto trong `scripts/`.

Output format YOLO:
```
<class_id> <x_center> <y_center> <width> <height>
```
Tọa độ normalized [0, 1].

Classes:
- 0: person (standing/walking/sitting/lying bình thường)
- 1: fall (người đang té)

### 4. Split train/val/test

```bash
python scripts/split_dataset.py --input datasets/processed/ --train 0.7 --val 0.2 --test 0.1
```

### 5. Tạo data.yaml

Script sẽ tự tạo `datasets/data.yaml` nếu chưa có.

## Visualize annotations

```bash
python scripts/visualize_annotations.py --images datasets/train/images --labels datasets/train/labels
```

Output sẽ là ảnh có bounding boxes để kiểm tra.

## Training

```bash
python -m backend.training.train_yolo --data datasets/data.yaml --model yolov8n.pt --epochs 50
```

## Lưu ý

- Mỗi video có thể chứa nhiều người → mỗi person 1 bbox, 1 label.
- Person ID được tracking tự động bằng ByteTrack khi chạy inference.
- Dataset lớn hơn = model tốt hơn. Khuyến nghị ≥ 1000 frames cho mỗi class.
- Nếu dataset nhỏ, dùng `yolov8n.pt` và tăng epoch + augmentation.