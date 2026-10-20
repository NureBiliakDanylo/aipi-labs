"""Guardrail"""

from .errors import DecisionError

ALLOWED_ACTIONS: dict[str, set[str]] = {
    "lookup_http_status": {"code"},
    "list_status_class": {"status_class"},
    "finish": {"answer"},
}


def validate_decision(decision: dict) -> None:
    """Перевіряє коректність рішення моделі відповідно до білого списку."""
    if not isinstance(decision, dict):
        raise DecisionError("decision must be a JSON object")

    action = decision.get("action")
    if action not in ALLOWED_ACTIONS:
        raise DecisionError(f"unknown action: {action!r}")

    arguments = decision.get("arguments")
    if not isinstance(arguments, dict):
        raise DecisionError("arguments must be a JSON object")

    missing = ALLOWED_ACTIONS[action] - arguments.keys()
    if missing:
        raise DecisionError(f"missing arguments for {action}: {sorted(missing)}")

    for key in ALLOWED_ACTIONS[action]:
        value = arguments[key]
        if not isinstance(value, str) or not value.strip():
            raise DecisionError(f"argument {key!r} must be a non-empty string")
