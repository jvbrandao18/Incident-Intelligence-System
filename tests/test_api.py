from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_health(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_create_list_and_retrieve_incident(client: TestClient) -> None:
    create_response = client.post(
        "/incidents",
        json={
            "title": "Production API returns 502",
            "description": "Checkout endpoint returns 502 from gateway for customers.",
            "service": "checkout-api",
            "environment": "production",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    assert created["id"] == 1
    assert created["category"] == "API"
    assert created["priority"] == "high"
    assert created["trace"]

    list_response = client.get("/incidents")
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    retrieve_response = client.get("/incidents/1")
    assert retrieve_response.status_code == 200
    assert retrieve_response.json()["title"] == "Production API returns 502"


def test_similar_incidents_and_metrics(client: TestClient) -> None:
    first = client.post(
        "/incidents",
        json={
            "title": "Checkout API gateway timeout",
            "description": "Payment checkout API endpoint returns gateway timeout in production.",
            "service": "checkout-api",
            "environment": "production",
        },
    ).json()
    client.post(
        "/incidents",
        json={
            "title": "Payment API 502 during checkout",
            "description": "Gateway returns 502 from checkout API for payment requests.",
            "service": "checkout-api",
            "environment": "production",
        },
    )

    similar_response = client.get(f"/incidents/{first['id']}/similar")
    assert similar_response.status_code == 200
    similar = similar_response.json()
    assert len(similar) == 1
    assert similar[0]["similarity_score"] > 0

    metrics_response = client.get("/metrics")
    assert metrics_response.status_code == 200
    metrics = metrics_response.json()
    assert metrics["total_incidents"] == 2
    assert metrics["incidents_by_category"]["API"] == 2


def test_missing_incident_returns_404(client: TestClient) -> None:
    response = client.get("/incidents/999")

    assert response.status_code == 404


def test_create_incident_validates_required_detail(client: TestClient) -> None:
    response = client.post(
        "/incidents",
        json={
            "title": "Too short",
            "description": "short",
        },
    )

    assert response.status_code == 422
