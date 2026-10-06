from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(20), default="queued", index=True)  # queued|processing|completed|failed
    progress: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    frames_sampled: Mapped[int] = mapped_column(Integer, default=0)
    frames_with_people: Mapped[int] = mapped_column(Integer, default=0)
    peak_people: Mapped[int] = mapped_column(Integer, default=0)
    avg_people: Mapped[float] = mapped_column(Float, default=0.0)

    # {"hardhat_ok": n, "no_hardhat": n, ...} summed over sampled frames
    detections: Mapped[dict] = mapped_column(JSON, default=dict)
    ppe_compliance: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    snapshots: Mapped[list] = mapped_column(JSON, default=list)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    incidents: Mapped[list["Incident"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", order_by="Incident.timestamp_seconds"
    )


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), index=True)
    type: Mapped[str] = mapped_column(String(30), index=True)  # no_hardhat | no_vest | no_mask
    timestamp_seconds: Mapped[float] = mapped_column(Float)
    frame_index: Mapped[int] = mapped_column(Integer)
    count: Mapped[int] = mapped_column(Integer, default=1)
    people_in_frame: Mapped[int] = mapped_column(Integer, default=0)

    analysis: Mapped[Analysis] = relationship(back_populates="incidents")
