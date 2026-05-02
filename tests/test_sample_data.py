import json
from pathlib import Path

from app.schemas.incident import IncidentCreate
from app.services.classifier import classify_incident


def test_sample_data_is_valid_and_covers_expected_categories() -> None:
    sample_file = Path(__file__).resolve().parents[1] / "samples" / "incidents.json"
    payloads = json.loads(sample_file.read_text(encoding="utf-8"))

    results = [classify_incident(IncidentCreate(**payload)) for payload in payloads]
    categories = {result.category for result in results}

    assert len(payloads) >= 7
    assert {"API", "RPA", "Database", "Authentication", "Infrastructure", "Unknown"}.issubset(categories)
