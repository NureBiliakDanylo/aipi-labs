---
tags: [дизайн, uri, ресурси, rest]
aliases: [Resource Naming, Іменування ресурсів]
source: "RESTful Web APIs, Richardson & Ruby; Google Cloud API Design Guide."
updated: 2026-11-01
---
# Resource Naming Conventions

Правильне іменування ресурсів робить REST API інтуїтивно зрозумілим, прогнозованим та легким для інтеграції.

## Ключові положення
- **Іменники у множині**: ресурси позначаються іменниками у множині (`/boxes`, `/orders`, `/restaurants`).
- **Жодних дієслів у шляхах**: дію визначає метод HTTP (GET — прочитати, POST — створити, DELETE — видалити), тому замість `/createOrder` використовується `POST /orders`.
- **Ієрархія сутностей (Sub-resources)**: підпорядковані сутності вкладаються в батьківські: `/restaurants/{id}/boxes`.
- **Kebab-case для сегментів**: розділення слів дефісом (`/food-categories`, `/order-items`).
- **Фільтрація та сортування**: параметри фільтрації передаються в query string: `/api/v1/boxes?city=kharkiv&status=AVAILABLE`.

## Приклад
У Nom-Nom-Save отримання відгуків для конкретного ресторану реалізовано за URI `GET /api/v1/restaurants/rest_88/reviews`.

## Пов'язані нотатки
- [[REST-Architectural-Constraints]]
- [[Boxes-API-Design]]
- [[Orders-API-and-FSM]]
