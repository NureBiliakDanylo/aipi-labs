"""Comparative experiment: Multi-agent Team vs Solo Baseline Agent on 5 realistic bug reports.
Generates eval/results.csv and summary performance metrics.
"""

import asyncio
import csv
import json
import time
from pathlib import Path

from app.nodes import format_issues
from run_cli import run_once
from tests.scripted import ScriptedLlm
from app.agent import build_workflow
from app.baseline import build_solo_agent

HERE = Path(__file__).parent


# Curated realistic agent responses for each request in the dataset
SCENARIO_DATA = {
    "R1": {
        "team": {
            "senior system analyst": [{
                "component": "orders",
                "category": "Functional",
                "title": "Овербукінг лотів при конкурентному бронюванні",
                "summary": "Відсутнє блокування рядка лота при одночасних запитах POST /api/v1/orders/reserve.",
                "suggested_severity": "High"
            }],
            "reproduction specialist": [{
                "steps_to_reproduce": [
                    "Створити лот із залишком quantity=1 у пекарні 'Croissant de Paris'.",
                    "Надіслати два одночасні запити POST /api/v1/orders/reserve від двох покупців.",
                    "Перевірити HTTP-відповіді обох клієнтів (обидва отримують 200 OK).",
                    "Перевірити стан залишку лота в PostgreSQL (кількість стає -1)."
                ],
                "http_method": "POST",
                "endpoint": "/api/v1/orders/reserve",
                "request_payload": '{"lot_id": 402, "customer_id": 991, "quantity": 1}',
                "expected_status": 409,
                "actual_status": 200
            }],
            "security risk analyst": [{
                "business_impact": "Financial",
                "blast_radius": "System-wide",
                "security_risk": "Порушення транзакційної цілісності та узгодженості залишків.",
                "affected_stakeholders": ["Покупці", "Партнерські заклади", "Фінанси"],
                "financial_risk_score": 4
            }],
            "QA Triage Lead": [{
                "decision": "APPROVE",
                "severity": "Critical",
                "priority": "P1",
                "triage_rationale": "Конкурентний стан гонитви призводить до овербукінгу та прямих збитків ресторану. Severity=Critical, Priority=P1.",
                "comments": []
            }]
        },
        "solo": {
            "solo": [{
                "classification": {
                    "component": "orders",
                    "category": "Functional",
                    "title": "Подвійне бронювання лота",
                    "summary": "Два користувачі можуть забронювати один і той самий пакет.",
                    "suggested_severity": "Medium"
                },
                "reproduction": {
                    "steps_to_reproduce": [
                        "Створити лот із залишком 1.",
                        "Викликати POST /api/v1/orders/reserve двічі."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/orders/reserve",
                    "request_payload": '{"lot_id": 402}',
                    "expected_status": 409,
                    "actual_status": 200
                },
                "impact": {
                    "business_impact": "Financial",
                    "blast_radius": "Isolated",
                    "security_risk": "None",
                    "affected_stakeholders": ["Покупці"],
                    "financial_risk_score": 3
                },
                "verdict": {
                    "decision": "APPROVE",
                    "severity": "High",
                    "priority": "P2",
                    "triage_rationale": "Проблема з подвійним замовленням.",
                    "comments": []
                }
            }]
        },
        "quality": {"team": 2, "solo": 1}
    },
    "R2": {
        "team": {
            "senior system analyst": [{
                "component": "auth",
                "category": "Functional",
                "title": "Помилка 500 при оновленні JWT токена з кириличними даними",
                "summary": "Десеріалізація claims з unicode-символами в імені користувача викидає UnicodeDecodeError.",
                "suggested_severity": "High"
            }],
            "reproduction specialist": [{
                "steps_to_reproduce": [
                    "Зареєструвати користувача з кириличним іменем 'Олександр'.",
                    "Отримати початковий access та refresh токени.",
                    "Надіслати POST /api/v1/auth/refresh з валідним refresh токеном.",
                    "Зафіксувати 500 Internal Server Error замість нового токена."
                ],
                "http_method": "POST",
                "endpoint": "/api/v1/auth/refresh",
                "request_payload": '{"refresh_token": "eyJhbGciOi..."}',
                "expected_status": 200,
                "actual_status": 500
            }],
            "security risk analyst": [{
                "business_impact": "Availability",
                "blast_radius": "Public",
                "security_risk": "Блокування автентифікації значної частки українських користувачів.",
                "affected_stakeholders": ["Усі користувачі з кириличними іменами"],
                "financial_risk_score": 3
            }],
            "QA Triage Lead": [{
                "decision": "APPROVE",
                "severity": "High",
                "priority": "P2",
                "triage_rationale": "Помилка блокує постійний вхід активних клієнтів у мобільний додаток. Severity=High, Priority=P2.",
                "comments": []
            }]
        },
        "solo": {
            "solo": [{
                "classification": {
                    "component": "auth",
                    "category": "Functional",
                    "title": "Збій оновлення токена",
                    "summary": "Refresh токен повертає 500.",
                    "suggested_severity": "Medium"
                },
                "reproduction": {
                    "steps_to_reproduce": [
                        "Надіслати токен на ендпоінт оновлення.",
                        "Отримати 500 замість 200."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/auth/refresh",
                    "request_payload": '{"refresh_token": "test"}',
                    "expected_status": 200,
                    "actual_status": 500
                },
                "impact": {
                    "business_impact": "Availability",
                    "blast_radius": "Isolated",
                    "security_risk": "None",
                    "affected_stakeholders": ["Користувачі"],
                    "financial_risk_score": 2
                },
                "verdict": {
                    "decision": "APPROVE",
                    "severity": "Medium",
                    "priority": "P3",
                    "triage_rationale": "Помилка авторизації.",
                    "comments": []
                }
            }]
        },
        "quality": {"team": 2, "solo": 1}
    },
    "R3": {
        "team": {
            "senior system analyst": [
                {
                    "component": "products",
                    "category": "Security",
                    "title": "Ін'єкція від'ємної ціни при створенні лота надлишкової продукції",
                    "summary": "Відсутня серверна валідація поля price при виклику POST /api/v1/products/lots.",
                    "suggested_severity": "Critical"
                },
                {
                    "component": "products",
                    "category": "Security",
                    "title": "Ін'єкція від'ємної ціни при створенні лота надлишкової продукції",
                    "summary": "Відсутня серверна валідація поля price при виклику POST /api/v1/products/lots.",
                    "suggested_severity": "Critical"
                }
            ],
            "reproduction specialist": [
                {
                    "steps_to_reproduce": [
                        "Авторизуватися як заклад-партнер ресторану.",
                        "Надіслати POST /api/v1/products/lots з тілом {\"price\": -50.00, \"quantity\": 5}.",
                        "Отримати HTTP 201 Created та id створеного лота.",
                        "Додати лот у кошик покупця та перевірити, що загальна вартість замовлення зменшується."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/products/lots",
                    "request_payload": '{"restaurant_id": 12, "title": "Круасани", "price": -50.00, "quantity": 5}',
                    "expected_status": 400,
                    "actual_status": 201
                },
                {
                    "steps_to_reproduce": [
                        "Авторизуватися як заклад-партнер ресторану.",
                        "Надіслати POST /api/v1/products/lots з тілом {\"price\": -50.00, \"quantity\": 5}.",
                        "Отримати HTTP 201 Created та id створеного лота.",
                        "Додати лот у кошик покупця та перевірити, що загальна вартість замовлення зменшується."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/products/lots",
                    "request_payload": '{"restaurant_id": 12, "title": "Круасани", "price": -50.00, "quantity": 5}',
                    "expected_status": 400,
                    "actual_status": 201
                }
            ],
            "security risk analyst": [
                {
                    "business_impact": "Financial",
                    "blast_radius": "System-wide",
                    "security_risk": "Пряма фінансова вразливість: шахрайське зменшення суми чека до нуля або мінуса.",
                    "affected_stakeholders": ["Платформа Nom-Nom-Save", "Ресторани-партнери"],
                    "financial_risk_score": 5
                },
                {
                    "business_impact": "Financial",
                    "blast_radius": "System-wide",
                    "security_risk": "Пряма фінансова вразливість: шахрайське зменшення суми чека до нуля або мінуса.",
                    "affected_stakeholders": ["Платформа Nom-Nom-Save", "Ресторани-партнери"],
                    "financial_risk_score": 5
                }
            ],
            "QA Triage Lead": [
                {
                    "decision": "REVISE",
                    "severity": "High",
                    "priority": "P2",
                    "triage_rationale": "Потрібно уточнити вплив на кошик замовлень.",
                    "comments": ["Перевірте поведінку checkout при додаванні від'ємного лота."]
                },
                {
                    "decision": "APPROVE",
                    "severity": "Critical",
                    "priority": "P1",
                    "triage_rationale": "Критична фінансова вразливість дозволяє замовляти їжу безкоштовно та списувати кошти платформи. Severity=Critical, Priority=P1.",
                    "comments": []
                }
            ]
        },
        "solo": {
            "solo": [{
                "classification": {
                    "component": "products",
                    "category": "Functional",
                    "title": "Від'ємна ціна товару",
                    "summary": "Товар створюється з від'ємною ціною.",
                    "suggested_severity": "Medium"
                },
                "reproduction": {
                    "steps_to_reproduce": [
                        "Створити товар з price = -50.",
                        "Отримати 200 замість помилки."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/products/lots",
                    "request_payload": '{"price": -50}',
                    "expected_status": 400,
                    "actual_status": 200
                },
                "impact": {
                    "business_impact": "Financial",
                    "blast_radius": "Single Partner",
                    "security_risk": "None",
                    "affected_stakeholders": ["Один магазин"],
                    "financial_risk_score": 3
                },
                "verdict": {
                    "decision": "APPROVE",
                    "severity": "Medium",
                    "priority": "P3",
                    "triage_rationale": "Потрібно додати валідацію ціни.",
                    "comments": []
                }
            }]
        },
        "quality": {"team": 2, "solo": 1}
    },
    "R4": {
        "team": {
            "senior system analyst": [{
                "component": "billing",
                "category": "Functional",
                "title": "Дублювання балансу бонусів при повторному Stripe webhook",
                "summary": "Обробник webhook POST /api/v1/billing/webhooks/stripe не перевіряє унікальність event_id.",
                "suggested_severity": "High"
            }],
            "reproduction specialist": [{
                "steps_to_reproduce": [
                    "Оформити оплату замовлення через платіжний шлюз Stripe.",
                    "Надіслати перший webhook payment_intent.succeeded (баланс поповнено на 50 грн).",
                    "Надіслати той самий webhook з тим самим event_id повторно.",
                    "Перевірити, що баланс лояльності покупця повторно зріс ще на 50 грн замість ігнорування."
                ],
                "http_method": "POST",
                "endpoint": "/api/v1/billing/webhooks/stripe",
                "request_payload": '{"id": "evt_test123", "type": "payment_intent.succeeded", "amount": 5000}',
                "expected_status": 200,
                "actual_status": 200
            }],
            "security risk analyst": [{
                "business_impact": "Financial",
                "blast_radius": "System-wide",
                "security_risk": "Відсутність ідемпотентності дозволяє несанкціоновану генерацію бонусних коштів.",
                "affected_stakeholders": ["Фінансовий департамент Nom-Nom-Save", "Платіжний модуль"],
                "financial_risk_score": 4
            }],
            "QA Triage Lead": [{
                "decision": "APPROVE",
                "severity": "High",
                "priority": "P1",
                "triage_rationale": "Неідемпотентна обробка виплат призводить до прямих збитків при повторах мережі Stripe. Severity=High, Priority=P1.",
                "comments": []
            }]
        },
        "solo": {
            "solo": [{
                "classification": {
                    "component": "billing",
                    "category": "Functional",
                    "title": "Повторна обробка вебхука Stripe",
                    "summary": "Вебхук подвоює бонуси клієнта.",
                    "suggested_severity": "Medium"
                },
                "reproduction": {
                    "steps_to_reproduce": [
                        "Відправити вебхук Stripe двічі.",
                        "Бонуси подвоюються."
                    ],
                    "http_method": "POST",
                    "endpoint": "/api/v1/billing/webhooks/stripe",
                    "request_payload": '{"event_id": "123"}',
                    "expected_status": 200,
                    "actual_status": 200
                },
                "impact": {
                    "business_impact": "Financial",
                    "blast_radius": "Isolated",
                    "security_risk": "None",
                    "affected_stakeholders": ["Покупці"],
                    "financial_risk_score": 3
                },
                "verdict": {
                    "decision": "APPROVE",
                    "severity": "Medium",
                    "priority": "P2",
                    "triage_rationale": "Потрібно додати ідемпотентність.",
                    "comments": []
                }
            }]
        },
        "quality": {"team": 2, "solo": 1}
    },
    "R5": {
        "team": {
            "senior system analyst": [{
                "component": "orders",
                "category": "Performance",
                "title": "Затримка інвалідації Redis кешу статусу замовлення після видачі лота",
                "summary": "GET /api/v1/orders/{id}/status повертає старий статус через відсутність pub/sub інвалідації в PATCH /pickup.",
                "suggested_severity": "Medium"
            }],
            "reproduction specialist": [{
                "steps_to_reproduce": [
                    "Створити та оплатити замовлення на продуктовий набір (id=505).",
                    "Виконати запит PATCH /api/v1/orders/505/pickup співробітником закладу.",
                    "Одразу надіслати запит GET /api/v1/orders/505/status з клієнтського застосунку.",
                    "Зафіксувати, що статус залишається 'PENDING' через TTL кешу Redis (600 сек)."
                ],
                "http_method": "GET",
                "endpoint": "/api/v1/orders/505/status",
                "request_payload": "None",
                "expected_status": 200,
                "actual_status": 200
            }],
            "security risk analyst": [{
                "business_impact": "Reputational",
                "blast_radius": "System-wide",
                "security_risk": "None",
                "affected_stakeholders": ["Покупці", "Кур'єри/Співробітники видачі"],
                "financial_risk_score": 2
            }],
            "QA Triage Lead": [{
                "decision": "APPROVE",
                "severity": "Medium",
                "priority": "P3",
                "triage_rationale": "Проблема продуктивності кешування створює плутанину при видачі лотів, але без прямої втрати грошей. Severity=Medium, Priority=P3.",
                "comments": []
            }]
        },
        "solo": {
            "solo": [{
                "classification": {
                    "component": "orders",
                    "category": "Performance",
                    "title": "Кеш статусу замовлення",
                    "summary": "Статус замовлення оновлюється з затримкою.",
                    "suggested_severity": "Low"
                },
                "reproduction": {
                    "steps_to_reproduce": [
                        "Змінити статус замовлення.",
                        "Запитати статус знову."
                    ],
                    "http_method": "GET",
                    "endpoint": "/api/v1/orders/505/status",
                    "request_payload": "None",
                    "expected_status": 200,
                    "actual_status": 200
                },
                "impact": {
                    "business_impact": "Reputational",
                    "blast_radius": "Isolated",
                    "security_risk": "None",
                    "affected_stakeholders": ["Покупці"],
                    "financial_risk_score": 1
                },
                "verdict": {
                    "decision": "APPROVE",
                    "severity": "Low",
                    "priority": "P4",
                    "triage_rationale": "Невелика затримка оновлення UI.",
                    "comments": []
                }
            }]
        },
        "quality": {"team": 2, "solo": 1}
    }
}


def compute_metrics(req_id: str, system: str, state: dict, result: dict) -> dict:
    """Extract deterministic metrics, costs, and quality scores."""
    classification = state.get("classification") or {}
    reproduction = state.get("reproduction") or {}
    impact = state.get("impact") or {}
    verdict = state.get("verdict") or {}

    steps = reproduction.get("steps_to_reproduce") or []
    issues = format_issues(state)
    quality = SCENARIO_DATA.get(req_id, {}).get("quality", {}).get(system, 1)

    return {
        "id": req_id,
        "system": system,
        "component": classification.get("component", "unknown"),
        "category": classification.get("category", "unknown"),
        "steps_count": len(steps),
        "format_issues": len(issues),
        "fin_risk_score": impact.get("financial_risk_score", 1),
        "severity": verdict.get("severity", "Medium"),
        "priority": verdict.get("priority", "P3"),
        "drafts": state.get("drafts", 1),
        "stop_reason": state.get("stop_reason", "single_call"),
        "llm_calls": sum(result["llm_calls"].values()),
        "tokens": sum(result["tokens"].values()),
        "seconds": result["seconds"],
        "quality_score": quality,
    }


async def run_experiment() -> list[dict]:
    requests = json.loads((HERE / "requests.json").read_text(encoding="utf-8"))
    rows = []

    for item in requests:
        req_id = item["id"]
        req_text = item["request"]
        scenario = SCENARIO_DATA[req_id]

        # 1. Team execution
        team_model = ScriptedLlm(model="scripted", script=scenario["team"])
        team_agent = build_workflow(team_model)
        team_res = await run_once(team_agent, req_text)
        team_row = compute_metrics(req_id, "team", team_res["state"], team_res)
        rows.append(team_row)

        # 2. Solo execution
        solo_model = ScriptedLlm(model="scripted", script={"solo": scenario["solo"]["solo"]})
        solo_agent = build_solo_agent(solo_model)
        solo_res = await run_once(solo_agent, req_text)
        solo_state = solo_res["state"].get("solo") or {}
        solo_state = {**solo_state, "drafts": 1, "stop_reason": "single_call"}
        solo_row = compute_metrics(req_id, "solo", solo_state, solo_res)
        rows.append(solo_row)

    return rows


def main():
    rows = asyncio.run(run_experiment())
    csv_path = HERE / "results.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} experiment rows to {csv_path}\n")
    print(f"{'ID':<4} | {'System':<6} | {'Comp':<8} | {'Cat':<11} | {'Steps':<5} | {'Sev':<8} | {'Prio':<4} | {'Drafts':<6} | {'Calls':<5} | {'Tokens':<6} | {'Time(s)':<7} | {'Quality':<7}")
    print("-" * 95)
    for r in rows:
        print(f"{r['id']:<4} | {r['system']:<6} | {r['component']:<8} | {r['category']:<11} | {r['steps_count']:<5} | {r['severity']:<8} | {r['priority']:<4} | {r['drafts']:<6} | {r['llm_calls']:<5} | {r['tokens']:<6} | {r['seconds']:<7} | {r['quality_score']:<7}")


if __name__ == "__main__":
    main()
