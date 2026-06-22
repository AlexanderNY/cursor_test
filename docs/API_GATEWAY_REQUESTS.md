# API Gateway — входящие и исходящие запросы

Gateway принимает запросы от клиентов (ui-app, scheduler, др.) и проксирует их в downstream-сервисы через `ProxyService` (httpx). Публичные эндпоинты не требуют JWT; остальные — защищены.

---

## 1. Входящие запросы (что принимает Gateway)

Клиенты обращаются к Gateway (напр. ui-app через `/api` → proxy → Gateway). Ниже — фактические пути на Gateway.

### 1.1 Собственные эндпоинты (без проксирования)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/` | — | Корень, статус сервиса |
| GET | `/health` | — | Healthcheck Gateway |
| GET | `/routes` | — | Список маршрутов (отладка) |

---

### 1.2 Auth (`/auth`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| POST | `/auth/register` | Нет | Регистрация |
| POST | `/auth/login` | Нет | Вход |
| POST | `/auth/refresh` | Нет | Обновление токена |
| POST | `/auth/logout` | Да | Выход (текущая сессия) |
| GET | `/auth/profile` | Да | Получить профиль |
| POST | `/auth/profile` | Да | Обновить профиль |
| POST | `/auth/verify` | Нет | Верификация email |
| POST | `/auth/reset-password` | Нет | Запрос сброса пароля |
| POST | `/auth/reset-password/confirm` | Нет | Подтверждение сброса пароля |
| POST | `/auth/all-logout` | Да | Выход со всех устройств |

---

### 1.3 Core (`/core`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/core/statistics` | Да | Статистика |
| GET | `/core/healthcheck` | Да | Healthcheck (→ core `/healthchecks`) |
| GET | `/core/healthchecks` | Да | Healthcheck |
| GET | `/core/schedules` | Да | Сводка расписаний |

---

### 1.4 WordPress (`/wp`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/wp/profile` | Да | Профиль WP |
| POST | `/wp/profile` | Да | Сохранить профиль WP |
| GET | `/wp/posts` | Да | Список постов |
| POST | `/wp/post` | Да | Создать пост |

---

### 1.5 Telegram (`/tg`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/tg/profile` | Да | Профиль Telegram |
| POST | `/tg/profile` | Да | Сохранить профиль |
| POST | `/tg/post` | Да | Опубликовать пост |

---

### 1.6 VKontakte (`/vk`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/vk/profile` | Да | Профиль VK |
| POST | `/vk/profile` | Да | Сохранить профиль |
| POST | `/vk/post` | Да | Опубликовать пост |

---

### 1.7 Twitter (`/tw`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/tw/profile` | Да | Профиль Twitter |
| POST | `/tw/profile` | Да | Сохранить профиль |
| POST | `/tw/post` | Да | Опубликовать пост |

---

### 1.8 Custom URL (`/curl`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/curl/settings` | Да | Настройки |
| POST | `/curl/settings` | Да | Сохранить настройки |

---

### 1.9 Create Post (`/cpost`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/cpost/profile` | Да | Профиль |
| POST | `/cpost/profile` | Да | Сохранить профиль |
| POST | `/cpost/post` | Да | Создать пост |

---

### 1.10 Test (`/test`)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| GET | `/test/products` | Да | Список продуктов |
| GET | `/test/search/{order_id}` | Да | Поиск заказа |
| POST | `/test/submit` | Да | Отправить тест |

---

### 1.11 Bot schedule (прокси к ботам)

| Метод | Путь | JWT | Описание |
|-------|------|-----|----------|
| POST | `/tg-bot/schedule` | Да | Расписание → tg-bot |
| POST | `/wp-bot/schedule` | Да | Расписание → wp-bot |
| POST | `/vk-bot/schedule` | Да | Расписание → vk-bot |
| POST | `/url-bot/schedule` | Да | Расписание → url-bot |

---

### 1.12 Stubs (501 Not Implemented)

Заглушки для сервисов, которые ещё не реализованы или не подключены. Любой метод, возвращают 501.

| Префикс | Методы | JWT |
|---------|--------|-----|
| `/scheduler`, `/scheduler/{path}` | GET, POST, PUT, DELETE, PATCH | Нет |
| `/tg-bot`, `/tg-bot/{path}` | GET, POST, … | Нет |
| `/vk-bot`, `/vk-bot/{path}` | GET, POST, … | Нет |
| `/wp-bot`, `/wp-bot/{path}` | GET, POST, … | Нет |
| `/url-bot`, `/url-bot/{path}` | GET, POST, … | Нет |

*Примечание:* `/tg-bot/schedule` и аналогичные обрабатываются **bot_proxy** (прокси к ботам), а не stubs. Stubs перехватывают остальные пути под этими префиксами.

---

## 2. Исходящие запросы (куда Gateway проксирует)

Все исходящие запросы выполняются через `ProxyService` (httpx) к URL из `config.Settings`. Пробрасываются заголовки (кроме hop-by-hop); при наличии JWT в `Authorization` добавляется `X-User-Id` из токена.

