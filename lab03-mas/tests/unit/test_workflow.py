"""Unit tests for multi-agent graph workflow orchestration using ScriptedLlm."""

import asyncio
from app.agent import build_workflow
from app.nodes import MAX_DRAFTS
from run_cli import run_once
from tests.fixtures import (
    APPROVE_VERDICT,
    BAD_FORMAT_CLASSIFICATION,
    BAD_FORMAT_REPRODUCTION,
    BAD_FORMAT_VERDICT,
    GOOD_CLASSIFICATION,
    GOOD_IMPACT,
    GOOD_REPRODUCTION,
    REQUEST,
    REVISE_VERDICT,
)
from tests.scripted import ScriptedLlm


def run(script: dict, req: str = REQUEST):
    """Helper to execute the workflow once against a ScriptedLlm model."""
    model = ScriptedLlm(model="scripted", script=script)
    result = asyncio.run(run_once(build_workflow(model), req))
    return result, model


def test_approved_on_first_round():
    """Happy path: bug report successfully triaged on the very first round."""
    script = {
        "senior system analyst": [GOOD_CLASSIFICATION],
        "reproduction specialist": [GOOD_REPRODUCTION],
        "security risk analyst": [GOOD_IMPACT],
        "QA Triage Lead": [APPROVE_VERDICT],
    }
    result, model = run(script)
    state = result["state"]

    assert state["stop_reason"] == "approved"
    assert state["drafts"] == 1
    assert "## 1. Відтворення дефекту (Reproduction)" in state["report"]
    assert "## 2. Оцінка впливу та ризиків" in state["report"]
    assert "## 3. Рішення тріажу (Triage Verdict)" in state["report"]
    assert "**Severity:** **Critical**" in state["report"]

    # Verify that all 4 agents were invoked exactly once
    assert model.calls.count("senior system analyst") == 1
    assert model.calls.count("reproduction specialist") == 1
    assert model.calls.count("security risk analyst") == 1
    assert model.calls.count("QA Triage Lead") == 1


def test_revise_loop_then_approve():
    """Feedback loop: triage lead asks for revision, team updates draft and gets approved."""
    script = {
        "senior system analyst": [GOOD_CLASSIFICATION, GOOD_CLASSIFICATION],
        "reproduction specialist": [GOOD_REPRODUCTION, GOOD_REPRODUCTION],
        "security risk analyst": [GOOD_IMPACT, GOOD_IMPACT],
        "QA Triage Lead": [REVISE_VERDICT, APPROVE_VERDICT],
    }
    result, model = run(script)
    state = result["state"]

    assert state["stop_reason"] == "approved"
    assert state["drafts"] == 2
    assert model.calls.count("senior system analyst") == 2
    assert model.calls.count("QA Triage Lead") == 2


def test_loop_is_bounded_by_max_drafts():
    """Bounded loop: when triage lead continuously requests revision, system stops at MAX_DRAFTS."""
    script = {
        "senior system analyst": [GOOD_CLASSIFICATION],
        "reproduction specialist": [GOOD_REPRODUCTION],
        "security risk analyst": [GOOD_IMPACT],
        "QA Triage Lead": [REVISE_VERDICT],
    }
    result, model = run(script)
    state = result["state"]

    assert state["stop_reason"] == "max_drafts"
    assert state["drafts"] == MAX_DRAFTS
    assert model.calls.count("QA Triage Lead") == MAX_DRAFTS


def test_bad_format_recovers_to_approval():
    """Deterministic format check guardrail: invalid format triggers fix loop, then passes."""
    script = {
        "senior system analyst": [BAD_FORMAT_CLASSIFICATION, GOOD_CLASSIFICATION],
        "reproduction specialist": [GOOD_REPRODUCTION, GOOD_REPRODUCTION],
        "security risk analyst": [GOOD_IMPACT, GOOD_IMPACT],
        "QA Triage Lead": [BAD_FORMAT_VERDICT, APPROVE_VERDICT],
    }
    result, model = run(script)
    state = result["state"]

    assert state["drafts"] >= 2
    assert state["stop_reason"] == "approved"


def test_short_request_rejected_without_llm():
    """Intake guardrail: too short input is rejected immediately with 0 LLM calls."""
    model = ScriptedLlm(model="scripted", script={})
    result = asyncio.run(run_once(build_workflow(model), "Баг логіну"))

    assert model.calls == []
    assert any("Запит відхилено" in (r.get("text") or "") for r in result["trace"])


def test_overlong_request_rejected_without_llm():
    """Intake guardrail: overlong input (> 2000 chars) is rejected immediately with 0 LLM calls."""
    model = ScriptedLlm(model="scripted", script={})
    long_request = "Опис дефекту платформи Nom-Nom-Save REST API. " * 70  # ~3200 chars
    result = asyncio.run(run_once(build_workflow(model), long_request))

    assert model.calls == []
    assert any("довший за 2000 символів" in (r.get("text") or "") for r in result["trace"])
