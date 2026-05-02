from app.models.incident import Incident
from app.services.classifier import tokenize


def incident_text(incident: Incident) -> str:
    return " ".join(
        part
        for part in (
            incident.title,
            incident.description,
            incident.service or "",
            incident.environment or "",
            incident.category,
            incident.probable_root_cause,
        )
        if part
    )


def similarity_score(left: str, right: str) -> float:
    left_tokens = tokenize(left)
    right_tokens = tokenize(right)
    if not left_tokens or not right_tokens:
        return 0.0
    overlap = left_tokens.intersection(right_tokens)
    union = left_tokens.union(right_tokens)
    return round(len(overlap) / len(union), 3)


def find_similar_incidents(target: Incident, candidates: list[Incident], limit: int = 5) -> list[tuple[Incident, float]]:
    target_text = incident_text(target)
    scored = [
        (candidate, similarity_score(target_text, incident_text(candidate)))
        for candidate in candidates
        if candidate.id != target.id
    ]
    return sorted((item for item in scored if item[1] > 0), key=lambda item: item[1], reverse=True)[:limit]
