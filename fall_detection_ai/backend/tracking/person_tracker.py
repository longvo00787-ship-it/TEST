"""
Person Tracking - quản lý ID và lịch sử per-person.
Tracking chính được YOLO .track() lo (ByteTrack), module này quản lý history.
"""
from collections import defaultdict, deque
from typing import Dict, Deque, List, Any, Optional
import time
import numpy as np


class PersonTrack:
    """Lưu lịch sử theo thời gian của 1 người."""

    def __init__(self, person_id: int, maxlen: int = 300):
        self.person_id = person_id
        self.history: Deque[Dict[str, Any]] = deque(maxlen=maxlen)
        self.first_seen = time.time()
        self.last_seen = time.time()

    def update(self, data: Dict[str, Any]):
        now = time.time()
        data["timestamp"] = now
        self.history.append(data)
        self.last_seen = now

    def is_stale(self, ttl: float = 2.0) -> bool:
        return (time.time() - self.last_seen) > ttl

    def recent(self, n: int = 30) -> List[Dict[str, Any]]:
        return list(self.history)[-n:]

    def get_feature_sequence(self, n: int = 30) -> List[Dict[str, Any]]:
        return self.recent(n)


class PersonTracker:
    """Quản lý nhiều PersonTrack theo person_id."""

    def __init__(self, max_history: int = 300, stale_ttl: float = 2.0):
        self.tracks: Dict[int, PersonTrack] = {}
        self.max_history = max_history
        self.stale_ttl = stale_ttl

    def update(self, detections: List[Dict[str, Any]]):
        """Cập nhật track từ list detections."""
        seen_ids = set()
        for det in detections:
            pid = det.get("person_id", -1)
            if pid < 0:
                continue
            seen_ids.add(pid)
            if pid not in self.tracks:
                self.tracks[pid] = PersonTrack(pid, maxlen=self.max_history)
            self.tracks[pid].update(det)

        # Xóa track stale
        stale = [pid for pid, t in self.tracks.items() if t.is_stale(self.stale_ttl)]
        for pid in stale:
            if pid not in seen_ids:
                del self.tracks[pid]

    def get(self, person_id: int) -> Optional[PersonTrack]:
        return self.tracks.get(person_id)

    def all(self) -> Dict[int, PersonTrack]:
        return dict(self.tracks)

    def active_ids(self) -> List[int]:
        return [pid for pid, t in self.tracks.items() if not t.is_stale(self.stale_ttl)]

    def reset(self):
        self.tracks.clear()