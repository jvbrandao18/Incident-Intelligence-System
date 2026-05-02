import json
from pathlib import Path

from app.database import SessionLocal, init_db
from app.schemas.incident import IncidentCreate
from app.services.incidents import create_incident


def main() -> None:
    init_db()
    sample_file = Path(__file__).resolve().parents[1] / "samples" / "incidents.json"
    payloads = json.loads(sample_file.read_text(encoding="utf-8"))

    db = SessionLocal()
    try:
        for payload in payloads:
            create_incident(db, IncidentCreate(**payload))
    finally:
        db.close()

    print(f"Loaded {len(payloads)} sample incidents.")


if __name__ == "__main__":
    main()
