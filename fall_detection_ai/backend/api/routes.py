"""
FastAPI routes for Fall Detection AI.
"""
import io
import json
import shutil
import base64
import time
import threading
from pathlib import Path
from datetime import datetime
from typing import List, Optional

import cv2
import numpy as np
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from pydantic import BaseModel

from backend.config import (
    PROJECT_ROOT, RUNS_DIR, VIDEO_OUTPUT_DIR, get_device, DATASET_RAW,
    DATASETS_DIR
)
from backend.database.models import (
    FallEvent, EvaluationResult, TrainingJob, DetectionLog, init_db, SessionLocal
)
from backend.utils.video import (
    get_video_info, annotate_frame, save_video_output
)
from backend.inference import FallDetectionEngine

router = APIRouter()

# Global state (đơn giản - production cần dùng dependency injection)
_state = {
    "engine": None,
    "webcam_active": False,
    "webcam_thread": None,
    "latest_frame": None,
    "latest_result": None,
    "lock": threading.Lock(),
}


def get_engine() -> FallDetectionEngine:
    if _state["engine"] is None:
        _state["engine"] = FallDetectionEngine(device=get_device())
    return _state["engine"]


def _serialize_result(result: dict) -> dict:
    """Convert numpy → json-able."""
    if not result:
        return {}
    out = dict(result)
    if "detections" in out:
        out["detections"] = [
            {k: (float(v) if isinstance(v, (np.floating,)) else
                 int(v) if isinstance(v, (np.integer,)) else
                 v) for k, v in d.items()}
            for d in out["detections"]
        ]
    return out


# === Health ===
@router.get("/health")
def health():
    init_db()
    engine = get_engine()
    return {
        "status": "ok",
        "model_loaded": engine.model_loaded,
        "pose_loaded": engine.pose_loaded,
        "device": engine.device,
    }


# === Model info ===
@router.get("/model-info")
def model_info():
    engine = get_engine()
    from backend.config import TRAINED_MODEL_PATH, DEFAULT_DETECT_MODEL, POSE_MODEL
    return {
        "detect_model": str(engine.detector.detect_weights_used) if engine.detector else None,
        "pose_model": str(engine.detector.pose_weights_used) if engine.detector else None,
        "default_detect_model": DEFAULT_DETECT_MODEL,
        "pose_model_default": POSE_MODEL,
        "trained_model_path": str(TRAINED_MODEL_PATH),
        "trained_model_exists": TRAINED_MODEL_PATH.exists() and TRAINED_MODEL_PATH.stat().st_size > 0,
        "model_loaded": engine.model_loaded,
        "pose_loaded": engine.pose_loaded,
        "device": engine.device,
        "method": engine.method,
    }


# === Image detection ===
@router.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(400, "Invalid image")

    engine = get_engine()
    result = engine.process_frame(frame)
    annotated = annotate_frame(
        frame, result["detections"],
        fps=result.get("fps", 0.0),
        inference_ms=result.get("inference_ms", 0.0),
    )
    _, buf = cv2.imencode(".jpg", annotated)
    img_b64 = base64.b64encode(buf.tobytes()).decode("utf-8")

    return {
        "result": _serialize_result(result),
        "annotated_image_base64": img_b64,
    }


