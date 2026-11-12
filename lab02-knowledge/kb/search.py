"""Утиліта налагодження пошуку: python -m kb.search "запит" [--tag тег]."""
import argparse
from .tools import build_tools

def main():
    parser = argparse.ArgumentParser(description="Пошук по базі знань")
    parser.add_argument("query", help="Текст пошукового запиту")
    parser.add_argument("--tag", default=None, help="Фільтр за тегом")
    args = parser.parse_args()

    tools = build_tools()
    res = tools.search_knowledge(args.query, tag=args.tag)
    print("=== Результат пошуку ===")
    print(res)

if __name__ == "__main__":
    main()
