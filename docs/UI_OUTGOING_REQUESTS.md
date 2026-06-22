# Исходящие запросы ui-app

Все запросы идут через `apiClient` (axios) на базовый URL `/api` (Vite proxy → API Gateway).  
В interceptor при 401 + истечении токена выполняется отдельный `POST /api/auth/refresh`.

---

## Auth (`/auth/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| POST | `/auth/login` | `LoginCredentials` | auth-service | Вход |
| POST | `/auth/register` | `RegisterCredentials` | auth-service | Регистрация |
| POST | `/auth/logout` | `{ refresh_token }` | auth-service | Выход (текущая сессия) |
| POST | `/auth/all-logout` | — | auth-service | Выход со всех устройств |
| GET | `/auth/profile` | — | auth-service | Получить профиль пользователя |
| POST | `/auth/profile` | `ProfileUpdate` | auth-service | Обновить профиль |
| POST | `/auth/reset-password` | `{ email }` | auth-service | Запрос сброса пароля |
| POST | `/auth/reset-password/confirm` | `{ token, new_password }` | auth-service | Подтверждение сброса пароля |
| POST | `/auth/refresh` | `{ refresh_token }` | api-client (interceptor) | Обновление access token |
| POST | `/auth/verify` | `{ code }` | auth-service | Подтверждение email |

---

## Core (`/core/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/core/healthchecks` | — | core-service | Healthcheck |
| GET | `/core/statistics` | — | core-service | Статистика |

---

## WordPress (`/wp/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/wp/profile` | — | wordpress-service | Получить профиль WP |
| POST | `/wp/profile` | `WordPressProfile` | wordpress-service | Сохранить профиль WP |
| POST | `/wp/post` | `WordPressPost` (+ файлы изображений) | wordpress-service | Создать пост с возможностью загрузки изображений в контент и caption |
| GET | `/wp/posts` | — | wordpress-service | Список постов |

---

## Telegram (`/tg/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/tg/profile` | — | telegram-service | Получить конфиг TG (404 → null) |
| POST | `/tg/profile` | `TelegramConfig` | telegram-service | Сохранить конфиг |
| POST | `/tg/post` | `TelegramPost` | telegram-service | Опубликовать пост |

---

## VKontakte (`/vk/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/vk/profile` | — | vkontakte-service | Получить профиль VK (404 → null) |
| POST | `/vk/profile` | `VKontakteProfile` | vkontakte-service | Сохранить профиль |
| POST | `/vk/post` | `VKontaktePost` | vkontakte-service | Опубликовать пост |

---

## Instagram (`/instagram/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/instagram/profile` | — | instagram-service | Получить профиль Instagram (404 → null) |
| POST | `/instagram/profile` | `InstagramProfile` | instagram-service | Сохранить профиль |
| GET | `/instagram/posts` | — | instagram-service | Список постов (params: limit, offset) |
| GET | `/instagram/post/{id}` | — | instagram-service | Один пост |
| POST | `/instagram/post` | `InstagramPost` или FormData (caption, images[]) | instagram-service | Создать пост (caption до 2200 символов) |
| PUT | `/instagram/post/{id}` | `InstagramPostUpdate` | instagram-service | Обновить пост |
| DELETE | `/instagram/post/{id}` | — | instagram-service | Удалить пост (status=deleted) |

---

## Дзен (`/dzen/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/dzen/profile` | — | dzen-service | Получить профиль Дзен (404 → null) |
| POST | `/dzen/profile` | `DzenProfile` | dzen-service | Сохранить профиль |
| GET | `/dzen/posts` | — | dzen-service | Список постов (params: limit, offset) |
| GET | `/dzen/post/{id}` | — | dzen-service | Один пост |
| POST | `/dzen/post` | `DzenPost` или FormData (text, title, images[], videos[]) | dzen-service | Создать пост (до 1500 символов, картинки и видео) |
| PUT | `/dzen/post/{id}` | `DzenPostUpdate` | dzen-service | Обновить пост |
| DELETE | `/dzen/post/{id}` | — | dzen-service | Удалить пост (status=deleted) |
| GET | `/dzen/rss/{user_id}` | — | dzen-service | Публичная RSS-лента (опционально ?token=) |

---

## Twitter (`/tw/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/tw/profile` | — | twitter-service | Получить профиль Twitter (404 → null) |
| POST | `/tw/profile` | `TwitterProfile` | twitter-service | Сохранить профиль |
| POST | `/tw/post` | `TwitterPost` | twitter-service | Опубликовать пост |

---

## Custom URL (`/curl/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/curl/settings` | — | custom-url-service | Получить настройки (404 → null) |
| POST | `/curl/settings` | `CustomURLSettings` | custom-url-service | Сохранить настройки |

---

## Create Post (`/cpost/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/cpost/profile` | — | create-post-service | Получить профиль (404 → null) |
| POST | `/cpost/profile` | `CreatePostProfile` | create-post-service | Сохранить профиль |
| POST | `/cpost/post` | `CreatePostRequest` | create-post-service | Создать пост |

---

## Test (`/test/*`)

| Метод | Путь | Тело | Сервис | Описание |
|-------|------|------|--------|----------|
| GET | `/test/products` | — | test-service | Список продуктов |
| GET | `/test/search/{orderId}` | — | test-service | Поиск заказа |
| POST | `/test/submit` | `SubmitRequest` | test-service | Отправить тест |

---

## Сводка по методам

- **GET:** 8 эндпоинтов  
- **POST:** 14 эндпоинтов  

**Всего:** 22 исходящих запроса (включая `/auth/refresh` в interceptor).

## Где вызываются

| Сервис | Файлы |
|--------|-------|
| api-client | `api-client.ts` (interceptor: refresh) |
| auth-service | `auth-context`, `profile`, `sign-in`, `sign-up`, `reset-password` |
| core-service | `stubs/statistics` |
| wordpress-service | `stubs/wordpress` |
| telegram-service | `telegram/telegram` |
| vkontakte-service | `stubs/vkontakte` |
| twitter-service | `stubs/twitter` |
| custom-url-service | `stubs/custom-url` |
| create-post-service | `create-post` |
| test-service | `test/test` |
