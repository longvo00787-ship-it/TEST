import { Camera, ScanFace, Users, Activity, Zap, BellRing } from 'lucide-react'

const steps = [
  {
    icon: Camera,
    title: 'Camera / Video Input',
    desc: 'Realtime webcam stream hoặc video file (.mp4/.avi/.mov) được đưa vào pipeline. Mỗi frame được lấy mẫu với FPS đồng bộ.',
  },
  {
    icon: ScanFace,
    title: 'YOLO Person Detection',
    desc: 'Ultralytics YOLO (yolov8n hoặc model đã train) detect bounding box người. Sử dụng class=0 (person) trong COCO dataset.',
  },
  {
    icon: Users,
    title: 'Person Tracking',
    desc: 'ByteTrack tích hợp trong YOLO duy trì ID ổn định cho mỗi người qua các frame. Lịch sử bbox + features theo thời gian được lưu.',
  },
  {
    icon: Activity,
    title: 'Pose Estimation',
    desc: 'YOLO-Pose trích xuất 17 keypoints (nose, shoulders, elbows, hips, knees, ankles) + bbox. Hỗ trợ pose-based features.',
  },
  {
    icon: Zap,
    title: 'Feature Extraction',
    desc: 'Tính các đặc trưng: body angle, torso angle, bbox ratio (w/h), vertical displacement, velocity, acceleration.',
  },
  {
    icon: Activity,
    title: 'Posture Classification',
    desc: 'Phân loại tư thế từ features: standing / sitting / lying / falling / unknown. Không dựa vào 1 điều kiện duy nhất.',
  },
  {
    icon: BellRing,
    title: 'Temporal Fall Detection',
    desc: 'Phân tích chuỗi thời gian (window 1.5s): vertical drop + body angle transition + speed → fall probability. Cần ≥3 frames liên tiếp có score cao để xác nhận.',
  },
  {
    icon: BellRing,
    title: 'Alert + Database',
    desc: 'Sự kiện té ngã được ghi vào DB (SQLite) cùng timestamp, latency, confidence. Dashboard và banner cảnh báo realtime.',
  },
]

export default function Architecture() {
  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">AI Architecture</h2>
        <p className="text-sm text-gray-400 mt-1">
          Pipeline chi tiết từ input đến alert. Mỗi bước đều có trong source code và được giải thích trong đồ án.
        </p>
      </div>

      <div className="card">
        <div className="space-y-5">
          {steps.map((s, i) => (
            <div key={i} className="flex items-start gap-4 pb-5 border-b border-dark-700/50 last:border-b-0">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 rounded-xl bg-cyan-500/10 border border-cyan-500/30 flex items-center justify-center text-cyan-300">
                  <s.icon className="w-6 h-6" />
                </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs px-2 py-0.5 rounded bg-dark-700 text-gray-300 font-mono">
                    Step {i + 1}
                  </span>
                  <h3 className="text-base font-semibold text-gray-100">{s.title}</h3>
                </div>
                <p className="text-sm text-gray-400 mt-2 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="card border-cyan-500/30 bg-cyan-500/5">
        <h3 className="text-sm font-semibold text-cyan-100 mb-3">Research Method (cho thuyết trình)</h3>
        <ol className="text-sm text-cyan-100/90 space-y-2 list-decimal pl-5 leading-relaxed">
          <li>
            <b>Dataset collection:</b> Upload video thật (webcam/online datasets). Mỗi clip chứa các hoạt động: walking, standing, sitting, lying, falling.
          </li>
          <li>
            <b>Data synchronization:</b> Extract frames đồng bộ FPS, lưu metadata (source, timestamp, person count).
          </li>
          <li>
            <b>Annotation:</b> Gán nhãn YOLO format (class, x_center, y_center, width, height normalized).
          </li>
          <li>
            <b>YOLO training:</b> Fine-tune YOLOv8 trên dataset. Augmentation mặc định (flip, mosaic, mixup). Lưu best.pt + last.pt.
          </li>
          <li>
            <b>Pose extraction:</b> YOLO-Pose lấy 17 keypoints cho mỗi người.
          </li>
          <li>
            <b>Posture classification:</b> Rule-based kết hợp ratio + body angle + hip_rel_y. ML classifier optional (Random Forest / XGBoost / LSTM).
          </li>
          <li>
            <b>Temporal fall detection:</b> Phân tích window 1.5s, kết hợp posture + vertical displacement + velocity + temporal confirmation.
          </li>
          <li>
            <b>Evaluation:</b> Precision, Recall, mAP@50, mAP@50:95, F1-score, False Positive, False Negative, Alert Latency. Tất cả từ run thực tế.
          </li>
          <li>
            <b>Realtime deployment:</b> FastAPI backend + React dashboard. Webcam streaming MJPEG, WebSocket optional.
          </li>
        </ol>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">False Positive Reduction Strategy</h3>
        <ul className="text-sm text-gray-300 space-y-2 list-disc pl-5">
          <li>
            <b>Không chỉ dựa vào posture horizontal:</b> Một người nằm nghỉ trên giường cũng có bbox ratio lớn nhưng KHÔNG có rapid downward movement.
          </li>
          <li>
            <b>Vertical displacement check:</b> Fall chỉ được confirm khi có sự thay đổi bbox height đáng kể trong window thời gian.
          </li>
          <li>
            <b>Speed threshold:</b> Nếu velocity quá thấp → giảm fall probability (likely lying/sitting bình thường).
          </li>
          <li>
            <b>Posture history check:</b> Nếu posture = lying từ đầu window, không có transition → giảm 90% fall probability.
          </li>
          <li>
            <b>Temporal confirmation:</b> Cần ≥3 frames liên tiếp có score vượt threshold → mới alert.
          </li>
          <li>
            <b>Cooldown 10s:</b> Tránh spam cùng một event nhiều lần.
          </li>
        </ul>
      </div>
    </div>
  )
}