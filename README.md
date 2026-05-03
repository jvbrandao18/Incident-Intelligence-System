# Incident Intelligence System

Incident Intelligence System is a small FastAPI backend that receives technical incidents, classifies them with deterministic rules, stores the result in SQLite, and helps find similar historical incidents.

## What is it?

It is an API-first incident triage service for backend and operations scenarios.

The API can:

- create classified incidents
- list and retrieve incidents
- find similar historical incidents
- return basic incident metrics
- expose API and database health

This version does not use LLMs or external paid APIs. Classification is deterministic and based on transparent rules.

## Why was it built?

Incident triage often starts with the same questions:

- What kind of issue is this?
- How urgent is it?
- What is the probable root cause?
- What should the team check next?
- Have we seen something similar before?

This project was built to automate that first triage pass in a way that is easy to inspect, test, and explain. It shows practical backend engineering through API design, validation, persistence, service boundaries, tests, Docker support, and clear documentation.

## How does it work?

A client sends an incident with `title`, `description`, `service`, and `environment`.

The classifier scans the incident text using deterministic token and phrase rules. It assigns:

- `category`: `RPA`, `Database`, `API`, `Authentication`, `Infrastructure`, or `Unknown`
- `priority`: `low`, `medium`, `high`, or `critical`
- `probable_root_cause`
- `recommended_action`
- `confidence`
- `trace`, explaining which rules matched

The classified incident is stored in SQLite through SQLAlchemy. Similarity search compares token overlap between the target incident and historical incidents, then returns matches with a `similarity_score`.

### Main technologies

- Python
- FastAPI
- Pydantic
- SQLAlchemy
- SQLite
- Pytest
- Docker

### API endpoints

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/incidents` | Create, classify, and store an incident |
| `GET` | `/incidents` | List incidents |
| `GET` | `/incidents/{incident_id}` | Retrieve one incident |
| `GET` | `/incidents/{incident_id}/similar` | Return similar historical incidents |
| `GET` | `/metrics` | Return totals by category and common root causes |
| `GET` | `/health` | Return API and database health |

### Example usage

```bash
curl -X POST http://localhost:8000/incidents \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Production API returns 502",
    "description": "Checkout endpoint returns 502 from gateway for customers.",
    "service": "checkout-api",
    "environment": "production"
  }'
```

Example trace:

```json
[
  "category:api_contract_or_gateway_failure",
  "category_keywords:api,endpoint,502,gateway",
  "priority:production_context",
  "confidence:production_context"
]
```

### Project structure

```text
app/
  main.py                 FastAPI application setup
  database.py             SQLAlchemy engine, session, and table initialization
  models/incident.py      SQLAlchemy incident model
  schemas/incident.py     Pydantic request and response schemas
  routers/                HTTP endpoints
  services/               Classification, persistence, metrics, and similarity logic
samples/incidents.json    Demo incidents covering multiple categories
scripts/load_sample_data.py
tests/                    Unit and API tests
```

## How do I run it?

### Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open the interactive API docs:

```text
http://localhost:8000/docs
```

### Load sample data

```bash
python scripts/load_sample_data.py
```

### Run with Docker

```bash
docker compose up --build
```

The API will be available at:

```text
http://localhost:8000
```

### Tests and validation

```bash
pytest
```

If your local Windows temp directory has restrictive permissions:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'; pytest tests -p no:cacheprovider
```
