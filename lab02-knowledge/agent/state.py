"""Стан агента."""
from dataclasses import dataclass, field

@dataclass
class AgentStep:
    step: int
    action: str
    args: dict
    observation: str
    thought: str = ""

@dataclass
class AgentState:
    goal: str
    steps: list[AgentStep] = field(default_factory=list)
    final_answer: str | None = None
    status: str = "RUNNING"
