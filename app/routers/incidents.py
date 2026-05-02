from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.incident import IncidentCreate, IncidentRead, SimilarIncident
from app.services.incidents import create_incident, get_incident, list_incidents, to_incident_read
from app.services.similarity import find_similar_incidents

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.post("", response_model=IncidentRead, status_code=201)
def create(payload: IncidentCreate, db: Session = Depends(get_db)) -> IncidentRead:
    return to_incident_read(create_incident(db, payload))


@router.get("", response_model=list[IncidentRead])
def list_all(db: Session = Depends(get_db)) -> list[IncidentRead]:
    return [to_incident_read(incident) for incident in list_incidents(db)]


@router.get("/{incident_id}", response_model=IncidentRead)
def retrieve(incident_id: int, db: Session = Depends(get_db)) -> IncidentRead:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")
    return to_incident_read(incident)


@router.get("/{incident_id}/similar", response_model=list[SimilarIncident])
def similar(
    incident_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> list[SimilarIncident]:
    incident = get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident not found")

    candidates = list_incidents(db)
    results = find_similar_incidents(incident, candidates, limit=limit)
    return [
        SimilarIncident(**to_incident_read(candidate).model_dump(), similarity_score=score)
        for candidate, score in results
    ]
