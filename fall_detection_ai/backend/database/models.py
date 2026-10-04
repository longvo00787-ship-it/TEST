"""
Database module - SQLAlchemy ORM.
Hỗ trợ SQLite cho demo, có thể chuyển PostgreSQL qua DATABASE_URL.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, create_engine
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from sqlalchemy.pool import StaticPool

from backend.config import DATABASE_URL

Base = declarative_base()


class FallEvent(Base):
    """Lưu sự kiện té ngã."""
    __tablename__ = "fall_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    person_id = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence = Column(Float, nullable=False)
    posture = Column(String(50), nullable=False)
    source = Column(String(50), nullable=False)  # webcam / video / image
    latency = Column(Float, nullable=True)  # alert latency in seconds
    video_path = Column(String(500), nullable=True)
    bbox = Column(String(200), nullable=True)  # JSON string
    fall_probability = Column(Float, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "person_id": self.person_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "confidence": self.confidence,
            "posture": self.posture,
            "source": self.source,
            "latency": self.latency,
            "video_path": self.video_path,
            "bbox": self.bbox,
            "fall_probability": self.fall_probability,
        }


class DetectionLog(Base):
    """Lưu log detection mỗi frame (giới hạn số lượng)."""
    __tablename__ = "detection_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    fps = Column(Float, nullable=True)
    inference_ms = Column(Float, nullable=True)
    num_persons = Column(Integer, default=0)
    fall_event = Column(Boolean, default=False)


class EvaluationResult(Base):
    """Lưu kết quả evaluation."""
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    model_name = Column(String(200), nullable=False)
    method = Column(String(100), nullable=False)  # yolo / rule_based / ml_classifier
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    map50 = Column(Float, nullable=True)
    map50_95 = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    accuracy = Column(Float, nullable=True)
    false_positive = Column(Integer, nullable=True)
    false_negative = Column(Integer, nullable=True)
    avg_latency = Column(Float, nullable=True)
    num_samples = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "model_name": self.model_name,
            "method": self.method,
            "precision": self.precision,
            "recall": self.recall,
            "map50": self.map50,
            "map50_95": self.map50_95,
            "f1_score": self.f1_score,
            "accuracy": self.accuracy,
            "false_positive": self.false_positive,
            "false_negative": self.false_negative,
            "avg_latency": self.avg_latency,
            "num_samples": self.num_samples,
            "notes": self.notes,
        }


class TrainingJob(Base):
    """Lưu trạng thái training job."""
    __tablename__ = "training_jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(50), default="running")  # running / completed / failed
    model_name = Column(String(200), nullable=False)
    epochs = Column(Integer, nullable=False)
    batch_size = Column(Integer, nullable=False)
    imgsz = Column(Integer, nullable=False)
    learning_rate = Column(Float, nullable=False)
    device = Column(String(20), nullable=False)
    data_yaml = Column(String(500), nullable=True)
    final_map50 = Column(Float, nullable=True)
    final_map50_95 = Column(Float, nullable=True)
    final_precision = Column(Float, nullable=True)
    final_recall = Column(Float, nullable=True)
    log = Column(Text, nullable=True)
    weights_path = Column(String(500), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "model_name": self.model_name,
            "epochs": self.epochs,
            "batch_size": self.batch_size,
            "imgsz": self.imgsz,
            "learning_rate": self.learning_rate,
            "device": self.device,
            "data_yaml": self.data_yaml,
            "final_map50": self.final_map50,
            "final_map50_95": self.final_map50_95,
            "final_precision": self.final_precision,
            "final_recall": self.final_recall,
            "weights_path": self.weights_path,
        }


# Engine setup
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Tạo tables nếu chưa có."""
    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()