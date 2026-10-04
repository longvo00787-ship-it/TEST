import { useEffect, useState } from 'react'
import { Database, Upload, FolderOpen, FileVideo } from 'lucide-react'
import { api } from '../services/api'
import type { DatasetInfo } from '../types/api'

export default function Dataset() {
  const [info, setInfo] = useState<DatasetInfo | null>(null)
  const [videos, setVideos] = useState<{ name: string; size: number }[]>([])
  const [uploading, setUploading] = useState(false)
  const [uploadMsg, setUploadMsg] = useState<string | null>(null)

  const refresh = async () => {
    try {
      const [i, v] = await Promise.all([api.datasetInfo(), api.listVideos()])
      setInfo(i)
      setVideos(v.videos)
    } catch (e) {/* */}
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 5000)
    return () => clearInterval(id)
  }, [])

  const onUpload = async (file: File) => {
    setUploading(true)
    setUploadMsg(null)
    try {
      await api.uploadVideo(file)
      setUploadMsg(`Uploaded ${file.name} ✓`)
      await refresh()
    } catch (e: any) {
      setUploadMsg(`Error: ${e.message}`)
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="p-6 space-y-6 overflow-y-auto">
      <div>
        <h2 className="text-2xl font-bold text-gray-100">Dataset Management</h2>
        <p className="text-sm text-gray-400 mt-1">
          Manage raw footage, annotations and train/val/test splits.
        </p>
      </div>

      {!info || info.raw_videos === 0 ? (
        <div className="card border-yellow-500/40 bg-yellow-500/5">
          <div className="flex items-start gap-3">
            <Database className="w-5 h-5 text-yellow-400 mt-0.5" />
            <div>
              <div className="text-yellow-200 font-semibold">Dataset required</div>
              <div className="text-yellow-200/80 text-sm mt-1">
                Upload real video footage to datasets/raw/videos/ via the form below, or copy files directly to
                <code className="mx-1 px-1 py-0.5 bg-dark-800 rounded text-yellow-100">datasets/raw/videos/</code>
                . Then run extract_frames, annotate, split_dataset scripts before training.
              </div>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="text-xs uppercase text-gray-400">Raw Videos</div>
          <div className="text-2xl font-bold text-cyan-300 mt-1">
            {info?.raw_videos ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase text-gray-400">Train Images</div>
          <div className="text-2xl font-bold text-purple-300 mt-1">
            {info?.train_images ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase text-gray-400">Val Images</div>
          <div className="text-2xl font-bold text-gray-100 mt-1">
            {info?.val_images ?? 0}
          </div>
        </div>
        <div className="card">
          <div className="text-xs uppercase text-gray-400">Test Images</div>
          <div className="text-2xl font-bold text-gray-100 mt-1">
            {info?.test_images ?? 0}
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
          <Upload className="w-4 h-4 text-cyan-400" /> Upload Video
        </h3>
        <div className="flex items-center gap-3">
          <input
            type="file"
            accept=".mp4,.avi,.mov,video/*"
            onChange={(e) => {
              const f = e.target.files?.[0]
              if (f) onUpload(f)
            }}
            disabled={uploading}
            className="input"
          />
        </div>
        {uploadMsg && (
          <div className="mt-3 text-sm text-cyan-300">{uploadMsg}</div>
        )}
      </div>

      <div className="card">
        <h3 className="text-sm font-semibold text-gray-200 mb-3 flex items-center gap-2">
          <FolderOpen className="w-4 h-4 text-purple-400" /> Raw Videos
        </h3>
        {videos.length === 0 ? (
          <div className="text-sm text-gray-500">No videos uploaded yet.</div>
        ) : (
          <div className="space-y-2 max-h-72 overflow-y-auto">
            {videos.map(v => (
              <div key={v.name} className="flex items-center justify-between p-3 bg-dark-800 rounded-lg border border-dark-600">
                <div className="flex items-center gap-2">
                  <FileVideo className="w-4 h-4 text-cyan-400" />
                  <div className="text-sm text-gray-100">{v.name}</div>
                </div>
                <div className="text-xs text-gray-400">
                  {(v.size / 1_048_576).toFixed(2)} MB
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card border-cyan-500/30">
        <h3 className="text-sm font-semibold text-gray-200 mb-3">Pipeline</h3>
        <ol className="text-sm text-gray-300 space-y-2 list-decimal pl-5">
          <li>
            Upload raw videos (UI above hoặc copy vào{' '}
            <code className="text-cyan-300">datasets/raw/videos/</code>)
          </li>
          <li>
            Extract frames:{' '}
            <code className="text-cyan-300">
              python scripts/extract_frames.py --input datasets/raw/videos/ --output datasets/processed/ --fps 5
            </code>
          </li>
          <li>
            Annotate (LabelImg / Roboflow) →{' '}
            <code className="text-cyan-300">datasets/train/labels/*.txt</code>
          </li>
          <li>
            Split:{' '}
            <code className="text-cyan-300">
              python scripts/split_dataset.py --images datasets/processed/ --labels datasets/processed/labels/ --output datasets/
            </code>
          </li>
          <li>
            Verify:{' '}
            <code className="text-cyan-300">
              python scripts/verify_annotations.py --images datasets/train/images/ --labels datasets/train/labels/
            </code>
          </li>
          <li>
            Train:{' '}
            <code className="text-cyan-300">
              python -m backend.training.train_yolo --data datasets/data.yaml --epochs 50
            </code>
          </li>
        </ol>
      </div>
    </div>
  )
}