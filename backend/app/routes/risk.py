from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Analysis
from app.schemas import RiskReport
from app.services.risk import explain

router = APIRouter(prefix="/api/risk", tags=["Risk"])


@router.get("/{analysis_id}", response_model=RiskReport)
def risk_report(analysis_id: int, db: Session = Depends(get_db)):
    a = db.get(Analysis, analysis_id)
    if not a:
        raise HTTPException(404, "Analysis not found.")
    if a.status != "completed":
        raise HTTPException(409, "Risk is available once the analysis has completed.")
    factors, advice = explain(a.detections or {}, a.ppe_compliance, a.risk_level or "unknown")
    return RiskReport(
        analysis_id=a.id,
        risk_score=a.risk_score if a.risk_score is not None else 0,
        risk_level=a.risk_level or "unknown",
        factors=factors,
        recommendations=advice,
    )
