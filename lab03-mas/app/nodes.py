"""Deterministic nodes of the workflow graph: validation, format guards, routing, and report generation."""

import re
from google.adk import Context, Event

MAX_DRAFTS = 3
MAX_REQUEST_CHARS = 2000
MIN_REQUEST_CHARS = 15

ALLOWED_COMPONENTS = {"auth", "orders", "products", "billing"}
ALLOWED_CATEGORIES = {"Functional", "Security", "Performance", "Usability"}
ALLOWED_SEVERITIES = {"Critical", "High", "Medium", "Low"}
ALLOWED_PRIORITIES = {"P1", "P2", "P3", "P4"}


def as_text(node_input) -> str:
    """Extract plain text from user message or string representation."""
    if hasattr(node_input, "parts"):
        return "".join(p.text or "" for p in node_input.parts or [])
    return str(node_input or "")


def intake(ctx: Context, node_input) -> Event:
    """Validate incoming bug report and initialize session state."""
    text = as_text(node_input).strip()
    ctx.state["drafts"] = 0
    ctx.state["feedback"] = ""
    ctx.state["format_issues"] = []

    if len(text) < MIN_REQUEST_CHARS:
        return Event(
            route="reject",
            output=f"Запит занадто короткий ({len(text)} симв.). Опишіть баг щонайменше одним повним реченням (від {MIN_REQUEST_CHARS} символів)."
        )

    if len(text) > MAX_REQUEST_CHARS:
        return Event(
            route="reject",
            output=f"Запит довший за {MAX_REQUEST_CHARS} символів ({len(text)} симв.). Будь ласка, скоротіть опис дефекту."
        )

    # Check for minimal semantic content (at least 3 words)
    words = [w for w in re.split(r"\s+", text) if len(w) > 1]
    if len(words) < 3:
        return Event(
            route="reject",
            output="Запит не містить зрозумілого опису симптомів дефекту. Вкажіть дію та спостережувану проблему."
        )

    ctx.state["request"] = text
    return Event(route="ok", output=text)


def format_issues(state: dict) -> list[str]:
    """Mandatory deterministic verification according to Variant 7 specifications.
    
    Checks:
    - severity is from allowed set (Critical, High, Medium, Low)
    - priority is from allowed set (P1, P2, P3, P4)
    - presence of concrete steps to reproduce (>= 2 steps)
    - component and category from allowed sets
    - valid endpoint format (/api/...)
    """
    issues = []
    classification = state.get("classification") or {}
    reproduction = state.get("reproduction") or {}
    verdict = state.get("verdict") or {}

    # 1. Classification checks
    comp = classification.get("component")
    if comp not in ALLOWED_COMPONENTS:
        issues.append(f"Неприпустимий або відсутній компонент API '{comp}'. Дозволені: {sorted(ALLOWED_COMPONENTS)}.")

    cat = classification.get("category")
    if cat not in ALLOWED_CATEGORIES:
        issues.append(f"Неприпустима категорія дефекту '{cat}'. Дозволені: {sorted(ALLOWED_CATEGORIES)}.")

    # 2. Reproduction checks
    steps = reproduction.get("steps_to_reproduce") or []
    if len(steps) < 2:
        issues.append(f"Потрібно щонайменше 2 конкретні кроки відтворення (отримано {len(steps)}).")

    endpoint = str(reproduction.get("endpoint", "")).strip()
    if not endpoint or not endpoint.startswith("/api/"):
        issues.append(f"Ендпоінт повинен починатися з '/api/' (отримано '{endpoint}').")

    # 3. Verdict checks (Severity & Priority from allowed sets)
    sev = verdict.get("severity")
    if sev not in ALLOWED_SEVERITIES:
        issues.append(f"Severity '{sev}' не належить до дозволеної множини {sorted(ALLOWED_SEVERITIES)}.")

    prio = verdict.get("priority")
    if prio not in ALLOWED_PRIORITIES:
        issues.append(f"Priority '{prio}' не належить до дозволеної множини {sorted(ALLOWED_PRIORITIES)}.")

    return issues


def format_check(ctx: Context, node_input) -> Event:
    """Deterministic guardrail: validates triage format before approving or cycling."""
    ctx.state["drafts"] = ctx.state.get("drafts", 0) + 1

    # Update state with the incoming verdict if provided
    if isinstance(node_input, dict):
        ctx.state["verdict"] = node_input

    current_state = ctx.state.to_dict() if hasattr(ctx.state, "to_dict") else dict(ctx.state)
    issues = format_issues(current_state)

    if issues and ctx.state["drafts"] < MAX_DRAFTS:
        ctx.state["feedback"] = "Виправте порушення формату: " + "; ".join(issues)
        return Event(route="fix", output=issues)

    ctx.state["format_issues"] = issues
    return Event(route="ok", output=node_input)


