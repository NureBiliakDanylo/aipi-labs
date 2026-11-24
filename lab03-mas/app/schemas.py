"""Data contracts between agents: each agent returns typed structured data conforming to Pydantic schemas."""

from typing import Literal
from pydantic import BaseModel, Field


class Classification(BaseModel):
    """API component classification and initial categorisation of the bug report."""
    component: str = Field(
        description="Target REST API backend component: auth, orders, products, or billing"
    )
    category: str = Field(
        description="Defect category: Functional, Security, Performance, or Usability"
    )
    title: str = Field(description="Clear and concise title of the defect")
    summary: str = Field(description="Brief technical summary of the observed defect")
    suggested_severity: str = Field(
        description="Initial estimated severity before deep reproduction and impact analysis: Critical, High, Medium, or Low"
    )


class ReproductionInfo(BaseModel):
    """Exact steps to reproduce the bug, including HTTP parameters and status codes."""
    steps_to_reproduce: list[str] = Field(
        description="Step-by-step reproduction sequence, min 2 concrete steps"
    )
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"] = Field(
        description="HTTP method of the failing API call"
    )
    endpoint: str = Field(
        description="API endpoint path (e.g. /api/v1/orders/{id}/reserve)"
    )
    request_payload: str = Field(
        description="Sample HTTP JSON payload or query parameters, or 'None'"
    )
    expected_status: int = Field(
        description="Expected HTTP response status code (e.g. 200, 201, 400)"
    )
    actual_status: int = Field(
        description="Actual HTTP response status code observed (e.g. 500, 403, 200)"
    )


class ImpactAnalysis(BaseModel):
    """Assessment of business, financial, and security impacts on the Nom-Nom-Save platform."""
    business_impact: Literal["Data Loss", "Availability", "Financial", "Reputational"] = Field(
        description="Primary business dimension affected"
    )
    blast_radius: Literal["Isolated", "Single Partner", "System-wide", "Public"] = Field(
        description="Scale of defect propagation across restaurants, stores, and users"
    )
    security_risk: str = Field(
        description="Description of security vulnerabilities, integrity violations, or 'None'"
    )
    affected_stakeholders: list[str] = Field(
        description="Affected platform participants (e.g. ['Customers', 'Partner Bakeries'])"
    )
    financial_risk_score: int = Field(
        ge=1,
        le=5,
        description="1 = negligible loss, 5 = direct revenue/inventory loss or financial theft"
    )


class TriageVerdict(BaseModel):
    """Final triage lead decision, severity/priority assignment, and revision comments."""
    decision: Literal["APPROVE", "REVISE"] = Field(
        description="Decision: APPROVE if reproduction and impact are consistent, REVISE if changes needed"
    )
    severity: str = Field(
        description="Final technical severity from allowed set: Critical, High, Medium, Low"
    )
    priority: str = Field(
        description="Final scheduling priority from allowed set: P1, P2, P3, P4"
    )
    triage_rationale: str = Field(
        description="Technical justification for assigned severity and priority"
    )
    comments: list[str] = Field(
        default_factory=list,
        description="Actionable feedback comments for the analyst/reproducer if REVISE, empty if APPROVE"
    )


class SoloResult(BaseModel):
    """Combined schema for single-agent baseline execution."""
    classification: Classification = Field(description="Component and category classification")
    reproduction: ReproductionInfo = Field(description="Reproduction steps and HTTP details")
    impact: ImpactAnalysis = Field(description="Business and security impact evaluation")
    verdict: TriageVerdict = Field(description="Triage decision, severity, and priority")
