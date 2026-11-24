"""Unit tests for deterministic graph nodes and helper functions."""

from app.nodes import (
    ALLOWED_CATEGORIES,
    ALLOWED_COMPONENTS,
    ALLOWED_PRIORITIES,
    ALLOWED_SEVERITIES,
    MAX_DRAFTS,
    format_issues,
    gate,
    intake,
    render_report,
)
from tests.fixtures import (
    APPROVE_VERDICT,
    GOOD_CLASSIFICATION,
    GOOD_IMPACT,
    GOOD_REPRODUCTION,
    REVISE_VERDICT,
)


class MockContext:
    """Mock context object with dictionary state."""
    def __init__(self, initial_state=None):
        self.state = initial_state or {}


def test_intake_valid():
    """Valid bug report initializes state and routes 'ok'."""
    ctx = MockContext()
    event = intake(ctx, "Дефект виникає при спробі замовлення лота через REST API.")
    assert event.actions.route == "ok"
    assert ctx.state["drafts"] == 0
    assert ctx.state["feedback"] == ""
    assert "замовлення лота" in ctx.state["request"]


def test_intake_too_short():
    """Short bug report (< 15 chars) routes 'reject' without LLM."""
    ctx = MockContext()
    event = intake(ctx, "Коротко")
    assert event.actions.route == "reject"
    assert "занадто короткий" in event.output


def test_intake_too_long():
    """Overlong request (> 2000 chars) routes 'reject'."""
    ctx = MockContext()
    event = intake(ctx, "А" * 2050)
    assert event.actions.route == "reject"
    assert "довший за 2000" in event.output


def test_format_issues_clean():
    """Complete and valid state produces 0 format issues."""
    state = {
        "classification": GOOD_CLASSIFICATION,
        "reproduction": GOOD_REPRODUCTION,
        "impact": GOOD_IMPACT,
        "verdict": APPROVE_VERDICT,
    }
    issues = format_issues(state)
    assert issues == []


def test_format_issues_invalid_component_and_category():
    """Unapproved component or category is detected."""
    state = {
        "classification": {
            "component": "unknown_microservice",
            "category": "InvalidCategory",
        },
        "reproduction": GOOD_REPRODUCTION,
        "impact": GOOD_IMPACT,
        "verdict": APPROVE_VERDICT,
    }
    issues = format_issues(state)
    assert any("Неприпустимий або відсутній компонент API" in i for i in issues)
    assert any("Неприпустима категорія дефекту" in i for i in issues)


def test_format_issues_missing_steps_and_bad_endpoint():
    """Fewer than 2 steps or missing /api/ prefix in endpoint are flagged."""
    state = {
        "classification": GOOD_CLASSIFICATION,
        "reproduction": {
            "steps_to_reproduce": ["Лише один крок"],
            "endpoint": "v1/orders",
        },
        "impact": GOOD_IMPACT,
        "verdict": APPROVE_VERDICT,
    }
    issues = format_issues(state)
    assert any("щонайменше 2 конкретні кроки" in i for i in issues)
    assert any("починатися з '/api/'" in i for i in issues)


def test_format_issues_invalid_severity_and_priority():
    """Variant 7 requirement: severity and priority must strictly match allowed sets."""
    state = {
        "classification": GOOD_CLASSIFICATION,
        "reproduction": GOOD_REPRODUCTION,
        "impact": GOOD_IMPACT,
        "verdict": {
            "decision": "APPROVE",
            "severity": "Catastrophic",
            "priority": "P0",
        },
    }
    issues = format_issues(state)
    assert any("Severity 'Catastrophic' не належить" in i for i in issues)
    assert any("Priority 'P0' не належить" in i for i in issues)


def test_gate_approved():
    """APPROVE decision routes 'publish'."""
    ctx = MockContext({"drafts": 1})
    event = gate(ctx, APPROVE_VERDICT)
    assert event.actions.route == "publish"
    assert ctx.state["stop_reason"] == "approved"


def test_gate_revise_within_limit():
    """REVISE decision within limit routes 'revise'."""
    ctx = MockContext({"drafts": 1})
    event = gate(ctx, REVISE_VERDICT)
    assert event.actions.route == "revise"
    assert ctx.state["stop_reason"] == "revise"
    assert "Idempotency-Key" in ctx.state["feedback"]


def test_gate_max_drafts_reached():
    """When drafts reaches MAX_DRAFTS, gate forces 'publish' even if REVISE."""
    ctx = MockContext({"drafts": MAX_DRAFTS})
    event = gate(ctx, REVISE_VERDICT)
    assert event.actions.route == "publish"
    assert ctx.state["stop_reason"] == "max_drafts"


def test_render_report_structure():
    """render_report builds a structured markdown document."""
    state = {
        "classification": GOOD_CLASSIFICATION,
        "reproduction": GOOD_REPRODUCTION,
        "impact": GOOD_IMPACT,
        "verdict": APPROVE_VERDICT,
        "drafts": 1,
        "stop_reason": "approved",
    }
    report = render_report(state)
    assert "# [Тріаж]" in report
    assert "## 1. Відтворення дефекту (Reproduction)" in report
    assert "## 2. Оцінка впливу та ризиків (Impact Analysis)" in report
    assert "## 3. Рішення тріажу (Triage Verdict)" in report
    assert "**Severity:** **Critical**" in report
    assert "**Priority:** **P1**" in report
