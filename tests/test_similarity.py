from datetime import datetime, timezone

from app.models.incident import Incident
from app.services.similarity import find_similar_incidents, similarity_score


def make_incident(incident_id: int, title: str, description: str, category: str = "API") -> Incident:
    return Incident(
        id=incident_id,
        title=title,
        description=description,
        service="test-service",
        environment="production",
        category=category,
        priority="medium",
        probable_root_cause="API dependency failure",
        recommended_action="Check logs",
        confidence=0.8,
        trace="[]",
        created_at=datetime.now(timezone.utc),
    )


def test_similarity_score_uses_token_overlap() -> None:
    score = similarity_score("api gateway timeout checkout", "checkout api gateway returns 502")

    assert 0 < score < 1


def test_find_similar_incidents_excludes_target_and_sorts() -> None:
    target = make_incident(1, "Checkout API 502", "Gateway timeout during checkout")
    close = make_incident(2, "Checkout API failure", "Gateway returns timeout during payment checkout")
    distant = make_incident(3, "RPA selector issue", "Invoice bot selector cannot find field", "RPA")

    results = find_similar_incidents(target, [target, distant, close], limit=2)

    assert [incident.id for incident, _score in results] == [2, 3]
    assert results[0][1] >= results[1][1]
