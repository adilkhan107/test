"""Background analysis. One worker thread: videos are analyzed one at a time."""
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Analysis, Incident, utcnow
from app.services import storage
from app.services.video_analyzer import VideoError, analyze_video

log = logging.getLogger("nirmaanai.jobs")
_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="analysis")

MAX_ACTIVE = 5  # queued + processing; extra uploads are rejected


def submit(analysis_id: int, path: Path) -> None:
    _executor.submit(_run, analysis_id, path)


def recover_stuck_jobs() -> None:
    """After a restart, jobs left queued/processing can never finish."""
    with SessionLocal() as db:
        stuck = db.scalars(select(Analysis).where(Analysis.status.in_(["queued", "processing"]))).all()
        for a in stuck:
            a.status, a.error = "failed", "Server restarted before analysis finished. Upload the video again."
        db.commit()


def _run(analysis_id: int, path: Path) -> None:
    db = SessionLocal()
    try:
        a = db.get(Analysis, analysis_id)
        if a is None:  # deleted while queued
            return
        a.status = "processing"
        db.commit()

        last = {"p": -1}

        def on_progress(p: int) -> None:
            if p - last["p"] >= 2:
                last["p"] = p
                a.progress = p
                db.commit()

        result = analyze_video(path, on_progress)

        names = [
            storage.save_snapshot(analysis_id, i, s["image"]) for i, s in enumerate(result.snapshots)
        ]
        a.snapshots = [
            {"file": n, "timestamp_seconds": s["timestamp"], "violations": s["violations"]}
            for n, s in zip(names, result.snapshots)
        ]
        a.duration_seconds = result.duration_seconds
        a.frames_sampled = result.frames_sampled
        a.frames_with_people = result.frames_with_people
        a.peak_people = result.peak_people
        a.avg_people = result.avg_people
        a.detections = result.detections
        a.ppe_compliance = result.compliance
        a.risk_score = result.risk_score
        a.risk_level = result.risk_level
        db.add_all(
            Incident(
                analysis_id=analysis_id,
                type=i["type"],
                timestamp_seconds=i["timestamp"],
                frame_index=i["frame"],
                count=i["count"],
                people_in_frame=i["people"],
            )
            for i in result.incidents
        )
        a.status, a.progress, a.completed_at = "completed", 100, utcnow()
        db.commit()
    except VideoError as e:
        _fail(db, analysis_id, str(e))
    except Exception:
        log.exception("Analysis %s failed", analysis_id)
        _fail(db, analysis_id, "Analysis failed on the server. Try again or use a different video.")
    finally:
        path.unlink(missing_ok=True)  # raw footage is not kept
        db.close()


def _fail(db, analysis_id: int, message: str) -> None:
    db.rollback()
    a = db.get(Analysis, analysis_id)
    if a:
        a.status, a.error, a.completed_at = "failed", message, utcnow()
        db.commit()
