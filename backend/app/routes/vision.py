from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis
from app.schemas import AnalysisCreated, AnalysisDetail, AnalysisList, AnalysisSummary
from app.services import jobs, storage
from app.services.video_analyzer import VideoError, probe_video

router = APIRouter(prefix="/api/vision", tags=["Vision"])


def _detail(a: Analysis) -> AnalysisDetail:
    data = AnalysisSummary.model_validate(a).model_dump()
    return AnalysisDetail(
        **data,
        frames_sampled=a.frames_sampled,
        frames_with_people=a.frames_with_people,
        avg_people=a.avg_people,
        detections=a.detections or {},
        snapshots=[
            {
                "url": f"/media/snapshots/{s['file']}",
                "timestamp_seconds": s["timestamp_seconds"],
                "violations": s["violations"],
            }
            for s in (a.snapshots or [])
        ],
        incidents=a.incidents,
    )


@router.post("/analyze", response_model=AnalysisCreated, status_code=202)
async def create_analysis(video: UploadFile = File(...), db: Session = Depends(get_db)):
    active = db.scalar(
        select(func.count()).select_from(Analysis).where(Analysis.status.in_(["queued", "processing"]))
    )
    if active >= jobs.MAX_ACTIVE:
        raise HTTPException(429, "Too many videos are being analyzed. Wait for one to finish.")

    path = await storage.save_upload(video)
    try:
        probe_video(path)
    except VideoError as e:
        path.unlink(missing_ok=True)
        raise HTTPException(400, str(e))

    name = (video.filename or "video")[:255]
    analysis = Analysis(original_filename=name, status="queued")
    db.add(analysis)
    db.commit()
    jobs.submit(analysis.id, path)
    return AnalysisCreated(id=analysis.id, status=analysis.status)


@router.get("/analyses", response_model=AnalysisList)
def list_analyses(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count()).select_from(Analysis))
    rows = db.scalars(select(Analysis).order_by(Analysis.created_at.desc()).limit(limit).offset(offset)).all()
    return AnalysisList(total=total, items=rows)


@router.get("/analyses/{analysis_id}", response_model=AnalysisDetail)
def get_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Analysis not found.")
    return _detail(a)


@router.delete("/analyses/{analysis_id}", status_code=204)
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Analysis not found.")
    if a.status in ("queued", "processing"):
        raise HTTPException(409, "This analysis is still running.")
    storage.delete_snapshots([s["file"] for s in (a.snapshots or [])])
    db.delete(a)
    db.commit()
