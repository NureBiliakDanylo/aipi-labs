"""Multi-agent Bug Report Triage System for Nom-Nom-Save REST API on Google ADK 2.x Workflow."""

import os
from google.adk import Workflow
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.models.base_llm import BaseLlm
from google.adk.workflow import JoinNode
from google.genai import types

from .agents import build_agents
from .nodes import format_check, gate, intake, publish, reject

MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def build_workflow(model: BaseLlm | str) -> Workflow:
    """Build the multi-agent graph workflow for bug report triage."""
    a = build_agents(model)
    reviews = JoinNode(name="reviews")

    return Workflow(
        name="triage_team",
        max_concurrency=2,
        edges=[
            ("START", intake),
            (intake, {"ok": a["classifier"], "reject": reject}),
            (a["classifier"], (a["reproducer"], a["impact_analyst"])),
            (a["reproducer"], reviews),
            (a["impact_analyst"], reviews),
            (reviews, a["triage_lead"], format_check),
            (format_check, {"ok": gate, "fix": a["classifier"]}),
            (gate, {"revise": a["classifier"], "publish": publish}),
        ],
    )


root_agent = build_workflow(
    Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3))
)
app = App(root_agent=root_agent, name="app")
