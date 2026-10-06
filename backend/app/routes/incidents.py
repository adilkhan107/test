from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Incident
from app.schemas import IncidentOut

router = APIRouter(prefix="/api/incidents", tags=["Incidents"])


@router.get("", response_model=list[IncidentOut])
def list_incidents(
    analysis_id: int | None = None,
    type: str | None = Query(None, pattern="^(no_hardhat|no_vest|no_mask)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = select(Incident).order_by(Incident.id.desc())
    if analysis_id is not None:
        q = q.where(Incident.analysis_id == analysis_id)
    if type:
        q = q.where(Incident.type == type)
    return db.scalars(q.limit(limit).offset(offset)).all()
