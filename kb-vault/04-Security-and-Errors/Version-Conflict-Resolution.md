---
tags: [конфлікти, версіонування, etag, rest]
aliases: [Version Conflict, Конфлікт версій]
source: "RFC 9110 Section 13: Conditional Requests; Martin Fowler: Patterns of Enterprise Application Architecture."
updated: 2026-11-01
---
# Version Conflict Resolution

Стратегії виявлення та вирішення конфліктів одночасного редагування ресурсів у REST API.

## Ключові положення
- **Проблема «втраченого оновлення» (Lost Update)**: коли два оператори ресторану одночасно редагують залишок страв в одному боксі, перезаписуючи зміни один одного.
- **Умовні запити за RFC 9110**:
  - Сервер надає заголовок `ETag: W/"v4-hash"` при читанні сутності.
  - При оновленні (`PUT` чи `PATCH`) клієнт обов'язково надсилає заголовок `If-Match: W/"v4-hash"`.
  - Якщо сутність уже змінилася, сервер відхиляє запит кодом `412 Precondition Failed` або `409 Conflict`.
- **Формат тіла відповіді при конфлікті версій**:
  Повертається об'єкт Problem Details, що містить поточну актуальну версію ресурсу (`currentVersion`) та версію клієнта (`providedVersion`), дозволяючи клієнту виконати 3-way merge або запитати користувача.

## Приклад
```json
{
  "type": "https://api.nomnomsave.ua/errors/version-conflict",
  "title": "Version Conflict",
  "status": 409,
  "detail": "The resource has been modified by another process. Your version: v4, current version: v5.",
  "instance": "/api/v1/boxes/bx_102"
}
```

## Пов'язані нотатки
- [[State-Machine-and-Conflict-Handling]]
- [[RFC-7807-Problem-Details]]
- [[Error-Status-Codes-Mapping]]
