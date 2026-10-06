from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    analysis_id: int
    type: str
    timestamp_seconds: float
    frame_index: int
    count: int
    people_in_frame: int


class AnalysisSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    original_filename: str
    status: str
    progress: int
    error: str | None
    duration_seconds: float | None
    ppe_compliance: float | None
    risk_score: int | None
    risk_level: str | None
    peak_people: int
    created_at: datetime
    completed_at: datetime | None


class Snapshot(BaseModel):
    url: str
    timestamp_seconds: float
    violations: int


class AnalysisDetail(AnalysisSummary):
    frames_sampled: int
    frames_with_people: int
    avg_people: float
    detections: dict
    snapshots: list[Snapshot]
    incidents: list[IncidentOut]


class AnalysisCreated(BaseModel):
    id: int
    status: str


class AnalysisList(BaseModel):
    total: int
    items: list[AnalysisSummary]


class DashboardSummary(BaseModel):
    total_analyses: int
    completed: int
    failed: int
    in_progress: int
    avg_compliance: float | None
    total_incidents: int
    risk_distribution: dict[str, int]
    incidents_by_type: dict[str, int]
    trend: list[dict]
    recent: list[AnalysisSummary]


class RiskReport(BaseModel):
    analysis_id: int
    risk_score: int
    risk_level: str
    factors: list[str]
    recommendations: list[str]
