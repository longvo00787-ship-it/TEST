// API types

export interface Detection {
  person_id: number
  bbox: [number, number, number, number]
  confidence: number
  posture: string
  posture_confidence: number
  fall_probability: number
  fall_event: boolean
  alert_latency: number | null
}

export interface ProcessResult {
  timestamp: number
  fps: number
  inference_ms: number
  detections: Detection[]
  fall_event: boolean
  alert_latency: number | null
  model_loaded: boolean
  pose_loaded: boolean
  method: string
}

export interface ModelInfo {
  detect_model: string | null
  pose_model: string | null
  default_detect_model: string
  pose_model_default: string
  trained_model_path: string
  trained_model_exists: boolean
  model_loaded: boolean
  pose_loaded: boolean
  device: string
  method: string
}

export interface EngineStats {
  total_detections: number
  total_fall_events: number
  false_alarms: number
  fps: number
  inference_ms: number
  avg_inference_ms: number
  avg_alert_latency: number | null
  min_alert_latency: number | null
  max_alert_latency: number | null
  model_loaded: boolean
  pose_loaded: boolean
  method: string
  device: string
}

export interface FallEventRecord {
  id: number
  person_id: number
  timestamp: string
  confidence: number
  posture: string
  source: string
  latency: number | null
  video_path: string | null
  bbox: string | null
  fall_probability: number | null
}

export interface EvaluationResult {
  id: number
  timestamp: string
  model_name: string
  method: string
  precision: number | null
  recall: number | null
  map50: number | null
  map50_95: number | null
  f1_score: number | null
  accuracy: number | null
  false_positive: number | null
  false_negative: number | null
  avg_latency: number | null
  num_samples: number | null
  notes: string | null
}

export interface TrainingJob {
  id: number
  started_at: string
  finished_at: string | null
  status: string
  model_name: string
  epochs: number
  batch_size: number
  imgsz: number
  learning_rate: number
  device: string
  data_yaml: string | null
  final_map50: number | null
  final_map50_95: number | null
  final_precision: number | null
  final_recall: number | null
  weights_path: string | null
}

export interface TimelineEntry {
  frame: number
  time_s: number
  person_id: number
  posture: string
  fall_probability: number
}

export interface VideoAnalysisResult {
  success: boolean
  video_info: {
    opened: boolean
    fps: number
    width: number
    height: number
    total_frames: number
    duration_s: number
    path: string
  }
  total_frames: number
  fall_events: Array<{
    frame: number
    time_s: number
    person_id: number
    confidence: number
    latency: number | null
  }>
  timeline: TimelineEntry[]
  output_video_path: string | null
  upload_path: string
}

export interface DatasetInfo {
  train: { raw_videos: number }
  val: { raw_videos: number }
  test: { raw_videos: number }
  train_images: number
  val_images: number
  test_images: number
  raw_videos: number
}