import json
from pathlib import Path
from agent.loop import run_agent
from kb.tools import build_tools
from eval.citations import check_citations
from main import save_trace

tools = build_tools()

scenarios = [
    {
        "name": "trace_type_b_version_conflict",
        "goal": "Який код помилки та формат тіла відповіді обрати для конфлікту версій ресурсу?"
    },
    {
        "name": "trace_type_c_order_cancellation",
        "goal": "Як обробити запит клієнта на скасування вже виконаного замовлення у стейт-машині?"
    },
    {
        "name": "trace_type_e_csrf_cors_security",
        "goal": "Як захистити сесію користувача від CSRF і одночасно запобігти викраденню cookie?"
    }
]

traces_dir = Path(r"c:\7 sem\Ші\lab02-knowledge\traces")
traces_dir.mkdir(parents=True, exist_ok=True)

print("Running 3 multi-step agent scenarios...")
for sc in scenarios:
    state = run_agent(sc["goal"], tools)
    trace_path = traces_dir / f"{sc['name']}.json"
    trace_data = {
        "goal": state.goal,
        "status": state.status,
        "final_answer": state.final_answer,
        "steps": [
            {
                "step": s.step,
                "action": s.action,
                "args": s.args,
                "observation": s.observation,
                "thought": s.thought
            }
            for s in state.steps
        ]
    }
    trace_path.write_text(json.dumps(trace_data, indent=2, ensure_ascii=False), encoding="utf-8")
    eval_res = check_citations(trace_path)
    print(f"Scenario: {sc['name']}")
    print(f"  Status: {state.status}, Steps: {len(state.steps)}")
    print(f"  Citations check: {eval_res}")
    assert eval_res["grounded"] is True, f"Trace {sc['name']} failed citations check!"

print("\nAll 3 multi-step traces generated and verified successfully!")
