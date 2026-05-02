from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class IncidentCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    service: str | None = Field(default=None, max_length=120)
    environment: str | None = Field(default=None, max_length=80)


class ClassificationResult(BaseModel):
    category: str
    priority: str
    probable_root_cause: str
    recommended_action: str
    confidence: float = Field(..., ge=0, le=1)
    trace: list[str]


class IncidentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    service: str | None
    environment: str | None
    category: str
    priority: str
    probable_root_cause: str
    recommended_action: str
    confidence: float
    trace: list[str]
    created_at: datetime


class SimilarIncident(IncidentRead):
    similarity_score: float = Field(..., ge=0, le=1)


class MetricsRead(BaseModel):
    total_incidents: int
    incidents_by_category: dict[str, int]
    common_root_causes: dict[str, int]


class HealthRead(BaseModel):
    status: str
    database: str
