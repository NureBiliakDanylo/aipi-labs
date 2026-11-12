import json
import re
import time
from pathlib import Path
from kb.tools import build_tools
from baseline import one_shot_answer, rag_answer
from agent.loop import run_agent

def normalize(s: str) -> str:
    return re.sub(r"[\s\-_.]+", "", s).lower()

tools = build_tools()
eval_set_path = Path(r"c:\7 sem\Ші\lab02-knowledge\eval\retrieval_set.json")
eval_queries = json.loads(eval_set_path.read_text(encoding="utf-8"))

print("=== 1. Оцінювання якості пошуку (Retrieval Evaluation) ===")
hits = 0
reciprocal_ranks = []
in_domain_count = 0
out_domain_distances = []
in_domain_min_distances = []

for q in eval_queries:
    expected_stems = [normalize(Path(e).stem) for e in q["expected"]]
    results = tools.store.search(q["query"], top_k=4)
    if expected_stems:
        in_domain_count += 1
        found_rank = 0
        min_dist = results[0].distance if results else 1.0
        in_domain_min_distances.append(min_dist)
        for rank, r in enumerate(results, 1):
            hit_stem = normalize(Path(r.path).stem)
            if hit_stem in expected_stems:
                found_rank = rank
                break
        if found_rank > 0:
            hits += 1
            reciprocal_ranks.append(1.0 / found_rank)
        else:
            reciprocal_ranks.append(0.0)
    else:
        min_dist = results[0].distance if results else 1.0
        out_domain_distances.append(min_dist)

hit_at_4 = hits / in_domain_count if in_domain_count else 0
mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0

print(f"In-domain queries: {in_domain_count}")
print(f"Hit@4: {hit_at_4:.3f} ({hits}/{in_domain_count})")
print(f"MRR: {mrr:.3f}")
print(f"Average in-domain best distance: {sum(in_domain_min_distances)/len(in_domain_min_distances):.3f}")
print(f"Average out-of-domain best distance: {sum(out_domain_distances)/len(out_domain_distances):.3f}")

print("\n=== 2. Експеримент для трьох систем (Типи запитів A-E) ===")
exp_tasks = [
    ("A", "Які методи HTTP вважаються ідемпотентними?"),
    ("B", "Який код помилки та формат тіла відповіді обрати для конфлікту версій ресурсу?"),
    ("C", "Як обробити запит клієнта на скасування вже виконаного замовлення у стейт-машині?"),
    ("D", "Як налаштувати компілятор C++ під архітектуру ARM Cortex-M4?"),
    ("E", "Як захистити сесію користувача від CSRF і одночасно запобігти викраденню cookie?"),
]

for q_type, q_text in exp_tasks:
    t0 = time.perf_counter()
    ans_os = one_shot_answer(q_text)
    t_os = round(time.perf_counter() - t0, 3)

    t0 = time.perf_counter()
    ans_rag = rag_answer(q_text, tools)
    t_rag = round(time.perf_counter() - t0, 3)

    t0 = time.perf_counter()
    st_agent = run_agent(q_text, tools)
    t_agent = round(time.perf_counter() - t0, 3)

    print(f"\nЗапит [{q_type}]: {q_text}")
    print(f"  One-shot ({t_os}s): {ans_os[:120]}...")
    print(f"  RAG ({t_rag}s): {ans_rag[:120]}...")
    print(f"  Agent ({t_agent}s, steps={len(st_agent.steps)}): {st_agent.final_answer[:120]}...")

print("\nEvaluation and Experiment script completed successfully!")
