import re
from dataclasses import dataclass

from app.schemas.incident import ClassificationResult, IncidentCreate


@dataclass(frozen=True)
class Rule:
    name: str
    category: str
    keywords: tuple[str, ...]
    root_cause: str
    action: str
    confidence: float


CATEGORY_RULES = (
    Rule(
        name="rpa_selector_or_bot_failure",
        category="RPA",
        keywords=("bot", "rpa", "selector", "robot", "queue", "orchestrator", "unattended"),
        root_cause="Automation bot failed because of selector drift, queue errors or runtime instability.",
        action="Check bot logs, validate selectors, inspect queue state and retry with a controlled transaction.",
        confidence=0.86,
    ),
    Rule(
        name="database_connectivity_or_query_failure",
        category="Database",
        keywords=("database", "db", "sql", "query", "deadlock", "timeout", "connection pool", "replication"),
        root_cause="Database connectivity, locking or slow query behavior is affecting the service.",
        action="Inspect database health, connection pool usage, locks, slow queries and recent schema changes.",
        confidence=0.88,
    ),
    Rule(
        name="api_contract_or_gateway_failure",
        category="API",
        keywords=("api", "endpoint", "http", "500", "502", "503", "gateway", "payload", "contract"),
        root_cause="API dependency, gateway or request contract failure is causing errors.",
        action="Check API logs, status codes, payload changes, dependency health and recent deployments.",
        confidence=0.84,
    ),
    Rule(
        name="authentication_or_authorization_failure",
        category="Authentication",
        keywords=("login", "auth", "token", "oauth", "jwt", "permission", "forbidden", "unauthorized", "sso"),
        root_cause="Authentication or authorization configuration is rejecting valid access.",
        action="Validate token expiry, identity provider status, permissions, secrets and recent access policy changes.",
        confidence=0.87,
    ),
    Rule(
        name="infrastructure_resource_or_network_failure",
        category="Infrastructure",
        keywords=("cpu", "memory", "disk", "pod", "container", "node", "network", "dns", "kubernetes", "latency"),
        root_cause="Infrastructure resource pressure or network instability is degrading the system.",
        action="Review resource saturation, node health, network/DNS metrics, scaling events and infrastructure changes.",
        confidence=0.83,
    ),
)

PRIORITY_KEYWORDS = (
    ("critical", ("outage", "down", "unavailable", "data loss", "security breach", "all users", "production down")),
    ("high", ("customer impact", "payment", "sla", "major", "severe")),
    ("medium", ("degraded", "slow", "intermittent", "retry", "partial", "delay", "timeout")),
    (
        "low",
        ("minor", "cosmetic", "warning", "question", "non prod", "non production", "nonprod", "development", "staging", "test"),
    ),
)


def normalize_text(text: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def tokenize(text: str) -> set[str]:
    return set(normalize_text(text).split())


def classify_incident(incident: IncidentCreate) -> ClassificationResult:
    raw_text = " ".join(
        part for part in (incident.title, incident.description, incident.service or "", incident.environment or "") if part
    )
    normalized_text = normalize_text(raw_text)
    tokens = tokenize(raw_text)
    trace: list[str] = []

    matched_rule, matched_keywords = _best_category_rule(normalized_text, tokens)
    if matched_rule:
        category = matched_rule.category
        root_cause = matched_rule.root_cause
        action = matched_rule.action
        confidence = matched_rule.confidence
        trace.append(f"category:{matched_rule.name}")
        trace.append(f"category_keywords:{','.join(matched_keywords)}")
    else:
        category = "Unknown"
        root_cause = "Insufficient incident details to identify a probable technical root cause."
        action = "Collect logs, affected scope, timestamps, recent changes and reproduction steps before escalation."
        confidence = 0.35
        trace.append("category:no_rule_matched")

    production_context = _is_production_context(incident.environment, normalized_text)
    priority, priority_trace = _priority_from_text(normalized_text, tokens, production_context)
    trace.append(priority_trace)

    if production_context:
        confidence = min(confidence + 0.04, 0.97)
        trace.append("confidence:production_context")

    return ClassificationResult(
        category=category,
        priority=priority,
        probable_root_cause=root_cause,
        recommended_action=action,
        confidence=round(confidence, 2),
        trace=trace,
    )


def _best_category_rule(normalized_text: str, tokens: set[str]) -> tuple[Rule | None, list[str]]:
    best_rule: Rule | None = None
    best_keywords: list[str] = []
    for rule in CATEGORY_RULES:
        matched_keywords = [keyword for keyword in rule.keywords if _keyword_matches(keyword, normalized_text, tokens)]
        if len(matched_keywords) > len(best_keywords):
            best_rule = rule
            best_keywords = matched_keywords
    return best_rule, best_keywords


def _priority_from_text(normalized_text: str, tokens: set[str], production_context: bool) -> tuple[str, str]:
    for priority, keywords in PRIORITY_KEYWORDS:
        if any(_keyword_matches(keyword, normalized_text, tokens) for keyword in keywords):
            return priority, f"priority:{priority}_keyword"
    if production_context:
        return "high", "priority:production_context"
    return "medium", "priority:default_medium"


def _keyword_matches(keyword: str, normalized_text: str, tokens: set[str]) -> bool:
    normalized_keyword = normalize_text(keyword)
    if " " in normalized_keyword:
        return f" {normalized_keyword} " in f" {normalized_text} "
    return normalized_keyword in tokens


def _is_production_context(environment: str | None, normalized_text: str) -> bool:
    if " non prod " in f" {normalized_text} " or " non production " in f" {normalized_text} ":
        return False
    env_tokens = tokenize(environment or "")
    if env_tokens.intersection({"nonprod", "development", "staging", "test"}):
        return False
    if " non prod " in f" {normalize_text(environment or '')} ":
        return False
    if env_tokens.intersection({"prod", "production"}):
        return True
    return " production " in f" {normalized_text} "
