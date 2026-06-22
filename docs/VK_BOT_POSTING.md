# VK Bot: токены, публикация и OAuth

Документ фиксирует матрицу использования токенов для [vk-bot/services/post_publisher.py](../vk-bot/services/post_publisher.py) и соглашения по полям `vk_profiles`.

## Поля профиля (без новых колонок)

| Поле | Назначение |
|------|------------|
| `access_token` | Как правило **токен сообщества** (community): `wall.post` на стену группы, `wall.get` при сборе. |
| `user_access_token` | **Пользовательский** OAuth-токен: `users.get`, `wall.post` на **личную** стену (положительный `owner_id`), загрузка фото/доков на стену **группы** (`photos.getWallUploadServer` и цепочка upload). |

Один пользовательский токен с scope `wall`, `photos`, `groups`, `offline` закрывает сценарии, где VK требует именно пользователя (см. ошибку API [27] при загрузке на стену группы с групповым ключом).

## Матрица: куда постим × текст или медиа

| Цель | Только текст (`wall.post` без attachments) | Текст + фото/доки |
|------|---------------------------------------------|-------------------|
| **Стена группы** (`owner_id < 0`) | `access_token` (сообщество), при необходимости `from_group=1` | Загрузка: **`user_access_token`**; публикация: **`access_token`** для `wall.post` с готовой строкой вложений (реализация: отдельные клиенты upload vs wall). |
| **Личная стена** (`owner_id > 0`) | **`user_access_token`** (или пользовательский `access_token`), `from_group=0` | Тот же пользовательский токен для upload и для `wall.post`. |

Версия API VK рекомендуется единая (например **5.199**), см. [версии API](https://dev.vk.com/ru/reference/versions).

## Выбор потока авторизации для `user_access_token`

| Подход | Статус в проекте |
|--------|------------------|
| **Классический OAuth** (`https://oauth.vk.com/authorize` → обмен `code` на `https://oauth.vk.com/access_token`) | **Используется** в Core: `GET /vk/oauth/url`, `GET /vk/oauth/callback`, сохранение в `user_access_token`. |
| **VK ID без SDK (PKCE)** (`https://id.vk.ru/authorize`, обмен на `https://id.vk.ru/oauth2/auth`) | **Не реализован**; подходит при необходимости refresh-токенов и требований VK ID к кнопке/дизайну. Документация: [авторизация без SDK](https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/start-integration/auth-without-sdk/auth-without-sdk-web), [дизайн кнопки](https://id.vk.com/about/business/go/docs/ru/vkid/latest/vk-id/connection/guidelines/design-rules). |
| Ручной ввод токена | Допустимо через API профиля; менее безопасно. |

## Наблюдаемость

В логах публикации ищите строки вида `wall.post` / `upload` с указанием `owner_id` и типа токена (`community` / `user`), чтобы отлаживать ошибки [27] и права доступа.
