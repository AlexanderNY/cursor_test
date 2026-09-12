# Жизненный цикл постов

Очередь контента — таблица **`posts`**. Очередь публикации — **`post_targets`** (`UNIQUE (post_id, platform)`). ETL-копирование между `posts` и `*_posts` **удалено**.

```
боты / core / RSS  →  posts (collected)
                         ↓ processor
                   posts (ready | review)
                         ↓ ensure_targets
              post_targets (ready)
                         ↓ боты (claim publishing)
              published | failed | skipped
```

SMM «опубликовать сейчас» сразу создаёт хаб + `post_targets.status=ready` и будит бота (`/internal/publish-now`).

Публикация во **VK**: [VK_BOT_POSTING.md](VK_BOT_POSTING.md).

---

## Статусы `posts`

| Статус | Кто ставит | Дальше |
|--------|------------|--------|
| **collected** / **created** | Сборщик или Core | Processor claim → **processing** |
| **processing** | Processor | **ready** или **review** |
| **ready** | Processor (есть цели) | Боты читают `post_targets` |
| **review** | Processor (модерация или нет целей) | Ручной перевод / повторная обработка |
| **deleted** | Core / UI | Конец |

`distributed` больше не используется пайплайном.

---

## Статусы `post_targets`

`pending` → `ready` → `publishing` → `published` | `failed` | `skipped` | `deleted`

Claim: `FOR UPDATE SKIP LOCKED` по `(platform, status, publish_at)`.

NOTIFY: `copyparse_process` на `posts.status=collected`, `copyparse_publish` на `post_targets.status=ready`.

Существующие БД: один раз выполнить `deploy/sql/migrate_unify_drop_platform_posts.sql` (бэкап `*_posts` → `posts`/`post_targets`, затем `DROP`). Greenfield (`init_schema.sql`) эти таблицы не создаёт.

---

## Collector

Сервис collector **больше не копирует** строки. Он:

- читает внешний RSS Дзена в `posts`;
- ставит NOTIFY-триггеры;
- отдаёт `/metrics` по `posts` / `post_targets`;
- `POST /collect/run` будит processor;
- `POST /distribute/run` — no-op (публикация из `post_targets`).

---

## Поля

- **posts:** `source_platform`, `source_native_id`, `extras` (inbound), текст и медиа.
- **post_targets:** `platform` ∈ `PUBLISH_PLATFORMS` (без url/cpost), `status`, `publish_at`, `target_channels` / `target_groups`, `result`.
- Флаги публикации приходят из UI как `to_*` и пишутся в `post_targets`, не в колонки `posts`.

Адаптация текста: `shared/post_adapt.py` (`NETWORK_TEXT_LIMITS`).
