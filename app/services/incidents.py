import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.incident import Incident
from app.schemas.incident import IncidentCreate, IncidentRead
from app.services.classifier import classify_incident


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    classification = classify_incident(payload)
    incident = Incident(
        title=payload.title,
        description=payload.description,
        service=payload.service,
        environment=payload.environment,
        category=classification.category,
        priority=classification.priority,
        probable_root_cause=classification.probable_root_cause,
        recommended_action=classification.recommended_action,
        confidence=classification.confidence,
        trace=json.dumps(classification.trace),
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def list_incidents(db: Session) -> list[Incident]:
    return list(db.scalars(select(Incident).order_by(Incident.created_at.desc(), Incident.id.desc())).all())


def get_incident(db: Session, incident_id: int) -> Incident | None:
    return db.get(Incident, incident_id)


def to_incident_read(incident: Incident) -> IncidentRead:
    return IncidentRead(
        id=incident.id,
        title=incident.title,
        description=incident.description,
        service=incident.service,
        environment=incident.environment,
        category=incident.category,
        priority=incident.priority,
        probable_root_cause=incident.probable_root_cause,
        recommended_action=incident.recommended_action,
        confidence=incident.confidence,
        trace=json.loads(incident.trace),
        created_at=incident.created_at,
    )


def metrics(db: Session) -> dict:
    total = db.scalar(select(func.count()).select_from(Incident)) or 0
    by_category = dict(db.execute(select(Incident.category, func.count()).group_by(Incident.category)).all())
    root_causes = dict(
        db.execute(select(Incident.probable_root_cause, func.count()).group_by(Incident.probable_root_cause)).all()
    )
    return {
        "total_incidents": total,
        "incidents_by_category": by_category,
        "common_root_causes": root_causes,
    }
