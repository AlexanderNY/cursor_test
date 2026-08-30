# VK Bot: токены, публикация и OAuth

Документ фиксирует матрицу использования токенов для [vk-bot/services/post_publisher.py](../vk-bot/services/post_publisher.py) и соглашения по полям `vk_profiles`.

Публикация в сообщество — **`wall.post`** на стену группы (не `messages.send`). [Callback API](https://dev.vk.ru/ru/api/callback/getting-started) принимает confirmation/`ok` на `POST /vk/callback`; автоответы `message_new` пока не реализованы.

**Секреты VK хранятся только в БД (`vk_profiles`)**, не в `.env`.

## Четыре блока авторизации (UI)

| Блок | Поля БД | Verify API | Назначение |
|------|---------|------------|------------|
| 1. Токен сообщества | `group_to_post`, `access_token` | `POST /vk/auth/verify/community` | wall.post / API от имени группы ([community-messages](https://dev.vk.ru/ru/api/community-messages/getting-started)) |
| 2. Callback API | `vk_callback_confirmation`, `vk_callback_secret` | `POST /vk/auth/verify/callback` | Подтверждение сервера; URL = `{vk_public_gateway_url}/vk/callback` |
| 3. Приложение | `vk_app_id`, `vk_app_secret`, `vk_app_service_key`, URL | `POST /vk/auth/verify/app` | Ключи приложения ([keys](https://dev.vk.ru/ru/mini-apps/settings/development/keys)) |
| 4. OAuth | `user_access_token`, `vk_user_id` (+ community через `flow=group`) | `POST /vk/auth/verify/oauth` | User OAuth для фото; group OAuth для `access_token` |

SQL-патч: [deploy/sql/patch_vk_auth_blocks.sql](../deploy/sql/patch_vk_auth_blocks.sql).

## Поля профиля

| Поле | Назначение |
|------|------------|
| `access_token` | Токен сообщества: `wall.post` (`from_group=1`) в свою группу |
| `user_access_token` | User OAuth: чтение чужих стен (`wall.get`), личная стена, upload фото на группу |
| `vk_app_*` | Клиент OAuth (только БД) |
| `vk_callback_*` | Confirmation + secret для Callback (lookup по `group_id` ≈ `group_to_post`) |

## Каналы (Channels): проверка доступа

| Роль канала | Токен | Что проверяется |
|-------------|-------|-----------------|
| `own` | community (`group_to_post`) + опционально user | Публикация в свою группу; сбор — если есть user OAuth |
| `source` / `competitor` | **user OAuth** | `groups.getById` / чтение чужой стены (short name ок) |

## OAuth scopes (Core)

| Flow | Endpoint | Scopes | Результат |
|------|----------|--------|-----------|
| Пользователь | `GET /vk/oauth/url?flow=user` | `wall,photos,offline` | `user_access_token` |
| Сообщество | `GET /vk/oauth/url?flow=group` | `wall,photos,docs,manage` + `group_ids` | `access_token` |

Redirect URI: `{VK_PUBLIC_GATEWAY_URL}/vk/oauth/callback`  
API version: **5.199**.

## Матрица публикации

| Цель | Текст | Текст + медиа |
|------|-------|---------------|
| Стена группы | community `access_token`, `from_group=1` | upload: `user_access_token`; post: community |
| Личная стена | `user_access_token` | тот же user token |

## Callback

`POST /vk/callback` (публичный): по `group_id` ищет профиль → сверяет `vk_callback_secret` → на `confirmation` отдаёт `vk_callback_confirmation` из БД, иначе `ok`.
