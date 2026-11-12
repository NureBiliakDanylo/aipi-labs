---
tags: [архітектура, fsm, конфлікти, 409]
aliases: [FSM, Стейт-машина, Конфлікти станів]
source: "Enterprise Integration Patterns, Hohpe & Woolf; REST in Practice."
updated: 2026-11-01
---
# State Machine and Conflict Handling

Коректна обробка переходів між станами бізнес-сутностей запобігає пошкодженню даних та race conditions.

## Ключові положення
- **Скінченний автомат замовлення (Order FSM)**:
  `CREATED` → `CONFIRMED` → `READY_FOR_PICKUP` → `COMPLETED`.
  Альтернативні фінальні стани: `CANCELLED` (клієнтом або рестораном), `EXPIRED` (прострочено час видачі).
- **Код 409 Conflict**: якщо клієнт намагається виконати неможливий перехід (наприклад, скасувати замовлення у стані `COMPLETED`), сервер зобов'язаний повернути `409 Conflict`.
- **Оптимістичне блокування (Optimistic Locking)**: використання заголовків `If-Match` та `ETag` для запобігання ситуаціям «втраченого оновлення» (Lost Update).

## Приклад
При спробі ресторану змінити статус замовлення, яке вже скасоване клієнтом (`CANCELLED`), бекенд повертає:
`409 Conflict: Cannot transition order ord_55 from CANCELLED to CONFIRMED`.

## Пов'язані нотатки
- [[Orders-API-and-FSM]]
- [[RFC-7807-Problem-Details]]
- [[Error-Status-Codes-Mapping]]
