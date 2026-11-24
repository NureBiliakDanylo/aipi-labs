"""Unit tests for coordinator architecture with expert sub-agents (single_turn mode)."""

import asyncio
from collections.abc import AsyncGenerator
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.coordinator import build_coordinator
from run_cli import run_once


class CallingLlm(BaseLlm):
    """Mock LLM where coordinator dynamically delegates to reproducer_expert then summarizes."""
    turn: int = 0

    def __init__(self, **data):
        super().__init__(**data)
        self.turn = 0

    async def generate_content_async(
        self, req, stream=False
    ) -> AsyncGenerator[LlmResponse, None]:
        instruction = str(req.config.system_instruction or "")

        if "reproduction engineer" in instruction:
            part = types.Part(
                text="- Відправити запит POST /api/v1/orders/reserve\n- Отримати 200 замість 409"
            )
        elif self.turn == 0:
            self.turn += 1
            part = types.Part(
                function_call=types.FunctionCall(
                    name="reproducer_expert",
                    args={"request": "Сформулюй кроки відтворення для POST /api/v1/orders/reserve"},
                )
            )
        else:
            part = types.Part(
                text="Підсумок тріажу від координатора: підтверджено баг конкурентного овербукінгу."
            )

        yield LlmResponse(
            content=types.Content(role="model", parts=[part]),
            usage_metadata=types.GenerateContentResponseUsageMetadata(
                prompt_token_count=120,
                candidates_token_count=80,
                total_token_count=200,
            ),
        )


def test_coordinator_delegates_to_expert():
    """Verify that coordinator calls reproducer_expert and produces final summary."""
    model = CallingLlm(model="scripted")
    coordinator = build_coordinator(model)
    result = asyncio.run(
        run_once(coordinator, "Як відтворити овербукінг лота у Nom-Nom-Save?")
    )

    authors = [s["author"] for s in result["trace"]]
    assert "coordinator" in authors
    assert "reproducer_expert" in authors
    assert "classifier_expert" not in authors
    assert "impact_expert" not in authors
    assert "triage_expert" not in authors

    last_text = result["trace"][-1]["text"]
    assert last_text.startswith("Підсумок тріажу від координатора")
