---
tags: [стандарти, помилки, rfc7807, rfc9457]
aliases: [Problem Details, RFC 7807, RFC 9457]
source: "RFC 7807 / RFC 9457: Problem Details for HTTP APIs, IETF. https://www.rfc-editor.org/rfc/rfc9457"
updated: 2026-11-01
---
# RFC 7807 Problem Details

RFC 7807 (та його оновлення RFC 9457) визначає стандартний JSON-формат для опису деталей помилок у відповідях HTTP API (`application/problem+json`).

## Ключові положення
- **Обов'язкові та рекомендовані поля**:
  - `type`: URI, що ідентифікує тип помилки та веде до людиночитаної документації.
  - `title`: Короткий підсумок типу помилки (не повинен змінюватися від запиту до запиту).
  - `status`: Числовий код стану HTTP (дублює код у заголовку відповіді).
  - `detail`: Людиночитане пояснення конкретного виникнення проблеми.
  - `instance`: URI конкретної операції чи ресурсу, де сталась помилка.
- **Розширюваність**: дозволено додавати специфічні для домену поля (наприклад, `invalidParams` або `validationErrors`).

## Приклад
Відповідь бекенду Nom-Nom-Save при спробі забронювати вже викуплений бокс:
```json
{
  "type": "https://api.nomnomsave.ua/errors/box-already-sold",
  "title": "Conflict State",
  "status": 409,
  "detail": "Box with ID bx_404 has already been reserved by another customer",
  "instance": "/api/v1/orders"
}
```

## Пов'язані нотатки
- [[Error-Status-Codes-Mapping]]
- [[State-Machine-and-Conflict-Handling]]
