"""Оркестрація: цикл Observe -> Reason -> Validate -> Act -> Update -> Evaluate."""

import time
from collections.abc import Callable
from .environment import lookup_http_status, list_status_class
from .errors import DecisionError
from .reasoning import get_decision
from .state import AgentState
from .validator import validate_decision

MAX_STEPS = 6
MAX_LLM_CALLS = 8

DecideFn = Callable[[str, list[str], int, int], dict]


def execute_action(decision: dict, state: AgentState) -> str | None:
    """Dispatcher: перетворює перевірене рішення на виклик конкретної Python-функції."""
    action = decision["action"]
    args = decision["arguments"]

    if action == "lookup_http_status":
        return lookup_http_status(args["code"])
    if action == "list_status_class":
        return list_status_class(args["status_class"])
    if action == "finish":
        state.final_answer = args["answer"]
        state.finished = True
        state.stop_reason = "finish"
        return None

    raise DecisionError(f"no handler for action {action!r}")


def print_step(record: dict) -> None:
    print(f"\nSTEP {record['step']}")
    print(f"  ACTION:   {record['action']} {record['arguments'] or ''}")
    if record.get("decision_summary"):
        print(f"  DECISION: {record['decision_summary']}")
    if record["observation"] is not None:
        print(f"  OBSERVATION: {record['observation']}")


def run_agent(
    goal: str,
    decide: DecideFn = get_decision,
    max_steps: int = MAX_STEPS,
    max_llm_calls: int = MAX_LLM_CALLS,
) -> AgentState:
    """Виконує цикл агента до досягнення мети або вичерпання лімітів."""
    state = AgentState(goal=goal)

    while not state.finished:
        # EVALUATE (бюджет кроків)
        if state.step >= max_steps:
            state.finished = True
            state.stop_reason = "max_steps"
            state.final_answer = (
                f"Агент зупинився: вичерпано ліміт кроків ({max_steps}) без фінальної відповіді."
            )
            break

        # EVALUATE (бюджет звернень до LLM)
        if state.llm_calls >= max_llm_calls:
            state.finished = True
            state.stop_reason = "max_llm_calls"
            state.final_answer = (
                f"Агент зупинився: вичерпано ліміт викликів моделі ({max_llm_calls})."
            )
            break

        state.step += 1
        record: dict = {"step": state.step}
        decision: dict | None = None
        started = time.perf_counter()

        try:
            state.llm_calls += 1  # OBSERVE + REASON
            decision = decide(state.goal, state.observations, state.step, max_steps)
            validate_decision(decision)  # VALIDATE
            observation = execute_action(decision, state)  # ACT
            record.update(
                action=decision["action"],
                arguments=decision["arguments"],
                decision_summary=decision.get("decision_summary", ""),
            )
        except DecisionError as exc:
            # Помилка стає спостереженням, і модель отримує шанс виправитися
            observation = f"ERROR: {exc}"
            record.update(
                action="rejected",
                arguments=None,
                decision_summary="",
                rejected=decision,
            )

        record["observation"] = observation
        record["seconds"] = round(time.perf_counter() - started, 2)
        state.trace.append(record)

        if observation is not None:
            state.observations.append(observation)  # UPDATE STATE

        print_step(record)

    return state
