---
tags: [безпека, jwt, auth, nomnomsave]
aliases: [JWT Auth, Автентифікація]
source: "RFC 7519: JSON Web Token; Auth0 Architecture Guide."
updated: 2026-11-01
---
# Authentication and JWT Handling

Безпека доступу до API Nom-Nom-Save реалізована на базі протоколів OAuth 2.0 та JSON Web Tokens (JWT).

## Ключові положення
- **Двотокенна модель**:
  - `Access Token`: короткоживучий токен (термін дії 15 хвилин), передається в заголовку `Authorization: Bearer <token>`. Містить `userId`, `role` (`CUSTOMER`, `RESTAURANT_MANAGER`, `ADMIN`), `email`.
  - `Refresh Token`: довгоживучий токен (14 днів), зберігається в `HttpOnly`, `Secure`, `SameSite=Strict` cookie для захисту від XSS.
- **Рольовий контроль доступу (RBAC)**:
  - Захист на рівні middleware: перевірка валідності підпису RSA-256 (RS256) та наявності необхідних scope/claims.
- **Коди помилок авторизації**:
  - `401 Unauthorized`: токен відсутній, прострочений або має невалідний цифровий підпис. Заголовок обов'язково містить `WWW-Authenticate: Bearer error="invalid_token"`.
  - `403 Forbidden`: користувач автентифікований, але його роль не має прав на операцію (наприклад, звичайний клієнт намагається відредагувати бокс ресторану).

## Приклад
Спроба оновити бокс без токена повертає:
`401 Unauthorized` із тілом у форматі Problem Details:
`detail: "Authentication token is missing or malformed"`.

## Пов'язані нотатки
- [[Error-Status-Codes-Mapping]]
- [[REST-Architectural-Constraints]]
- [[CSRF-and-CORS-Protection]]