### 2.1 → Auth (`AUTH_SERVICE_URL`)

| Входящий (Gateway) | Исходящий (Auth) | Примечание |
|--------------------|------------------|------------|
| POST `/auth/register` | POST `{AUTH}/register` | — |
| POST `/auth/login` | POST `{AUTH}/login` | — |
| POST `/auth/refresh` | POST `{AUTH}/refresh` | — |
| POST `/auth/logout` | POST `{AUTH}/logout` | — |
| GET `/auth/profile` | GET `{AUTH}/profile` | — |
| POST `/auth/profile` | **PUT** `{AUTH}/profile` | override_method |
| POST `/auth/verify` | POST `{AUTH}/verify-token` | путь другой |
| POST `/auth/reset-password` | POST `{AUTH}/reset-password` | — |
| POST `/auth/reset-password/confirm` | POST `{AUTH}/reset-password/confirm` | — |
| POST `/auth/all-logout` | POST `{AUTH}/all_logout` | all_logout |

---

### 2.2 → Core (`CORE_SERVICE_URL`)

| Входящий (Gateway) | Исходящий (Core) |
|--------------------|------------------|
| GET `/core/statistics` | GET `{CORE}/statistics` |
| GET `/core/healthcheck` | GET `{CORE}/healthchecks` |
| GET `/core/healthchecks` | GET `{CORE}/healthchecks` |
| GET `/core/schedules` | GET `{CORE}/schedules` |
| GET `/wp/profile` | GET `{CORE}/wp/profile` |
| POST `/wp/profile` | POST `{CORE}/wp/profile` |
| GET `/wp/posts` | GET `{CORE}/wp/posts` |
| POST `/wp/post` | POST `{CORE}/wp/post` |
| GET `/tg/profile` | GET `{CORE}/tg/profile` |
| POST `/tg/profile` | POST `{CORE}/tg/profile` |
| POST `/tg/post` | POST `{CORE}/tg/post` |
| GET `/vk/profile` | GET `{CORE}/vk/profile` |
| POST `/vk/profile` | POST `{CORE}/vk/profile` |
| POST `/vk/post` | POST `{CORE}/vk/post` |
| GET `/tw/profile` | GET `{CORE}/tw/profile` |
| POST `/tw/profile` | POST `{CORE}/tw/profile` |
| POST `/tw/post` | POST `{CORE}/tw/post` |
| GET `/curl/settings` | GET `{CORE}/curl/settings` |
| POST `/curl/settings` | POST `{CORE}/curl/settings` |
| GET `/cpost/profile` | GET `{CORE}/cpost/profile` |
| POST `/cpost/profile` | POST `{CORE}/cpost/profile` |
| POST `/cpost/post` | POST `{CORE}/cpost/post` |

---

### 2.3 → SelectCB (`SELECTCB_SERVICE_URL`)

| Входящий (Gateway) | Исходящий (SelectCB) |
|--------------------|----------------------|
| GET `/test/products` | GET `{SELECTCB}/test/products` |
| GET `/test/search/{order_id}` | GET `{SELECTCB}/test/search/{order_id}` |
| POST `/test/submit` | POST `{SELECTCB}/test/submit` |

---

### 2.4 → Боты (tg-bot, wp-bot, vk-bot, url-bot)

| Входящий (Gateway) | Исходящий |
|--------------------|-----------|
| POST `/tg-bot/schedule` | POST `{TG_BOT_SERVICE_URL}/schedule` |
| POST `/wp-bot/schedule` | POST `{WP_BOT_SERVICE_URL}/schedule` |
| POST `/vk-bot/schedule` | POST `{VK_BOT_SERVICE_URL}/schedule` |
| POST `/url-bot/schedule` | POST `{URL_BOT_SERVICE_URL}/schedule` |

---

## 3. Сводка

| Направление | Количество |
|-------------|------------|
| **Входящие** (без stubs) | 3 собственных + 10 auth + 4 core + 4 wp + 3 tg + 3 vk + 3 tw + 2 curl + 3 cpost + 3 test + 4 bot = **46** |
| **Исходящие** | 10 → Auth, 22 → Core, 3 → SelectCB, 4 → Bots = **39** |
| **Stubs** | 5 префиксов (scheduler, tg-bot, vk-bot, wp-bot, url-bot), 501 на любые методы |

---

## 4. Конфиг URL сервисов (`config.py`)

| Переменная | Назначение |
|------------|------------|
| `AUTH_SERVICE_URL` | Auth |
| `CORE_SERVICE_URL` | Core |
| `SCHEDULER_SERVICE_URL` | Scheduler (пока только stubs) |
| `TG_BOT_SERVICE_URL` | tg-bot |
| `VK_BOT_SERVICE_URL` | vk-bot |
| `WP_BOT_SERVICE_URL` | wp-bot |
| `URL_BOT_SERVICE_URL` | url-bot |
| `SELECTCB_SERVICE_URL` | selectcb (test) |
