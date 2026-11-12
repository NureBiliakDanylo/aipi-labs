---
tags: [безпека, cors, csrf, owasp]
aliases: [CORS, CSRF, Веб-безпека]
source: "OWASP Top 10: Cross-Site Request Forgery; MDN Web Docs: CORS."
updated: 2026-11-01
---
# CSRF and CORS Protection

Механізми захисту від підробки міжсайтових запитів (CSRF) та політика безпечного спільного використання ресурсів між різними джерелами (CORS).

## Ключові положення
- **Захист від CSRF**:
  - Токени автентифікації передаються в заголовку `Authorization: Bearer`, що автоматично захищає API від класичного CSRF (браузер не підставляє заголовок автоматично при cross-site запитах).
  - Cookie з `Refresh Token` обов'язково маркується `SameSite=Strict`.
- **Конфігурація CORS**:
  - `Access-Control-Allow-Origin`: суворо білий список дозволених доменів клієнта (`https://nomnomsave.ua`, `https://app.nomnomsave.ua`). Заборонено використання wildcard `*` разом з передачею credentials.
  - `Access-Control-Allow-Methods`: GET, POST, PUT, PATCH, DELETE, OPTIONS.
  - `Access-Control-Allow-Headers`: Content-Type, Authorization, Idempotency-Key.
  - `Access-Control-Max-Age`: 86400 (кешування Preflight запиту OPTIONS на 24 години).

## Приклад
Браузер клієнта перед виконанням `POST /api/v1/orders` надсилає автоматичний передзапит:
```http
OPTIONS /api/v1/orders HTTP/1.1
Origin: https://app.nomnomsave.ua
Access-Control-Request-Method: POST
```
Сервер відповідає `204 No Content` із відповідними CORS-заголовками.

## Пов'язані нотатки
- [[Authentication-and-JWT-Handling]]
- [[Rate-Limiting-and-429]]
- [[REST-Architectural-Constraints]]
