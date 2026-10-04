# QUICKSTART - Hướng dẫn chạy Fall Detection AI

## 1. Cài đặt dependencies

### Python (Backend)
```bash
pip install -r requirements.txt
```

Lần đầu chạy, ultralytics sẽ tự download YOLO weights (~13MB cho yolov8n).

### Node (Frontend)
```bash
cd frontend
npm install
```

## 2. Chạy hệ thống

### Cách 1: Backend serve cả frontend (đơn giản nhất)
```bash
# Build frontend (chỉ làm 1 lần hoặc khi update code)
cd frontend
npm run build
cd ..

# Start backend
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

Mở browser: http://localhost:8000

### Cách 2: Dev mode (frontend hot-reload)
Terminal 1:
```bash
python -m uvicorn backend.main:app --reload --port 8000
```

Terminal 2:
```bash
cd frontend
npm run dev
```

Mở: http://localhost:5173

### Cách 3: dùng script
```bash
# Windows
start.bat

# Linux/Mac
./start.sh
```

## 3. Sử dụng

### Realtime Webcam
1. Vào trang "Realtime Detection"
2. Chọn camera index (0 = default webcam)
4. Click "Start Camera"
5. Đứng trước camera, di chuyển, ngồi xuống, té
6. Hệ thống sẽ hiển thị:
   - Person ID, bounding box
   - Posture (standing/sitting/lying/falling)
   - Confidence score
   - Fall probability
   - Alert banner khi phát hiện té ngã

### Video Upload
1. Vào trang "Video Analysis"
2. Kéo thả hoặc chọn file video
3. Click "Process Video"
4. Đợi xử lý (10s video ~ 30s với CPU)
5. Xem annotated video, fall events, timeline

### Training
**QUAN TRỌNG:** Cần có dataset thật trước khi train.

1. Upload video vào `datasets/raw/videos/` (qua UI hoặc copy trực tiếp)
2. Extract frames: `python scripts/extract_frames.py --input datasets/raw/videos/ --output datasets/processed/`
3. Annotate (dùng LabelImg hoặc Roboflow)
4. Split: `python scripts/split_dataset.py --images datasets/processed/ --labels datasets/processed/ --output datasets/`
5. Verify: `python scripts/verify_annotations.py --images datasets/train/images/ --labels datasets/train/labels/`
6. Train: `python -m backend.training.train_yolo --data datasets/data.yaml --epochs 50`
7. Sau khi train xong, model `runs/detect/train/weights/best.pt` sẽ được load tự động.

### Evaluation
Sau khi train:
1. Vào trang "Evaluation"
2. Click "Run YOLO Eval"
3. Hệ thống tính precision, recall, mAP50, mAP50-95 từ val set
4. Kết quả hiển thị trên UI + lưu DB

### Fall Detection Evaluation
Đánh giá riêng hệ thống phát hiện té ngã cần labeled fall events:
```bash
# Tạo file labels (xem datasets/README.md)
python -m backend.evaluation.evaluate_fall --weights runs/detect/train/weights/best.pt --annotations path/to/labels.json
```

## 4. Cấu trúc output

```
fall_detection_ai/
├── backend/                 # FastAPI backend
│   ├── api/routes.py        # Endpoints
│   ├── detection/           # YOLO wrapper
│   ├── tracking/            # Person tracking
│   ├── pose/                # Feature extraction
│   ├── classification/      # Posture classification
│   ├── fall_detection/      # Temporal + ML classifier
│   ├── training/            # YOLO training
│   ├── evaluation/          # Metrics
│   ├── database/            # SQLAlchemy models
│   ├── inference.py         # Main pipeline
│   └── main.py              # FastAPI app
├── frontend/                # React + TS
│   ├── src/
│   │   ├── pages/           # Dashboard, Realtime, etc.
│   │   ├── components/      # Sidebar, TopBar, StatCard
│   │   ├── services/api.ts  # API client
│   │   └── types/api.ts     # Types
│   └── dist/                # Build output (served by backend)
├── datasets/
│   ├── raw/videos/          # Video gốc
│   ├── processed/           # Frames
│   ├── annotations/         # Labels
│   ├── train/val/test/      # Splits
│   └── data.yaml            # YOLO config
├── models/                  # Trained weights
├── runs/                    # Training runs, video outputs
├── scripts/                 # extract_frames, split, etc.
└── fall_detection.db        # SQLite database
```

## 5. Demo nhanh

```bash
# Generate sample test video (synthetic)
python scripts/make_test_video.py

# Start backend
python -m uvicorn backend.main:app --port 8000

# Mở browser
# http://localhost:8000
```

Lưu ý: synthetic video không phải người thật nên YOLO không detect được.
Cần video có người thật để demo detection.