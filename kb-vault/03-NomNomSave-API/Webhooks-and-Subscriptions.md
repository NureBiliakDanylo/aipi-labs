---
tags: [nomnomsave, webhooks, асинхронність, підписки]
aliases: [Webhooks, Події підписок]
source: "Webhooks Standard, Webhooks.fyi; Stripe Webhook Best Practices."
updated: 2026-11-01
---
# Webhooks and Subscriptions

Асинхронне сповіщення зовнішніх систем та клієнтів про зміну стану замовлень та оплати.

## Ключові положення
- **Зворотні виклики (Webhooks)**: сервер надсилає HTTP POST на зареєстрований URL партнера при зміні статусу замовлення (`order.ready`, `order.cancelled`, `payment.succeeded`).
- **Підпис подій**: кожен webhook містить заголовок `X-Signature-SHA256` (HMAC від payload із секретом клієнта) для верифікації цілісності та автентичності.
- **Повторні спроби (Retry policy)**: при неотриманні статусу `2xx` сервер використовує експоненційне відтермінування (Exponential Backoff: 1 хв, 5 хв, 30 хв, 2 год).

## Приклад
При оплаті замовлення платіжний шлюз надсилає виклик на `/api/v1/webhooks/payments`, після чого статус замовлення автоматично переходить у `CONFIRMED`.

## Пов'язані нотатки
- [[Orders-API-and-FSM]]
- [[Idempotency-and-Safe-Methods]]
- [[Rate-Limiting-and-429]]
