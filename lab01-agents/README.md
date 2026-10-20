# lab01-agents: Побудова AI-агента

Лабораторна робота № 1

**Автор**: Біляк Данило, студент групи ПЗПІ-23-5  
**Предметна область**: Коди стану протоколу HTTP

---

## Структура репозиторію

```text
lab01-agents/
├── .gitignore               # Виключення .env, .venv/ тощо
├── README.md                # Опис проєкту та інструкція із запуску
├── AGENT-CARD.md            # Паспорт агента версії 1.0.0
├── manual-agent/            # Частина А: Власний агент з циклом без фреймворків
│   ├── pyproject.toml       # Залежності та конфігурація pytest
│   ├── .env.example         # Шаблон змінних оточення (без секретів)
│   ├── baseline.py          # Базова лінія (одиничний one-shot виклик LLM)
│   ├── main.py              # Точка входу CLI та збереження трасувань
│   ├── agent/               # Модулі власного агента
│   │   ├── __init__.py
│   │   ├── errors.py        # DecisionError
│   │   ├── state.py         # AgentState
│   │   ├── environment.py   # База фактів та дії lookup_http_status, list_status_class
│   │   ├── reasoning.py     # Побудова спостереження, інструкція, виклик Gemini
│   │   ├── validator.py     # Білий список дій та валідація аргументів
│   │   └── loop.py          # Оркестрація циклу агента, ліміти MAX_STEPS / MAX_LLM_CALLS
│   ├── tests/               # Модульні тести (детермінована частина + мок-цикл)
│   │   ├── test_environment.py
│   │   ├── test_validator.py
│   │   └── test_loop.py
│   └── traces/              # Журнал виконаних трасувань у форматі JSON
└── adk-agent/               # Частина Б: Агент на базі Google ADK 2.x
    ├── pyproject.toml       # Залежності google-adk
    ├── agents-cli-manifest.yaml
    ├── Makefile
    ├── GEMINI.md
    ├── .env.example
    ├── app/
    │   ├── __init__.py
    │   ├── agent.py         # Оголошення агента, інструкції та інструментів
    │   └── environment.py   # Спільне верифіковане середовище фактів
    └── tests/
        ├── unit/            # Модульні тести інструментів
        └── integration/     # Наскрізні інтеграційні тести
```

---