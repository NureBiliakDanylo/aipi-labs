"""CLI runner for Nom-Nom-Save Bug Triage MAS with report and trace persistence.
Usage:
    python run_cli.py "опис багу..." [--mode team|solo|coordinator]
"""

import argparse
import asyncio
import json
import time
from collections import defaultdict
from pathlib import Path

from google.adk import Workflow
from google.adk.runners import InMemoryRunner
from google.genai import types

APP_NAME = "triage_team"


async def run_once(agent, request: str) -> dict:
    """Execute the agent or workflow once and collect final state, event trace, and metrics."""
    runner = InMemoryRunner(agent=agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="student"
    )
    trace, calls, tokens = [], defaultdict(int), defaultdict(int)
    started = time.perf_counter()

    message = types.Content(role="user", parts=[types.Part(text=request)])
    async for event in runner.run_async(
        user_id="student", session_id=session.id, new_message=message
    ):
        text = ""
        if event.content and event.content.parts:
            text = "".join(p.text or "" for p in event.content.parts)
        route = event.actions.route if event.actions else None

        from_model = (
            text
            and event.author != "user"
            and not (isinstance(agent, Workflow) and event.author == agent.name)
        )
        if event.usage_metadata or from_model:
            calls[event.author] += 1
        if event.usage_metadata:
            tokens[event.author] += event.usage_metadata.total_token_count or 0

        node = (event.node_info.path or "") if event.node_info else ""
        trace.append({
            "t": round(time.perf_counter() - started, 2),
            "author": event.author,
            "node": node.split("/")[-1] if node else "",
            "route": route,
            "text": text[:300],
        })

    session = await runner.session_service.get_session(
        app_name=APP_NAME, user_id="student", session_id=session.id
    )

    return {
        "state": dict(session.state),
        "trace": trace,
        "llm_calls": dict(calls),
        "tokens": dict(tokens),
        "seconds": round(time.perf_counter() - started, 2),
    }


def main() -> None:
    from google.adk.models import Gemini
    from app.agent import MODEL, build_workflow
    from app.baseline import build_solo_agent
    from app.coordinator import build_coordinator
    from app.nodes import render_report

    parser = argparse.ArgumentParser(description="Nom-Nom-Save Bug Triage MAS CLI")
    parser.add_argument("request", help="Bug report description text")
    parser.add_argument(
        "--mode",
        choices=["team", "solo", "coordinator"],
        default="team",
        help="System execution mode",
    )
    args = parser.parse_args()

    model = Gemini(model=MODEL, retry_options=types.HttpRetryOptions(attempts=3))
    agent = {
        "team": build_workflow,
        "solo": build_solo_agent,
        "coordinator": build_coordinator,
    }[args.mode](model)

    result = asyncio.run(run_once(agent, args.request))

    if args.mode == "coordinator":
        for step in result["trace"]:
            print(f"{step['t']:>6}s {step['author']:<20} {step['text'][:90]!r}")
        print(f"\nLLM calls: {result['llm_calls']}, time: {result['seconds']}s")
        return

    state = result["state"]
    if args.mode == "solo" and "solo" in state:
        state = {**state["solo"], "drafts": 1, "stop_reason": "single_call"}

    report = state.get("report") or render_report(state)
    print(report)
    print(
        f"\n[{args.mode}] LLM calls: {result['llm_calls']}, "
        f"tokens: {sum(result['tokens'].values())}, time: {result['seconds']}s"
    )

    out = Path("runs") / time.strftime("%Y%m%d_%H%M%S")
    out.mkdir(parents=True, exist_ok=True)
    (out / f"{args.mode}_report.md").write_text(report, encoding="utf-8")
    (out / f"{args.mode}_trace.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
