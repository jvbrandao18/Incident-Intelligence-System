from app.schemas.incident import IncidentCreate
from app.services.classifier import classify_incident


def test_classifies_database_incident_as_high_priority() -> None:
    result = classify_incident(
        IncidentCreate(
            title="Production database timeout",
            description="SQL query timeout and connection pool waits are causing customer impact.",
            service="orders-db",
            environment="production",
        )
    )

    assert result.category == "Database"
    assert result.priority == "high"
    assert result.confidence >= 0.88
    assert any(item.startswith("category:") for item in result.trace)


def test_unknown_incident_uses_fallback_guidance() -> None:
    result = classify_incident(
        IncidentCreate(
            title="Unexpected behavior",
            description="A user reported something unusual but there are no logs or technical details yet.",
        )
    )

    assert result.category == "Unknown"
    assert result.priority == "medium"
    assert result.confidence == 0.35
    assert "category:no_rule_matched" in result.trace


def test_critical_priority_wins_over_other_priority_keywords() -> None:
    result = classify_incident(
        IncidentCreate(
            title="Production outage",
            description="The payment API is down for all users and the checkout service is unavailable.",
        )
    )

    assert result.category == "API"
    assert result.priority == "critical"


def test_non_production_context_does_not_trigger_high_priority_or_confidence_boost() -> None:
    result = classify_incident(
        IncidentCreate(
            title="Non-prod database timeout",
            description="A development SQL query timeout happened during a test run.",
            service="orders-db",
            environment="non-prod",
        )
    )

    assert result.category == "Database"
    assert result.priority == "medium"
    assert result.confidence == 0.88
    assert "confidence:production_context" not in result.trace


def test_short_keywords_match_tokens_not_substrings() -> None:
    result = classify_incident(
        IncidentCreate(
            title="Job update issue",
            description="A scheduled update failed after a configuration change, with no database errors.",
        )
    )

    assert result.category == "Database"
    assert "db" not in next(item for item in result.trace if item.startswith("category_keywords:"))
