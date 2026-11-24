"""Scripted test double for LLM calls: operates 100% offline without network or API keys."""

import json
from collections.abc import AsyncGenerator
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types


class ScriptedLlm(BaseLlm):
    script: dict[str, list] = {}
    calls: list[str] = []

    def __init__(self, **data):
        super().__init__(**data)
        self.calls = []

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        instruction = str(llm_request.config.system_instruction or "")
        
        for marker, replies in self.script.items():
            if marker in instruction:
                self.calls.append(marker)
                reply = replies.pop(0) if len(replies) > 1 else replies[0]
                text = (
                    reply
                    if isinstance(reply, str)
                    else json.dumps(reply, ensure_ascii=False)
                )
                yield LlmResponse(
                    content=types.Content(
                        role="model", parts=[types.Part(text=text)]
                    ),
                    usage_metadata=types.GenerateContentResponseUsageMetadata(
                        prompt_token_count=150,
                        candidates_token_count=100,
                        total_token_count=250,
                    ),
                )
                return

        raise AssertionError(
            f"No scripted reply found for instruction marker. Instruction prefix: {instruction[:120]!r}"
        )
