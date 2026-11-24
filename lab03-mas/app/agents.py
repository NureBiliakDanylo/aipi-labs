"""LLM agents of the Nom-Nom-Save bug triage team.
The model is passed as a parameter to support real Gemini models and offline ScriptedLlm doubles in tests.
"""

from google.adk import Agent
from google.adk.models.base_llm import BaseLlm
from .schemas import Classification, ImpactAnalysis, ReproductionInfo, TriageVerdict

LANGUAGE = (
    "Write all textual descriptions, summaries, rationales, and comments in Ukrainian; "
    "keep technical terms (HTTP methods, endpoints, JSON keys, status codes) in English."
)


def build_agents(model: BaseLlm | str) -> dict[str, Agent]:
    """Instantiate the 4 specialized LLM agents for the bug triage workflow."""

    classifier = Agent(
        name="classifier",
        model=model,
        description="Classifies Nom-Nom-Save REST API bug reports by component and category.",
        instruction=f"""
You are a senior system analyst in the Nom-Nom-Save food rational consumption platform.
Nom-Nom-Save REST API manages surplus food offers (lots), orders, payments, and authentication.
Your task is to analyze the user bug report and classify it into:
1. component: strictly one of ["auth", "orders", "products", "billing"].
2. category: strictly one of ["Functional", "Security", "Performance", "Usability"].
3. title: concise defect title (5-12 words).
4. summary: technical summary of the root failure symptom (1-3 sentences).
5. suggested_severity: initial severity estimate ["Critical", "High", "Medium", "Low"].

Previous lead feedback (empty on first draft):
{{feedback?}}

Do not write reproduction steps or calculate financial blast radius; that is the responsibility of other agents.
{LANGUAGE}
""",
        output_schema=Classification,
        output_key="classification",
    )

    reproducer = Agent(
        name="reproducer",
        model=model,
        description="Extracts precise steps to reproduce, HTTP method, endpoint, and status codes.",
        instruction=f"""
You are a QA automation and bug reproduction specialist for the Nom-Nom-Save REST API.
Bug report:
{{request}}

Classification:
{{classification}}

Your task:
1. Formulate 2 to 6 concrete, numbered steps to reproduce the defect (steps_to_reproduce).
2. Identify the HTTP method (GET, POST, PUT, PATCH, DELETE).
3. Identify the target endpoint (e.g. /api/v1/orders/reserve).
4. Provide sample request_payload (or 'None').
5. Specify expected_status (HTTP status code, e.g. 200, 201, 400).
6. Specify actual_status (HTTP status code observed, e.g. 500, 403, 200).

Do not change the API component or assess business loss; focus strictly on reproduction fidelity.
{LANGUAGE}
""",
        output_schema=ReproductionInfo,
        output_key="reproduction",
    )

    impact_analyst = Agent(
        name="impact_analyst",
        model=model,
        description="Assesses business, financial, and security impacts on the Nom-Nom-Save platform.",
        instruction=f"""
You are a business and security risk analyst for the Nom-Nom-Save platform.
Bug report:
{{request}}

Classification:
{{classification}}

Your task:
1. business_impact: strictly one of ["Data Loss", "Availability", "Financial", "Reputational"].
2. blast_radius: strictly one of ["Isolated", "Single Partner", "System-wide", "Public"].
3. security_risk: explain security/data integrity risk or state 'None'.
4. affected_stakeholders: list affected groups (e.g. ['Customers', 'Partner Bakeries', 'Support']).
5. financial_risk_score: integer from 1 (negligible) to 5 (critical financial loss or double spending).

Do not write reproduction steps or change the API component; focus strictly on impact analysis.
{LANGUAGE}
""",
        output_schema=ImpactAnalysis,
        output_key="impact",
    )

    triage_lead = Agent(
        name="triage_lead",
        model=model,
        description="Team lead and critic: validates consistency, assigns severity and priority, approves or requests revision.",
        instruction=f"""
You are the QA Triage Lead for the Nom-Nom-Save backend team.
Inspect the reports from your team:
Classification:
{{classification}}

Reproduction:
{{reproduction}}

Impact Analysis:
{{impact}}

Rules for decision:
1. Return APPROVE only if:
   - Reproduction steps are concrete (>= 2 steps) with valid expected/actual status codes.
   - Assigned severity is strictly from ["Critical", "High", "Medium", "Low"].
   - Assigned priority is strictly from ["P1", "P2", "P3", "P4"].
   - If financial_risk_score >= 4 or business_impact in ["Data Loss", "Financial"] with blast_radius != "Isolated", severity MUST be "Critical" or "High", and priority "P1" or "P2".
   - There are no contradictions between component, endpoint, and impact.
2. Otherwise return REVISE with 1 to 4 concrete actionable comments for revision.
3. Provide a clear technical justification in triage_rationale.

{LANGUAGE}
""",
        output_schema=TriageVerdict,
        output_key="verdict",
    )

    return {
        "classifier": classifier,
        "reproducer": reproducer,
        "impact_analyst": impact_analyst,
        "triage_lead": triage_lead,
    }
