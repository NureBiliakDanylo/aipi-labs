"""Точка входу для тестування агента, RAG та One-shot."""
import argparse
import json
import time
from pathlib import Path
from agent.loop import run_agent
from baseline import one_shot_answer, rag_answer
from kb.tools import build_tools

def save_trace(state, trace_dir: Path) -> Path:
    trace_dir.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    path = trace_dir / f"trace_{timestamp}.json"
    data = {
        "goal": state.goal,
        "status": state.status,
        "final_answer": state.final_answer,
        "steps": [
            {
                "step": s.step,
                "action": s.action,
                "args": s.args,
                "observation": s.observation[:300] + ("..." if len(s.observation) > 300 else ""),
                "thought": s.thought
            }
            for s in state.steps
        ]
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path

def main():
    parser = argparse.ArgumentParser(description="Запуск kb-agent з базою знань")
    parser.add_argument("goal", help="Запит користувача")
    parser.add_argument("--mode", choices=["agent", "rag", "oneshot"], default="agent", help="Режим роботи")
    args = parser.parse_args()

    tools = build_tools()

    if args.mode == "oneshot":
        ans = one_shot_answer(args.goal)
        print("=== ONE-SHOT ANSWER ===")
        print(ans)
    elif args.mode == "rag":
        ans = rag_answer(args.goal, tools)
        print("=== NAIVE RAG ANSWER ===")
        print(ans)
    else:
        print(f"Goal: {args.goal}")
        state = run_agent(args.goal, tools)
        trace_path = save_trace(state, Path("./traces"))
        print(f"\nStatus: {state.status}")
        print(f"Final Answer:\n{state.final_answer}")
        print(f"\nSaved trace to: {trace_path}")

if __name__ == "__main__":
    main()
