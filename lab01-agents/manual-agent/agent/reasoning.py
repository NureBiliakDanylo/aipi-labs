"""Компонент прийняття рішень: LLM як політика policy(state) -> action."""

import json
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from .errors import DecisionError

load_dotenv()
MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

AGENT_INSTRUCTION = """
You are the decision component of an educational AI agent specialized in HTTP status codes for REST API design (RFC 9110 and Nom-Nom-Save server architecture).
You do not chat. On every call you choose exactly one action.

Available actions:
1. lookup_http_status
   Use it when verified information about a specific HTTP status code is needed.
   Arguments: {"code": string} e.g. "200", "201", "204", "400", "401", "403", "404", "409", "500", "503".

2. list_status_class
   Use it when user asks about a whole status category or class of codes.
   Arguments: {"status_class": string} e.g. "2xx", "3xx", "4xx", "5xx".

3. finish
   Use it when the verified observations are enough to reach the goal and construct a comprehensive answer in Ukrainian, or when the environment reported that the information does not exist.
   Arguments: {"answer": string} final answer in Ukrainian.

Return valid JSON only:
{"action": "lookup_http_status | list_status_class | finish", "arguments": {...}, "decision_summary": "one short sentence: why this action"}

Rules:
- Use only facts from VERIFIED OBSERVATIONS in the final answer.
- If an observation starts with NOT_FOUND, state clearly that the verified information is missing from the environment; do not invent it.
- If an observation starts with ERROR, fix your previous decision according to the error message.
- Do not repeat a lookup or action that is already present in the observations.
- decision_summary must be one sentence explaining the rational choice of action.
"""

_client: genai.Client | None = None


def get_client() -> genai.Client:
    """Лінива ініціалізація: тести без мережі імпортують модуль без ключа."""
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def build_observation(goal: str, observations: list[str], step: int, max_steps: int) -> str:
    """OBSERVE: формує те, що бачить модель на поточному кроці."""
    known = "\n".join(f"- {item}" for item in observations) or "None yet."
    return (
        f"GOAL:\n{goal}\n\n"
        f"CURRENT STEP: {step} of {max_steps}\n\n"
        f"VERIFIED OBSERVATIONS:\n{known}\n\n"
        "AVAILABLE ACTIONS: lookup_http_status, list_status_class, finish\n"
        "Choose the next action."
    )


def parse_decision(text: str | None) -> dict:
    """Перетворює текст відповіді моделі на словник або піднімає DecisionError."""
    try:
        decision = json.loads(text)
    except (json.JSONDecodeError, TypeError) as exc:
        raise DecisionError(f"invalid JSON from model: {exc}") from exc
    if not isinstance(decision, dict):
        raise DecisionError("decision must be a JSON object")
    return decision


def get_decision(goal: str, observations: list[str], step: int, max_steps: int) -> dict:
    """REASON: один виклик LLM повертає одне структуроване рішення."""
    prompt = build_observation(goal, observations, step, max_steps)
    response = get_client().models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=AGENT_INSTRUCTION,
            response_mime_type="application/json",
        ),
    )
    return parse_decision(response.text)
