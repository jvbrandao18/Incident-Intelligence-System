from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.incident import MetricsRead
from app.services.incidents import metrics

router = APIRouter(tags=["metrics"])


@router.get("/metrics", response_model=MetricsRead)
def read_metrics(db: Session = Depends(get_db)) -> MetricsRead:
    return MetricsRead(**metrics(db))
