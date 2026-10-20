import re

HTTP_STATUSES: dict[str, str] = {
    "200": (
        "200 OK — Успішне виконання запиту. Стандартна відповідь для успішних REST-запитів GET, "
        "коли тіло відповіді містить запитуваний ресурс (наприклад, GET /api/v1/baskets повертає список кошиків), "
        "або PUT/PATCH, якщо повертається оновлена сутність."
    ),
    "201": (
        "201 Created — Успішне створення нового ресурсу на сервері. Застосовується після обробки запитів POST "
        "(наприклад, POST /api/v1/orders для оформлення замовлення або POST /api/v1/auth/register). "
        "Сервер повертає створений об'єкт та заголовок Location."
    ),
    "204": (
        "204 No Content — Запит успішно виконано, але відповідь не містить тіла. Застосовується для операцій DELETE "
        "(наприклад, DELETE /api/v1/cart/items/{id} для видалення позиції) або оновлень без необхідності "
        "повертати змінені дані клієнту."
    ),
    "301": (
        "301 Moved Permanently — Запитуваний ресурс остаточно переміщено за новим URI, вказаним у заголовку Location. "
        "Пошукові системи та клієнти оновлюють свої посилання на нову адресу."
    ),
    "304": (
        "304 Not Modified — Ресурс не змінювався з моменту попереднього запиту. Використовується для умовного кешування "
        "(заголовки If-None-Match / ETag та If-Modified-Since), тіло відповіді не надсилається для економії трафіку."
    ),
    "400": (
        "400 Bad Request — Некоректний синтаксис запиту або помилка валідації вхідних DTO. Сервер не може "
        "обробити запит через помилку на стороні клієнта (наприклад, відсутні обов'язкові поля, некоректний JSON "
        "або невідповідність типам схеми в POST /api/v1/orders/checkout)."
    ),
    "401": (
        "401 Unauthorized — Відсутня або недійсна автентифікація. Клієнт не надав дійсний токен доступу (Bearer JWT) "
        "у заголовку Authorization або термін дії токена минув. Захищені ендпоінти вимагають входу в систему."
    ),
    "403": (
        "403 Forbidden — Запит автентифіковано, але користувач не має достатніх прав (прав доступу / ролі) "
        "для виконання цієї операції над ресурсом. Наприклад, покупець намагається змінити статус ресторану "
        "або замовлення іншого користувача."
    ),
    "404": (
        "404 Not Found — Запитуваний ресурс не знайдено на сервері. Застосовується, коли за вказаним ідентифікатором "
        "у маршруті (наприклад, GET /api/v1/orders/{id}) сутність відсутня в базі даних або маршрут не існує."
    ),
    "409": (
        "409 Conflict — Конфлікт запиту з поточним станом сервера. Виникає у REST API при порушенні унікальності "
        "чи бізнес-правил (наприклад, спроба забронювати останній кошик із залишками їжі, який вже зарезервував інший клієнт)."
    ),
    "500": (
        "500 Internal Server Error — Внутрішня непередбачена помилка сервера. Виникає при збоях бази даних, необроблених "
        "винятках у коді контролерів або аварійному завершенні сервісних процесів."
    ),
    "503": (
        "503 Service Unavailable — Сервіс тимчасово недоступний через технічне обслуговування або перевантаження. "
        "Наприклад, коли сторонній платіжний шлюз тимчасово не відповідає або база даних перебуває на регламентних роботах."
    ),
}

STATUS_CLASSES: dict[str, list[str]] = {
    "2xx": ["200", "201", "204"],
    "3xx": ["301", "304"],
    "4xx": ["400", "401", "403", "404", "409"],
    "5xx": ["500", "503"],
}

NAME_ALIASES: dict[str, str] = {
    "ok": "200",
    "created": "201",
    "nocontent": "204",
    "no-content": "204",
    "movedpermanently": "301",
    "moved-permanently": "301",
    "notmodified": "304",
    "not-modified": "304",
    "badrequest": "400",
    "bad-request": "400",
    "unauthorized": "401",
    "forbidden": "403",
    "notfound": "404",
    "not-found": "404",
    "conflict": "409",
    "internalservererror": "500",
    "internal-server-error": "500",
    "serviceunavailable": "503",
    "service-unavailable": "503",
}

NOT_FOUND = "NOT_FOUND"


def normalize_code(code: str) -> str:
    """Зводить різні варіанти написання ('400', '400 Bad Request', 'bad_request', ' 404 ') до числового коду."""
    cleaned = code.strip().lower()
    match = re.match(r"^(\d{3})", cleaned)
    if match and match.group(1) in HTTP_STATUSES:
        return match.group(1)

    slug = re.sub(r"[\s_]+", "-", cleaned)
    slug_compact = re.sub(r"[\s_-]+", "", cleaned)
    if slug in NAME_ALIASES:
        return NAME_ALIASES[slug]
    if slug_compact in NAME_ALIASES:
        return NAME_ALIASES[slug_compact]
    return cleaned


def lookup_http_status(code: str) -> str:
    """Return verified information about one HTTP status code.

    Use it when the user asks about a specific HTTP status code such as
    200, 201, 204, 301, 304, 400, 401, 403, 404, 409, 500, or 503.

    Args:
        code: HTTP status code, for example "200", "400" or "404 Not Found".

    Returns:
        "<code>: <description>" or a line starting with NOT_FOUND.
    """
    key = normalize_code(code)
    if key not in HTTP_STATUSES:
        return f"{NOT_FOUND}: no verified information about HTTP status '{code}'."
    return f"{key}: {HTTP_STATUSES[key]}"


def list_status_class(status_class: str) -> str:
    """Return verified HTTP status codes for a given class.

    Use it when user asks to list all status codes in a specific class such as
    "2xx" (Success), "3xx" (Redirection), "4xx" (Client Errors), or "5xx" (Server Errors).

    Args:
        status_class: HTTP status class, e.g. "2xx", "3xx", "4xx", "5xx", "4", "400s".

    Returns:
        Comma-separated codes with titles, or NOT_FOUND line.
    """
    cleaned = status_class.strip().lower()
    match = re.match(r"^([1-5])(xx|\d\d)?$", cleaned)
    cls_key = f"{match.group(1)}xx" if match else cleaned

    if cls_key not in STATUS_CLASSES:
        return f"{NOT_FOUND}: no status codes found for class '{status_class}'."

    codes = STATUS_CLASSES[cls_key]
    items = [
        f"{c} ({HTTP_STATUSES[c].split(' — ')[0].split(' ', 1)[1]})" for c in codes
    ]
    return f"Class {cls_key} contains: " + ", ".join(items)


def list_all_statuses() -> str:
    """Return identifiers of all HTTP status codes known to the environment."""
    return ", ".join(sorted(HTTP_STATUSES.keys()))
