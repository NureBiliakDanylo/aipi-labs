"""Guardrail: модель пропонує, програма вирішує (Лістинг 1.19 МВ)."""
from .errors import DecisionError

ALLOWED_ACTIONS: dict[str, dict[str, set[str]]] = {
    "search_knowledge": {
        "required": {"query"},
        "optional": {"tag"},
    },
    "read_note": {
        "required": {"path"},
        "optional": {"name"},  # сумісність
    },
    "write_note": {
        "required": {"title", "content"},
        "optional": {"confirmed"},
    },
    "finish": {
        "required": {"answer"},
        "optional": set(),
    },
}

def validate_decision(decision: dict) -> None:
    if not isinstance(decision, dict):
        raise DecisionError("Рішення має бути JSON-об'єктом")
    action = decision.get("action")
    if not action or not isinstance(action, str):
        raise DecisionError("Поле 'action' обов'язкове і має бути рядком")
    if action not in ALLOWED_ACTIONS:
        raise DecisionError(f"unknown action: {action!r}")
    
    # Підтримка і "arguments" (за стандартом МВ), і "args" (якщо модель згенерувала скорочено)
    arguments = decision.get("arguments")
    if arguments is None:
        arguments = decision.get("args")
    if not isinstance(arguments, dict):
        raise DecisionError("arguments must be a JSON object")

    spec = ALLOWED_ACTIONS[action]
    
    # Для read_note підтримуємо path або name
    if action == "read_note" and "name" in arguments and "path" not in arguments:
        arguments["path"] = arguments["name"]

    missing = spec["required"] - arguments.keys()
    if missing:
        raise DecisionError(f"missing arguments for {action}: {sorted(missing)}")
    extra = arguments.keys() - spec["required"] - spec["optional"]
    if extra:
        raise DecisionError(f"unexpected arguments for {action}: {sorted(extra)}")

    for key, value in arguments.items():
        if value is None and key in spec["optional"]:
            continue
        if key == "confirmed":
            if not isinstance(value, bool):
                raise DecisionError("argument 'confirmed' must be boolean")
            continue
        if not isinstance(value, str) or not value.strip():
            raise DecisionError(f"argument {key!r} must be a non-empty string")
