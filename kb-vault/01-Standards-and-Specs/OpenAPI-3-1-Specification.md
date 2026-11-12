---
tags: [стандарти, openapi, документація, rest]
aliases: [OpenAPI 3.1, OAS 3.1]
source: "OpenAPI Specification v3.1.0, OpenAPI Initiative, 2021. https://spec.openapis.org/oas/v3.1.0"
updated: 2026-11-01
---
# OpenAPI 3.1 Specification

OpenAPI 3.1 — це стандарт опису машиночитаних інтерфейсів REST API, що повністю узгоджений із JSON Schema Draft 2020-12.

## Ключові положення
- **Повна сумісність із JSON Schema**: підтримуються всі валідаційні ключові слова (`unevaluatedProperties`, `prefixItems`, `pattern`, `minimum`).
- **Специфікація відповідей**: дозволяє чітко типізувати тіла успішних відповідей та стандартизовані об'єкти помилок через `$ref`.
- **Компоненти безпеки**: декларація схем безпеки через `securitySchemes` (Bearer JWT, OAuth2, API Keys).

## Приклад
В API Nom-Nom-Save схема боксів із залишками описується об'єктом `FoodBoxResponse`, де обов'язковими полями визначено `id`, `restaurantId`, `price`, `discountPrice`, а структура помилок посилається на [[RFC-7807-Problem-Details]].

## Пов'язані нотатки
- [[RFC-9110-HTTP-Semantics]]
- [[RFC-7807-Problem-Details]]
- [[Boxes-API-Design]]