def gate(ctx: Context, node_input) -> Event:
    """Decision gate: inspects lead verdict and iteration count limit."""
    verdict = node_input or ctx.state.get("verdict") or {}
    decision = verdict.get("decision") if isinstance(verdict, dict) else getattr(verdict, "decision", None)

    if decision == "APPROVE":
        ctx.state["stop_reason"] = "approved"
        return Event(route="publish", output=verdict)

    if ctx.state.get("drafts", 0) >= MAX_DRAFTS:
        ctx.state["stop_reason"] = "max_drafts"
        return Event(route="publish", output=verdict)

    # REVISE requested
    ctx.state["stop_reason"] = "revise"
    comments = verdict.get("comments", []) if isinstance(verdict, dict) else getattr(verdict, "comments", [])
    ctx.state["feedback"] = "; ".join(comments) if comments else "Потрібне доопрацювання узгодженості тріажу."
    return Event(route="revise", output=verdict)


def render_report(state: dict) -> str:
    """Render comprehensive Markdown bug triage report from session state."""
    classification = state.get("classification") or {}
    reproduction = state.get("reproduction") or {}
    impact = state.get("impact") or {}
    verdict = state.get("verdict") or {}

    title = classification.get("title") or "Звіт тріажу баг-репорту Nom-Nom-Save"
    comp = classification.get("component", "unknown")
    cat = classification.get("category", "unknown")
    summary = classification.get("summary", "")

    steps = reproduction.get("steps_to_reproduce") or []
    method = reproduction.get("http_method", "POST")
    endpoint = reproduction.get("endpoint", "/api/v1/...")
    payload = reproduction.get("request_payload", "None")
    exp_status = reproduction.get("expected_status", 200)
    act_status = reproduction.get("actual_status", 500)

    biz_impact = impact.get("business_impact", "Availability")
    blast = impact.get("blast_radius", "System-wide")
    sec_risk = impact.get("security_risk", "None")
    stakeholders = impact.get("affected_stakeholders") or []
    fin_score = impact.get("financial_risk_score", 1)

    dec = verdict.get("decision", "APPROVE")
    sev = verdict.get("severity", "Medium")
    prio = verdict.get("priority", "P3")
    rationale = verdict.get("triage_rationale", "")

    lines = [
        f"# [Тріаж] {title}",
        "",
        f"**Компонент API:** `{comp}` | **Категорія:** `{cat}`",
        f"**Суть дефекту:** {summary}",
        "",
        "## 1. Відтворення дефекту (Reproduction)",
        f"- **HTTP Запит:** `{method} {endpoint}`",
        f"- **Тіло запиту (Payload):** `{payload}`",
        f"- **Очікуваний статус:** `{exp_status}` | **Фактичний статус:** `{act_status}`",
        "",
        "**Кроки відтворення:**",
        *[f"  {i}. {s}" for i, s in enumerate(steps, 1)],
        "",
        "## 2. Оцінка впливу та ризиків (Impact Analysis)",
        f"- **Вплив на бізнес:** {biz_impact}",
        f"- **Радіус ураження (Blast Radius):** {blast}",
        f"- **Фінансовий ризик:** {fin_score}/5",
        f"- **Безпековий ризик:** {sec_risk}",
        f"- **Зачеплені стейкхолдери:** {', '.join(stakeholders) if stakeholders else 'Кінцеві користувачі'}",
        "",
        "## 3. Рішення тріажу (Triage Verdict)",
        f"- **Severity:** **{sev}** | **Priority:** **{prio}**",
        f"- **Рішення:** `{dec}` (після {state.get('drafts', 1)} чернетки/ок, причина зупинки: `{state.get('stop_reason', 'approved')}`)",
        f"- **Обґрунтування:** {rationale}",
    ]

    comments = verdict.get("comments") or []
    if dec != "APPROVE" and comments:
        lines += [
            "",
            "## Зауваження для доопрацювання:",
            *[f"- {c}" for c in comments],
        ]

    issues = state.get("format_issues") or []
    if issues:
        lines += [
            "",
            "## Порушення формату:",
            *[f"- {issue}" for issue in issues],
        ]

    return "\n".join(lines)


def publish(ctx: Context, node_input) -> Event:
    """Terminal publish node: generates final markdown report and persists to state."""
    report = render_report(ctx.state.to_dict() if hasattr(ctx.state, "to_dict") else dict(ctx.state))
    ctx.state["report"] = report
    return Event(message=report, output=report)


def reject(ctx: Context, node_input) -> Event:
    """Terminal reject node: informs caller about invalid input without LLM invocations."""
    msg = f"Запит відхилено: {node_input}"
    return Event(message=msg, output=None)
