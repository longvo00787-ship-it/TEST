# Fall Detection AI System

Hệ thống phát hiện sự kiện té ngã trong môi trường sống thông minh sử dụng YOLO (Person Detection + Pose Estimation).

## Đề tài

**PHÁT HIỆN SỰ KIỆN TÉ NGÃ TRONG MÔI TRƯỜNG SỐNG THÔNG MINH BẰNG NHẬN DIỆN NGƯỜI VÀ TƯ THẾ VỚI YOLO**

## 1. Problem statement

Té ngã là một trong những nguyên nhân hàng đầu gây chấn thương nghiêm trọng ở người cao tuổi và người sống một mình. Việc phát hiện kịp thời sự kiện té ngã giúp giảm thời gian chờ cấp cứu, hạn chế biến chứng và tăng khả năng sống sót.

Hệ thống cần:
- Phát hiện người trong video/webcam realtime
- Theo dõi nhiều người cùng lúc
- Trích xuất pose (keypoints)
- Phân loại tư thế (standing/sitting/lying/falling)
- Phát hiện sự kiện té ngã dựa trên temporal analysis
- Phát cảnh báo với độ trễ thấp
- Lưu trữ lịch sử sự kiện

## 2. Cấu trúc hệ thống

```
Video/Webcam
    ↓
Frame extraction (OpenCV)
    ↓
YOLO Person Detection (Ultralytics YOLO)
    ↓
Person Tracking (ByteTrack / SORT)
    ↓
Pose Estimation (YOLO Pose / keypoints)
    ↓
Feature Extraction (body angle, ratio, displacement, speed)
    ↓
Posture Classification (rule-based + ML-ready)
    ↓
Temporal Fall Detection (window-based)
    ↓
Fall Probability + Confidence
    ↓
Alert + Database
    ↓
Web Dashboard
```

## 3. Cài đặt

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

## 4. Chạy hệ thống

### Backend
```bash
cd backend
python main.py
# Server: http://localhost:8000
# API docs: http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm run dev
# Dashboard: http://localhost:5173
```

## 5. Dataset

Xem chi tiết tại `datasets/README.md`.

Cấu trúc:
```
datasets/
    raw/videos/         # Video gốc
    processed/          # Frames đã xử lý
    annotations/        # Nhãn YOLO format
    train/              # Train split
    val/                # Validation split
    test/               # Test split
```

Yêu cầu dataset thật để train. Hệ thống hỗ trợ:
- Import video từ webcam
- Upload video
- Annotation tool
- Train/val/test split

## 6. Training YOLO

```bash
cd backend
python -m training.train_yolo --data ../datasets/data.yaml --model yolov8n.pt --epochs 100 --imgsz 640
```

Model sẽ được lưu tại `runs/detect/train/weights/best.pt`.

## 7. Evaluation

```bash
python -m evaluation.evaluate_yolo --weights runs/detect/train/weights/best.pt --data ../datasets/data.yaml
```

Kết quả (precision, recall, mAP50, mAP50-95) sẽ được lưu vào database và hiển thị trên dashboard.

## 8. Fall Detection

Hệ thống hỗ trợ 2 phương pháp:

### Method A: Rule-based
Phân tích posture + vertical movement + body angle + temporal window.

### Method B: ML-based (optional)
Sử dụng Random Forest / XGBoost / LSTM trên feature sequence.
Xem `backend/fall_detection/ml_classifier.py`.

## 9. Công nghệ sử dụng

**Backend:**
- Python 3.10+
- FastAPI
- PyTorch + Ultralytics YOLO
- OpenCV
- NumPy, Pandas, scikit-learn

**Frontend:**
- React 18 + TypeScript
- Tailwind CSS
- Recharts
- Lucide Icons

**Database:** SQLite (có thể chuyển PostgreSQL)

## 10. Đánh giá mô hình

Các metric được tính từ evaluation thực tế:
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **mAP@50** = Mean Average Precision tại IoU=0.5
- **mAP@50:95** = Mean Average Precision trung bình IoU 0.5-0.95
- **F1-score** = 2 × (Precision × Recall) / (Precision + Recall)
- **Alert Latency** = Alert timestamp − Fall occurrence timestamp

Các metric được lưu vào DB và hiển thị trên Dashboard/Evaluation pages.

## 11. Lưu ý quan trọng

- Hệ thống KHÔNG sử dụng random/hard-coded values.
- Mọi số liệu đều từ evaluation/inference thực tế.
- Nếu model chưa train, dashboard hiển thị rõ "Model has not been trained yet."
- Nếu dataset trống, hiển thị "Dataset required before training."
- False Positive Reduction: nằm nghỉ KHÔNG trigger alert té ngã.

## 12. Cấu trúc thư mục

```
fall_detection_ai/
├── backend/
│   ├── main.py
│   ├── api/
│   ├── detection/
│   ├── tracking/
│   ├── pose/
│   ├── classification/
│   ├── fall_detection/
│   ├── training/
│   ├── evaluation/
│   ├── database/
│   └── utils/
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/
│       ├── hooks/
│       └── types/
├── datasets/
├── models/
├── runs/
├── scripts/
├── configs/
├── README.md
└── requirements.txt
```

## 13. License & Citation

Đồ án môn Trí tuệ nhân tạo.