"""Alternative architecture: Coordinator agent with sub_agents in mode='single_turn'.
Here the LLM coordinator dynamically decides which expert sub-agents to invoke.
"""

from google.adk import Agent
from google.adk.models.base_llm import BaseLlm
from .agents import LANGUAGE


def build_coordinator(model: BaseLlm | str) -> Agent:
    """Build a coordinator agent coordinating specialized sub-agents."""

    def expert(name: str, description: str, focus: str) -> Agent:
        return Agent(
            name=name,
            model=model,
            description=description,
            mode="single_turn",
            instruction=f"""
You are a {focus} for the Nom-Nom-Save food rational consumption platform REST API.
Answer the delegated triage request concisely and concretely, max 6 bullet points.
{LANGUAGE}
""",
        )

    experts = [
        expert(
            "classifier_expert",
            "Classifies REST API component (auth, orders, products, billing) and defect category.",
            "REST API system analyst",
        ),
        expert(
            "reproducer_expert",
            "Formulates precise reproduction steps, HTTP method, endpoint, and status codes.",
            "QA automation reproduction engineer",
        ),
        expert(
            "impact_expert",
            "Evaluates business, financial, and security impacts (blast radius, financial loss 1-5).",
            "business and security risk analyst",
        ),
        expert(
            "triage_expert",
            "Assigns final technical severity (Critical..Low) and priority (P1..P4) with rationale.",
            "senior QA triage lead",
        ),
    ]

    return Agent(
        name="coordinator",
        model=model,
        instruction=f"""
You coordinate a team of bug triage experts: classifier_expert, reproducer_expert, impact_expert, triage_expert.
For the user's Nom-Nom-Save bug report:
1. Call classifier_expert to categorize the API component and failure type.
2. Call reproducer_expert to construct minimal reproduction steps and HTTP call details.
3. Call impact_expert to assess platform blast radius and financial/security risk.
4. Call triage_expert to assign final severity and scheduling priority.
Synthesize all expert outputs into one clear, cohesive bug triage report.
Do not invent expert findings yourself; pass focused requests to each expert.
Call each expert at most once.
{LANGUAGE}
""",
        sub_agents=experts,
    )