# === Video upload + analyze ===
@router.post("/detect/video")
async def detect_video(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    save_output: bool = Form(default=True),
):
    """Upload video, chạy AI, trả về JSON results + đường dẫn video đã annotate."""
    # Lưu file upload
    tmp_dir = VIDEO_OUTPUT_DIR / "uploads"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    ts = int(time.time())
    src_path = tmp_dir / f"upload_{ts}_{file.filename}"
    with open(src_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    info = get_video_info(str(src_path))
    if not info["opened"]:
        raise HTTPException(400, "Cannot open video")

    engine = get_engine()
    engine.reset()

    cap = cv2.VideoCapture(str(src_path))
    fps = info["fps"] or 30.0
    total_frames = info["total_frames"]
    width = info["width"]
    height = info["height"]

    out_path = VIDEO_OUTPUT_DIR / f"annotated_{ts}.mp4"
    annotated_frames: list = []
    timeline: List[dict] = []
    fall_events: List[dict] = []

    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        result = engine.process_frame(frame)

        # Lưu event log nếu fall
        if result["fall_event"]:
            for d in result["detections"]:
                if d.get("fall_event"):
                    latency = d.get("alert_latency")
                    _save_fall_event(
                        person_id=d["person_id"],
                        confidence=d["confidence"],
                        posture=d["posture"],
                        source="video",
                        latency=latency,
                        fall_probability=d["fall_probability"],
                        bbox=d["bbox"],
                        video_path=str(src_path),
                    )
                    fall_events.append({
                        "frame": frame_idx,
                        "time_s": frame_idx / fps,
                        "person_id": d["person_id"],
                        "confidence": d["confidence"],
                        "latency": latency,
                    })

        # Sample timeline mỗi ~0.5s
        if frame_idx % int(max(fps * 0.5, 1)) == 0:
            for det in result["detections"]:
                timeline.append({
                    "frame": frame_idx,
                    "time_s": round(frame_idx / fps, 2),
                    "person_id": det["person_id"],
                    "posture": det["posture"],
                    "fall_probability": round(det["fall_probability"], 3),
                })

        if save_output:
            ann = annotate_frame(
                frame, result["detections"],
                fps=result.get("fps", 0.0),
                inference_ms=result.get("inference_ms", 0.0),
            )
            annotated_frames.append(ann)

        frame_idx += 1

    cap.release()

    if save_output and annotated_frames:
        save_video_output(str(out_path), annotated_frames, fps=fps, width=width, height=height)

    # Log detection cuối
    _save_detection_log(fps=engine.last_fps, inference_ms=engine.last_inference_ms,
                        num_persons=len(result["detections"]) if result else 0,
                        fall_event=any(e.get("fall_event") for e in fall_events))

    return {
        "success": True,
        "video_info": info,
        "total_frames": frame_idx,
        "fall_events": fall_events,
        "timeline": timeline[-500:],  # cap
        "output_video_path": str(out_path) if save_output and out_path.exists() else None,
        "upload_path": str(src_path),
    }


@router.get("/detect/video/download")
def download_video(path: str = Query(...)):
    p = Path(path)
    if not p.exists() or not str(p.resolve()).startswith(str(VIDEO_OUTPUT_DIR.resolve())):
        raise HTTPException(404, "Not found")
    return FileResponse(str(p), media_type="video/mp4", filename=p.name)


# === Webcam ===
class WebcamState:
    def __init__(self):
        self.cap = None
        self.thread = None
        self.active = False
        self.latest_jpg: str | None = None
        self.latest_result: dict | None = None
        self.lock = threading.Lock()


_webcam = WebcamState()


def _webcam_loop(state: WebcamState):
    """Loop đọc webcam và chạy inference."""
    engine = get_engine()
    while state.active:
        ret, frame = state.cap.read()
        if not ret:
            time.sleep(0.05)
            continue
        result = engine.process_frame(frame)
        ann = annotate_frame(
            frame, result["detections"],
            fps=result.get("fps", 0.0),
            inference_ms=result.get("inference_ms", 0.0),
        )
        _, buf = cv2.imencode(".jpg", ann, [cv2.IMWRITE_JPEG_QUALITY, 80])
        with state.lock:
            state.latest_jpg = buf.tobytes()
            state.latest_result = result

        # Save fall events
        if result["fall_event"]:
            for d in result["detections"]:
                if d.get("fall_event"):
                    _save_fall_event(
                        person_id=d["person_id"],
                        confidence=d["confidence"],
                        posture=d["posture"],
                        source="webcam",
                        latency=d.get("alert_latency"),
                        fall_probability=d["fall_probability"],
                        bbox=d["bbox"],
                    )


@router.post("/detect/webcam/start")
def webcam_start(index: int = 0):
    if _webcam.active:
        return {"ok": True, "already_running": True}
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        raise HTTPException(400, f"Cannot open webcam index {index}")
    _webcam.cap = cap
    _webcam.active = True
    _webcam.thread = threading.Thread(target=_webcam_loop, args=(_webcam,), daemon=True)
    _webcam.thread.start()
    return {"ok": True, "index": index}


@router.post("/detect/webcam/stop")
def webcam_stop():
    _webcam.active = False
    if _webcam.cap:
        _webcam.cap.release()
        _webcam.cap = None
    return {"ok": True}


@router.get("/detect/webcam/frame")
def webcam_frame():
    """Trả về frame mới nhất dạng JPEG."""
    if not _webcam.active:
        raise HTTPException(400, "Webcam not active")
    with _webcam.lock:
        if _webcam.latest_jpg is None:
            raise HTTPException(404, "No frame yet")
        return StreamingResponse(io.BytesIO(_webcam.latest_jpg), media_type="image/jpeg")


@router.get("/detect/webcam/latest")
def webcam_latest():
    if not _webcam.active:
        return {"active": False}
    with _webcam.lock:
        return {
            "active": True,
            "result": _serialize_result(_webcam.latest_result),
        }


# === Events / metrics ===
@router.get("/events")
def get_events(limit: int = 100, source: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(FallEvent)
        if source:
            q = q.filter(FallEvent.source == source)
        rows = q.order_by(FallEvent.timestamp.desc()).limit(limit).all()
        return {"events": [r.to_dict() for r in rows], "total": len(rows)}
    finally:
        db.close()


@router.get("/metrics")
def get_metrics():
    engine = get_engine()
    return engine.get_stats()


@router.get("/system/stats")
def system_stats():
    db = SessionLocal()
    try:
        total_events = db.query(FallEvent).count()
        total_det = db.query(DetectionLog).count()
        return {
            "total_fall_events": total_events,
            "total_detection_logs": total_det,
            "engine_stats": get_engine().get_stats(),
        }
    finally:
        db.close()


# === Training ===
class TrainRequest(BaseModel):
    data: Optional[str] = None
    model: str = "yolov8n.pt"
    epochs: int = 50
    batch: int = 16
    imgsz: int = 640
    lr: float = 0.001
    device: str = "auto"


@router.post("/training/start")
def training_start(req: TrainRequest, background: BackgroundTasks):
    from backend.training.train_yolo import train_yolo
    from backend.database.models import TrainingJob

    # Run in background
    def _run():
        result = train_yolo(
            data=req.data or str(DATASETS_DIR / "data.yaml"),
            model=req.model,
            epochs=req.epochs,
            batch=req.batch,
            imgsz=req.imgsz,
            lr=req.lr,
            device=req.device,
        )
        # Sau khi train xong, reload engine để dùng model mới
        if result.get("success"):
            _state["engine"] = None  # force reload

    background.add_task(_run)
    return {"ok": True, "status": "started"}


@router.get("/training/status")
def training_status():
    db = SessionLocal()
    try:
        jobs = db.query(TrainingJob).order_by(TrainingJob.started_at.desc()).limit(10).all()
        return {
            "jobs": [j.to_dict() for j in jobs],
            "latest": jobs[0].to_dict() if jobs else None,
        }
    finally:
        db.close()


# === Evaluation ===
@router.get("/evaluation")
def get_evaluation(method: Optional[str] = None):
    db = SessionLocal()
    try:
        q = db.query(EvaluationResult)
        if method:
            q = q.filter(EvaluationResult.method == method)
        rows = q.order_by(EvaluationResult.timestamp.desc()).limit(20).all()
        return {"results": [r.to_dict() for r in rows]}
    finally:
        db.close()


@router.post("/evaluation/run-yolo")
def run_yolo_eval(background: BackgroundTasks, weights: str = "auto"):
    from backend.evaluation.evaluate_yolo import evaluate_yolo

    if weights == "auto":
        from backend.config import TRAINED_MODEL_PATH
        if not TRAINED_MODEL_PATH.exists():
            return {"ok": False, "error": "Model has not been trained yet."}
        weights = str(TRAINED_MODEL_PATH)

    def _run():
        evaluate_yolo(weights=weights, data=str(DATASETS_DIR / "data.yaml"))
        _state["engine"] = None
    background.add_task(_run)
    return {"ok": True}


# === Helpers ===
def _save_fall_event(person_id, confidence, posture, source, latency, fall_probability, bbox, video_path=None):
    db = SessionLocal()
    try:
        ev = FallEvent(
            person_id=person_id,
            timestamp=datetime.utcnow(),
            confidence=confidence,
            posture=posture,
            source=source,
            latency=latency,
            video_path=video_path,
            bbox=json.dumps(bbox) if bbox else None,
            fall_probability=fall_probability,
        )
        db.add(ev)
        db.commit()
    except Exception as e:
        print(f"[_save_fall_event] {e}")
    finally:
        db.close()


def _save_detection_log(fps, inference_ms, num_persons, fall_event):
    db = SessionLocal()
    try:
        log = DetectionLog(
            timestamp=datetime.utcnow(),
            fps=fps,
            inference_ms=inference_ms,
            num_persons=num_persons,
            fall_event=fall_event,
        )
        db.add(log)
        db.commit()
    except Exception:
        pass
    finally:
        db.close()


# === Datasets ===
@router.get("/dataset/info")
def dataset_info():
    """Thông tin dataset hiện tại."""
    info = {}
    for split, path in [("train", DATASET_RAW), ("val", DATASET_RAW), ("test", DATASET_RAW)]:
        info[split] = {
            "raw_videos": len(list(DATASET_RAW.glob("*.mp4"))) + len(list(DATASET_RAW.glob("*.avi"))),
        }
    # Count actual images
    info["train_images"] = len(list((DATASETS_DIR / "train" / "images").glob("*.*"))) if (DATASETS_DIR / "train" / "images").exists() else 0
    info["val_images"] = len(list((DATASETS_DIR / "val" / "images").glob("*.*"))) if (DATASETS_DIR / "val" / "images").exists() else 0
    info["test_images"] = len(list((DATASETS_DIR / "test" / "images").glob("*.*"))) if (DATASETS_DIR / "test" / "images").exists() else 0
    info["raw_videos"] = len(list(DATASET_RAW.glob("*.*")))
    return info


@router.get("/dataset/videos")
def list_videos():
    files = []
    for ext in ["*.mp4", "*.avi", "*.mov"]:
        for f in DATASET_RAW.glob(ext):
            files.append({"name": f.name, "size": f.stat().st_size})
    return {"videos": files, "count": len(files)}


@router.post("/dataset/upload-video")
async def upload_video(file: UploadFile = File(...)):
    dst = DATASET_RAW / file.filename
    with open(dst, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"ok": True, "path": str(dst)}


# === Experiment comparison ===
@router.get("/experiments/comparison")
def experiments_comparison():
    db = SessionLocal()
    try:
        results = db.query(EvaluationResult).order_by(EvaluationResult.timestamp.desc()).limit(50).all()
        # Group by method
        by_method: dict = {}
        for r in results:
            by_method.setdefault(r.method, []).append(r.to_dict())
        # Latest per method
        latest_per_method = {}
        for m, lst in by_method.items():
            latest_per_method[m] = lst[0]
        return {"by_method": latest_per_method, "all": [r.to_dict() for r in results]}
    finally:
        db.close()