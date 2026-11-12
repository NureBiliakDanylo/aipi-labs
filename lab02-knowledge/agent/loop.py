"""Головний цикл взаємодії ReAct-агента з базою знань."""
import time
from .state import AgentState, AgentStep
from .validator import validate_decision
from .errors import DecisionError
from .reasoning import get_decision
from kb.tools import KnowledgeTools

def run_agent(goal: str, tools: KnowledgeTools, decision_fn=None, max_steps: int = 8) -> AgentState:
    state = AgentState(goal=goal)
    decide = decision_fn or get_decision
    observations: list[str] = []

    for step_num in range(1, max_steps + 1):
        decision = decide(goal, observations, step_num, max_steps)
        validate_decision(decision)
        action = decision["action"]
        arguments = decision.get("arguments") or decision.get("args", {})
        thought = decision.get("decision_summary") or decision.get("thought", "")

        if action == "finish":
            state.final_answer = arguments["answer"]
            state.status = "SUCCESS"
            state.steps.append(AgentStep(step=step_num, action=action, args=arguments, observation="FINISHED", thought=thought))
            break

        obs = ""
        if action == "search_knowledge":
            obs = tools.search_knowledge(arguments["query"], tag=arguments.get("tag"))
        elif action == "read_note":
            obs = tools.read_note(arguments.get("path") or arguments.get("name", ""))
        elif action == "write_note":
            obs = tools.write_note(arguments["title"], arguments["content"], confirmed=arguments.get("confirmed", False))

        observations.append(obs)
        state.steps.append(AgentStep(step=step_num, action=action, args=arguments, observation=obs, thought=thought))
    else:
        state.status = "MAX_STEPS_EXCEEDED"

    return state
