"""Перевірка обґрунтованості відповіді: чи кожне посилання [[...]] веде на отримане джерело (Лістинг 1.25 МВ)."""
import json
import re
import sys
from pathlib import Path

WIKILINK_SOURCE = re.compile(r"\[\[([^\]#|]+)(?:#([^\]|]+))?(?:\|([^\]]+))?\]\]")

def _normalize_name(name: str) -> str:
    """Нормалізує назву: замінює дефіси та підкреслення на пробіли, зводить до нижнього регістру."""
    return re.sub(r"[\s\-_]+", " ", name).strip().lower()

def check_citations(trace_path: Path) -> dict:
    data = json.loads(trace_path.read_text(encoding="utf-8"))
    final_answer = data.get("final_answer", "")
    
    # 1. Знаходимо всі цитати у фінальній відповіді
    citations = set()
    for m in WIKILINK_SOURCE.finditer(final_answer):
        note = m.group(1).strip()
        sec = m.group(2).strip() if m.group(2) else ""
        citations.add(f"{note}#{sec}" if sec else note)

    # 2. Знаходимо всі джерела зі спостережень агента
    observed_sources = set()
    for step in data.get("steps", []):
        obs = step.get("observation", "")
        # З фрагментів та нотаток: source="[[...]]"
        for m in re.finditer(r'source="\[\[([^\]]+)\]\]"', obs):
            observed_sources.add(m.group(1).strip())
        # З шляхів: path="..."
        for m in re.finditer(r'path="([^"]+)"', obs):
            p = m.group(1).strip()
            observed_sources.add(Path(p).stem)
        # З читання повної нотатки (arguments/args)
        if step.get("action") == "read_note":
            args = step.get("arguments") or step.get("args", {})
            name = args.get("path") or args.get("name", "")
            if name:
                observed_sources.add(Path(name).stem)

    # 3. Перевірка валідності з урахуванням нормалізації
    valid = []
    invalid = []
    norm_observed = [_normalize_name(s.split("#")[0]) for s in observed_sources]

    for c in citations:
        c_base = c.split("#")[0].strip()
        c_norm = _normalize_name(c_base)
        matched = any(c_norm == obs or c_norm in obs or obs in c_norm for obs in norm_observed)
        if matched:
            valid.append(c)
        else:
            invalid.append(c)

    return {
        "cited": len(citations),
        "valid": len(valid),
        "invalid": invalid,
        "grounded": len(invalid) == 0 and len(citations) > 0
    }

def main():
    if len(sys.argv) < 2:
        print("Використання: python -m eval.citations <шлях_до_файлу_трасування>")
        sys.exit(1)
    res = check_citations(Path(sys.argv[1]))
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
