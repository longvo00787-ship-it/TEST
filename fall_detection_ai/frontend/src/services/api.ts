// API service layer

import type {
  ProcessResult,
  ModelInfo,
  EngineStats,
  FallEventRecord,
  EvaluationResult,
  TrainingJob,
  VideoAnalysisResult,
  DatasetInfo,
} from '../types/api'

const API_BASE = '/api'

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  return res.json()
}

export const api = {
  health: () => request<{ status: string; model_loaded: boolean; pose_loaded: boolean; device: string }>('/health'),

  modelInfo: () => request<ModelInfo>('/model-info'),
  metrics: () => request<EngineStats>('/metrics'),
  systemStats: () => request<{ total_fall_events: number; total_detection_logs: number; engine_stats: EngineStats }>('/system/stats'),

  events: (limit = 100, source?: string) =>
    request<{ events: FallEventRecord[]; total: number }>(
      `/events?limit=${limit}${source ? `&source=${source}` : ''}`
    ),

  // Image
  detectImage: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/detect/image`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Detect image failed')
    return res.json() as Promise<{ result: ProcessResult; annotated_image_base64: string }>
  },

  // Video
  analyzeVideo: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    form.append('save_output', 'true')
    const res = await fetch(`${API_BASE}/detect/video`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Analyze video failed')
    return res.json() as Promise<VideoAnalysisResult>
  },

  // Webcam
  startWebcam: (index = 0) =>
    request<{ ok: boolean; already_running?: boolean; index?: number }>(
      `/detect/webcam/start?index=${index}`,
      { method: 'POST' }
    ),
  stopWebcam: () => request<{ ok: boolean }>('/detect/webcam/stop', { method: 'POST' }),
  webcamFrameUrl: () => `${API_BASE}/detect/webcam/frame?t=${Date.now()}`,
  webcamLatest: () => request<{ active: boolean; result?: ProcessResult }>('/detect/webcam/latest'),

  // Training
  startTraining: (config: {
    data?: string
    model?: string
    epochs?: number
    batch?: number
    imgsz?: number
    lr?: number
    device?: string
  }) => request<{ ok: boolean; status: string }>('/training/start', {
    method: 'POST',
    body: JSON.stringify({
      model: 'yolov8n.pt',
      epochs: 50,
      batch: 16,
      imgsz: 640,
      lr: 0.001,
      device: 'auto',
      ...config,
    }),
  }),
  trainingStatus: () =>
    request<{ jobs: TrainingJob[]; latest: TrainingJob | null }>('/training/status'),

  // Evaluation
  evaluation: (method?: string) =>
    request<{ results: EvaluationResult[] }>(`/evaluation${method ? `?method=${method}` : ''}`),
  runYoloEval: (weights = 'auto') =>
    request<{ ok: boolean; error?: string }>(`/evaluation/run-yolo?weights=${weights}`, { method: 'POST' }),
  experiments: () =>
    request<{ by_method: Record<string, EvaluationResult>; all: EvaluationResult[] }>(
      '/experiments/comparison'
    ),

  // Dataset
  datasetInfo: () => request<DatasetInfo>('/dataset/info'),
  listVideos: () => request<{ videos: { name: string; size: number }[]; count: number }>('/dataset/videos'),
  uploadVideo: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/dataset/upload-video`, { method: 'POST', body: form })
    if (!res.ok) throw new Error('Upload failed')
    return res.json()
  },
}