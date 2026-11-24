"""Test fixtures with pre-configured agent responses and bug report samples."""

REQUEST = (
    "При одночасному бронюванні останнього акційного продуктового набору двома користувачами "
    "через POST /api/v1/orders/reserve обидва отримують HTTP 200 OK і підтвердження, "
    "що призводить до продажу одного лота двічі (double-booking) та розбіжності залишків у пекарні."
)

GOOD_CLASSIFICATION = {
    "component": "orders",
    "category": "Functional",
    "title": "Овербукінг лотів при одночасному резервуванні замовлень",
    "summary": "Відсутнє песимістичне блокування залишку лота при виклику /api/v1/orders/reserve.",
    "suggested_severity": "High",
}

GOOD_REPRODUCTION = {
    "steps_to_reproduce": [
        "Створити акційний лот з доступною кількістю quantity=1 у пекарні.",
        "Надіслати два паралельні асинхронні POST запити на /api/v1/orders/reserve від імені різних користувачів.",
        "Зафіксувати відповіді обох HTTP-запитів.",
        "Перевірити фінальний залишок лота в базі даних (фактично стає -1 замість відхилення другого запиту).",
    ],
    "http_method": "POST",
    "endpoint": "/api/v1/orders/reserve",
    "request_payload": '{"lot_id": 77, "quantity": 1, "customer_id": 1042}',
    "expected_status": 409,
    "actual_status": 200,
}

GOOD_IMPACT = {
    "business_impact": "Financial",
    "blast_radius": "System-wide",
    "security_risk": "Порушення узгодженості даних інвентарю та потенційний овербукінг продуктів із фінансовими поверненнями.",
    "affected_stakeholders": ["Покупці", "Партнерські заклади харчування", "Бухгалтерія"],
    "financial_risk_score": 4,
}

APPROVE_VERDICT = {
    "decision": "APPROVE",
    "severity": "Critical",
    "priority": "P1",
    "triage_rationale": (
        "Дефект спричиняє овербукінг лотів харчування з високим фінансовим і репутаційним ризиком. "
        "Кроки відтворення деталізовані та підтверджують стан гонитви. Severity=Critical, Priority=P1."
    ),
    "comments": [],
}

REVISE_VERDICT = {
    "decision": "REVISE",
    "severity": "High",
    "priority": "P2",
    "triage_rationale": "Кроки відтворення не містять обов'язкового заголовка Idempotency-Key.",
    "comments": ["Уточніть наявність заголовка Idempotency-Key у вхідному HTTP-запиті."],
}

BAD_FORMAT_CLASSIFICATION = {
    "component": "invalid_component",
    "category": "Functional",
    "title": "Некоректний компонент",
    "summary": "Опис дефекту",
    "suggested_severity": "Medium",
}

BAD_FORMAT_REPRODUCTION = {
    "steps_to_reproduce": ["Лише один крок"],
    "http_method": "POST",
    "endpoint": "bad_endpoint_without_api_prefix",
    "request_payload": "None",
    "expected_status": 200,
    "actual_status": 500,
}

BAD_FORMAT_VERDICT = {
    "decision": "APPROVE",
    "severity": "Catastrophic",  # Invalid severity
    "priority": "Urgent",        # Invalid priority
    "triage_rationale": "Невалідні severity і priority",
    "comments": [],
}
