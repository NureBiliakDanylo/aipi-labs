---
tags: [nomnomsave, boxes, api, rest]
aliases: [Boxes API, Ендпоінти боксів]
source: "Специфікація підсистеми Food Box Management Nom-Nom-Save, 2026."
updated: 2026-11-01
---
# Boxes API Design

Підсистема Boxes API відповідає за життєвий цикл продуктових боксів-сюрпризів зі знижками від закладів харчування.

## Ключові положення
- **Ендпоінти**:
  - `GET /api/v1/boxes` — публічний список активних боксів з фільтрацією за геопозицією, категорією та часом самовивозу.
  - `GET /api/v1/boxes/{id}` — детальна інформація про бокс, склад, алергени та заклад.
  - `POST /api/v1/restaurants/{id}/boxes` — створення нового боксу (доступно лише ролі `RESTAURANT_MANAGER`).
  - `PATCH /api/v1/boxes/{id}` — часткове оновлення ціни або залишку порцій (`quantity`).
  - `DELETE /api/v1/boxes/{id}` — деактивація пропозиції.
- **Статуси доступності**: `AVAILABLE`, `RESERVED`, `SOLD_OUT`, `EXPIRED`.

## Приклад
Запит на пошук боксів поблизу користувача:
`GET /api/v1/boxes?lat=50.005&lng=36.229&radiusKm=5&status=AVAILABLE`
Повертає масив об'єктів з розрахованою відстанню та часовим вікном видачі `pickupWindowStart`/`pickupWindowEnd`.

## Пов'язані нотатки
- [[Resource-Naming-Conventions]]
- [[Orders-API-and-FSM]]
- [[Authentication-and-JWT-Handling]]
