import heapq
import logging
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import cv2

from app.config import settings
from app.services.risk import compute_risk

log = logging.getLogger("nirmaanai.analyzer")

# model class name (lowercase) -> internal key
CLASS_MAP = {
    "person": "people",
    "hardhat": "hardhat",
    "no-hardhat": "no_hardhat",
    "safety vest": "vest",
    "no-safety vest": "no_vest",
    "mask": "mask",
    "no-mask": "no_mask",
}
# required PPE name -> violation key
VIOLATION_KEYS = {"hardhat": "no_hardhat", "vest": "no_vest", "mask": "no_mask"}

_model = None
_model_lock = threading.Lock()


def get_model():
    """Load the YOLO model once, on first use."""
    global _model
    with _model_lock:
        if _model is None:
            from huggingface_hub import hf_hub_download
            from ultralytics import YOLO

            weights = hf_hub_download(
                repo_id=settings.model_repo,
                filename=settings.model_filename,
                revision=settings.model_revision,
            )
            _model = YOLO(weights)
            log.info("Model loaded from %s", settings.model_repo)
    return _model


class VideoError(Exception):
    """Raised for problems the uploader can understand (bad file, too long...)."""


def probe_video(path: Path) -> tuple[float, float]:
    """Return (fps, duration_seconds) or raise VideoError."""
    cap = cv2.VideoCapture(str(path))
    try:
        if not cap.isOpened():
            raise VideoError("This file could not be read as a video.")
        fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
        frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        if frames <= 0:
            raise VideoError("This video has no readable frames.")
        duration = frames / fps
    finally:
        cap.release()
    if duration > settings.max_video_seconds:
        raise VideoError(
            f"Video is {duration / 60:.1f} min long; the limit is {settings.max_video_seconds / 60:.0f} min."
        )
    return fps, duration


@dataclass
class AnalysisResult:
    duration_seconds: float = 0.0
    frames_sampled: int = 0
    frames_with_people: int = 0
    peak_people: int = 0
    avg_people: float = 0.0
    detections: dict = field(default_factory=dict)
    compliance: float | None = None
    risk_score: int | None = None
    risk_level: str = "unknown"
    incidents: list[dict] = field(default_factory=list)
    snapshots: list[dict] = field(default_factory=list)  # {"image": bytes, "timestamp": s, "violations": n}


def analyze_video(
    path: Path,
    on_progress: Callable[[int], None] | None = None,
) -> AnalysisResult:
    fps, duration = probe_video(path)
    model = get_model()
    required = [VIOLATION_KEYS[k] for k in VIOLATION_KEYS if k in settings.required_ppe]

    step = max(1, round(fps * settings.sample_every_seconds))
    cap = cv2.VideoCapture(str(path))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1

    totals = {k: 0 for k in set(CLASS_MAP.values())}
    res = AnalysisResult(duration_seconds=round(duration, 2))
    worker_checks = 0
    violation_total = 0
    violation_frames = 0
    peak_violations = 0
    best: list[tuple[int, float, bytes]] = []  # min-heap of (violations, ts, jpg)
    idx = -1

    try:
        while True:
            if not cap.grab():
                break
            idx += 1
            if idx % step:
                continue
            ok, frame = cap.retrieve()
            if not ok:
                continue

            ts = idx / fps
            result = model.predict(frame, imgsz=640, conf=settings.conf_threshold, verbose=False)[0]

            counts = {k: 0 for k in totals}
            for box in result.boxes:
                name = str(result.names[int(box.cls[0])]).lower()
                key = CLASS_MAP.get(name)
                if key:
                    counts[key] += 1

            res.frames_sampled += 1
            for k, v in counts.items():
                totals[k] += v

            people = counts["people"]
            if people:
                res.frames_with_people += 1
                res.peak_people = max(res.peak_people, people)
                # a violation can't affect more workers than are in the frame
                frame_viol = {k: min(counts[k], people) for k in required}
                n_viol = sum(frame_viol.values())
                worker_checks += people * len(required)
                violation_total += n_viol

                if n_viol:
                    violation_frames += 1
                    peak_violations = max(peak_violations, n_viol)
                    for k, c in frame_viol.items():
                        if c and len(res.incidents) < settings.max_incidents_per_video:
                            res.incidents.append(
                                {"type": k, "timestamp": round(ts, 2), "frame": idx, "count": c, "people": people}
                            )
                    if len(best) < settings.max_snapshots or n_viol > best[0][0]:
                        ok_jpg, buf = cv2.imencode(".jpg", result.plot(), [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if ok_jpg:
                            item = (n_viol, round(ts, 2), buf.tobytes())
                            if len(best) < settings.max_snapshots:
                                heapq.heappush(best, item)
                            else:
                                heapq.heapreplace(best, item)

            if on_progress:
                on_progress(min(99, int(idx / total_frames * 100)))
    finally:
        cap.release()

    res.detections = totals
    if res.frames_sampled:
        res.avg_people = round(totals["people"] / res.frames_sampled, 2)
    if worker_checks:
        res.compliance = round(100 * (1 - violation_total / worker_checks), 2)
    ratio = violation_frames / res.frames_with_people if res.frames_with_people else 0.0
    res.risk_score, res.risk_level = compute_risk(res.compliance, ratio, peak_violations)
    res.snapshots = [
        {"image": img, "timestamp": ts, "violations": v}
        for v, ts, img in sorted(best, key=lambda x: x[0], reverse=True)
    ]
    return res
