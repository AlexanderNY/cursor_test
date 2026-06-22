# Диагностика постинга в Telegram

Если сообщения попали в БД со статусом `collected`, но дальше не двигаются, ниже — схема пайплайна и как искать причину.

## Схема пайплайна (Telegram)

```
tg-bot (PostCollector)     →  tg_posts (status=collected)
                                    ↓
Collector (collect_posts)  →  posts (status=collected), tg_posts (status=processing)
                                    ↓
Processor                   →  posts (status=processing → ready)
                                    ↓
Collector (distribute)      →  tg_posts (status=ready) для постов с to_tg
                                    ↓
tg-bot (PostPublisher)      →  публикация в channel_to_post, tg_posts (status=published)
```

## Где могут застревать посты

| Где застряло | Таблица и статус | Что проверить |
|--------------|------------------|----------------|
| Не подхватываются сборщиком | `tg_posts.status = 'collected'` | Запущен ли **Collector**, цикл **collect** |
| Не попадают в центральную таблицу | `posts` пусто при наличии записей в `tg_posts` | Collector: логи, endpoint `/collect/run` |
| Не обрабатываются | `posts.status = 'collected'` | Запущен ли **Processor**, логи |
| Не возвращаются в TG для публикации | `posts.status = 'ready'`, в `tg_posts` нет `ready` | Запущен ли **Collector**, цикл **distribute**; у поста `to_tg = true` |
| Не публикуются в канал | `tg_posts.status = 'ready'` | Запущен ли **tg-bot**, в `tg_profiles` задан `channel_to_post` |

## SQL для диагностики

Выполняйте в БД по очереди.

### 1. Сводка по статусам в tg_posts

```sql
SELECT status, COUNT(*) AS cnt
FROM tg_posts
GROUP BY status
ORDER BY status;
```

Если много `collected` и мало/нет `processing` или `ready` — коллектор не забирает посты или дистрибьютор не ставит `ready`.

### 2. Сводка по статусам в posts

```sql
SELECT status, source_platform, COUNT(*) AS cnt
FROM posts
GROUP BY status, source_platform
ORDER BY status, source_platform;
```

Проверка: есть ли посты из `tg` в `collected` (не забирает процессор) или в `ready` (не забирает дистрибьютор).

### 3. Посты из TG: от tg_posts до posts

```sql
-- Посты в tg_posts со статусом collected (ждут сбора)
SELECT id, user_id, LEFT(post_text, 80) AS text_preview, status, created_at
FROM tg_posts
WHERE status = 'collected'
ORDER BY created_at DESC
LIMIT 20;

-- Есть ли соответствующие записи в posts (по source_platform, source_id)
SELECT p.id, p.source_platform, p.source_id, p.status, p.to_tg, p.created_at
FROM posts p
WHERE p.source_platform = 'tg'
ORDER BY p.created_at DESC
LIMIT 20;
```

### 4. Готовые к публикации в TG, но не в tg_posts

```sql
-- Посты в posts готовы к TG, но дистрибьютор должен был обновить tg_posts
SELECT id, source_platform, source_id, status, to_tg, to_wp, to_vk, created_at
FROM posts
WHERE status = 'ready' AND (to_tg = TRUE OR source_platform = 'tg')
ORDER BY created_at DESC
LIMIT 20;
```

### 5. Посты ready в tg_posts (должны публиковаться tg-bot)

```sql
SELECT p.id, p.user_id, pr.channel_to_post, p.status, LEFT(p.post_text, 60) AS text_preview
FROM tg_posts p
JOIN tg_profiles pr ON p.user_id = pr.user_id
WHERE p.status = 'ready'
  AND pr.channel_to_post IS NOT NULL AND pr.channel_to_post != ''
ORDER BY p.created_at ASC;
```

Если здесь строк нет — либо дистрибьютор не обновил `tg_posts` до `ready`, либо у профилей не задан `channel_to_post`.

## Проверка сервисов

1. **Collector** (сбор + распределение):
   - `GET http://<collector>/health` — сервис жив
   - В ответе или логах: время последнего цикла `collect` и `distribute`
   - Ручной запуск: `POST /collect/run`, `POST /distribute/run`

2. **Processor**:
   - `GET http://<processor>/health`
   - Ручной запуск цикла обработки (если есть endpoint)

3. **tg-bot**:
   - Убедиться, что в `tg_profiles` для нужного `user_id` заданы `channel_to_post` и при необходимости `publish_enabled`
   - Логи: раз в `PUBLISH_INTERVAL_SEC` вызывается `get_ready_posts` и публикация

## Если Collector не переносит посты из tg_posts в posts

1. **Collector запущен?**  
   Админка → Services Status: сервис `collector` должен быть в статусе **ok**. Если **error** (Connection refused / Timeout) — поднимите контейнер/процесс Collector и проверьте порт 8009.

2. **Один и тот же DATABASE_URL?**  
   У Collector, Core и tg-bot должен быть один и тот же `DATABASE_URL` (одна БД). Иначе tg-bot пишет в одну БД, Collector читает из другой.

3. **Таблицы созданы?**  
   Таблицы `posts` и `tg_posts` создаёт Core при первом запуске. Запустите Core хотя бы один раз до Collector. В логах Collector при старте при проблемах с таблицами будет сообщение уровня CRITICAL.

4. **Ручной запуск сбора и ошибки**  
   Админка → Диагностика постинга → **Запустить сбор (collect)**. Если цикл завершился с ошибкой, в ответе придут `errors` (например, «таблица posts не найдена», «column does not exist»). По ним можно понять, чего не хватает в БД или схеме.

5. **Логи Collector**  
   При ошибках сбора в логах Collector пишется полный traceback. Просмотр логов контейнера:  
   `docker compose logs -f collector` (или аналог для вашего окружения).

## Частые причины

- **Collector не запущен или падает** — посты остаются в `tg_posts.collected` и не попадают в `posts`.
- **Разные БД у tg-bot и Collector** — посты пишутся в одну БД, Collector поднят с другой.
- **Таблицы posts/tg_posts не созданы** — сначала должен отработать Core (создание схемы), затем Collector.
- **Processor не запущен** — посты в `posts` остаются в `collected`, не переходят в `ready`.
- **Distribute не обновляет tg_posts** — посты из TG (source_platform='tg') с `to_tg=true` должны получать в `tg_posts` статус `ready` (обновление строки по `source_id`). Если дистрибьютор не запущен или падает, в `tg_posts` не будет `ready`.
- **У поста to_tg = false** — в TG такой пост не публикуется; проверьте флаги в `posts` и откуда они выставляются (профиль/настройки).
- **В tg_profiles не задан channel_to_post** — PostPublisher не публикует посты для этого пользователя.

После исправления кода дистрибьютора (обновление той же платформы для TG) перезапустите Collector и при необходимости один раз вызовите `POST /distribute/run`.
