---
tags: [безпека, rate-limiting, 429, dos]
aliases: [Rate Limiting, Обмеження частоти запитів]
source: "RFC 6585: Additional HTTP Status Codes; Cloudflare Rate Limiting Architecture."
updated: 2026-11-01
---
# Rate Limiting and 429

Захист сервісу Nom-Nom-Save від перевантаження, DoS-атак та брутфорсу облікових записів.

## Ключові положення
- **Алгоритм Token Bucket / Leaky Bucket**:
  - Для публічних ендпоінтів (`/api/v1/boxes`): 100 запитів на хвилину на IP.
  - Для ендпоінтів автентифікації (`/api/v1/auth/login`): 5 спроб на хвилину на IP.
- **Стандартні заголовки відповіді**:
  - `RateLimit-Limit`: максимальна кількість запитів за період.
  - `RateLimit-Remaining`: залишок дозволених запитів.
  - `RateLimit-Reset`: час у секундах до відновлення квоти.
  - `Retry-After`: обов'язковий заголовок при перевищенні (статус `429 Too Many Requests`).

## Приклад
При 6-й невдалій спробі логіну поспіль сервер повертає:
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 60
Content-Type: application/problem+json

{
  "type": "https://api.nomnomsave.ua/errors/rate-limit-exceeded",
  "title": "Too Many Requests",
  "status": 429,
  "detail": "Login attempt limit exceeded. Please try again in 60 seconds."
}
```

## Пов'язані нотатки
- [[Error-Status-Codes-Mapping]]
- [[CSRF-and-CORS-Protection]]
- [[Authentication-and-JWT-Handling]]
