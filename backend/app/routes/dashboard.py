from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis, Incident
from app.schemas import DashboardSummary

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def summary(db: Session = Depends(get_db)):
    by_status = dict(db.execute(select(Analysis.status, func.count()).group_by(Analysis.status)).all())
    avg = db.scalar(select(func.avg(Analysis.ppe_compliance)).where(Analysis.status == "completed"))
    risk = dict(
        db.execute(
            select(Analysis.risk_level, func.count())
            .where(Analysis.status == "completed", Analysis.risk_level.is_not(None))
            .group_by(Analysis.risk_level)
        ).all()
    )
    inc = dict(db.execute(select(Incident.type, func.coalesce(func.sum(Incident.count), 0)).group_by(Incident.type)).all())

    trend_rows = db.scalars(
        select(Analysis)
        .where(Analysis.status == "completed", Analysis.ppe_compliance.is_not(None))
        .order_by(Analysis.completed_at.desc())
        .limit(14)
    ).all()
    trend = [
        {"id": a.id, "label": a.original_filename, "compliance": a.ppe_compliance, "risk_score": a.risk_score}
        for a in reversed(trend_rows)
    ]
    recent = db.scalars(select(Analysis).order_by(Analysis.created_at.desc()).limit(5)).all()

    return DashboardSummary(
        total_analyses=sum(by_status.values()),
        completed=by_status.get("completed", 0),
        failed=by_status.get("failed", 0),
        in_progress=by_status.get("queued", 0) + by_status.get("processing", 0),
        avg_compliance=round(avg, 1) if avg is not None else None,
        total_incidents=int(sum(inc.values())),
        risk_distribution=risk,
        incidents_by_type={k: int(v) for k, v in inc.items()},
        trend=trend,
        recent=recent,
    )
