# Жизненный цикл постов в таблице `posts`

Таблица **posts** — центральное хранилище постов из всех платформ (Telegram, WordPress, URL, VK и т.д.). Записи проходят несколько статусов от появления до распределения в целевые таблицы для публикации.

Публикация во **VK** (токены сообщества vs пользователя, текст и вложения): см. [VK_BOT_POSTING.md](VK_BOT_POSTING.md).

---

## Схема статусов

```
  [платформенные таблицы]     posts                    [платформенные таблицы]
  tg_posts, url_posts, ...    (центральная)            tg_posts, wp_posts, vk_posts
  status = 'collected' или 'created'  ──►   collected   ──►  processing   ──►   ready / review
       │                            │              │                    │
       │  Collector (collect)       │  Processor   │  Collector         │
       │  INSERT + source_id        │  обработка   │  (distribute)      │
       └────────────────────────────┘              └──────────►  distributed
                                                                     │
                                                                     ▼
                                                            INSERT/UPDATE в *_posts
                                                            со статусом 'ready'
```

---

## Этапы жизненного цикла

### 1. Появление записи в платформенных таблицах и перенос в **posts**: **collected**

- **Кто создаёт строки в `*_posts`:** боты и сервисы Core (сборщики, url-bot, vk-bot, ручные cpost/Twitter и т.д.) — вставка со статусом **`collected`** (сбор с внешних источников) или **`created`** (например, ручное создание поста VK в Core), пока collector не заберёт запись в `posts`.
- **Кто переносит в `posts`:** только сервис **Collector** (цикл collect). Без запущенного collector новые строки остаются только в платформенной таблице.
- **Реестр источников** задаётся в `collector/config.py` (`SOURCE_TABLES`), в том числе: `tg_posts`, `wp_posts`, `url_posts`, `vk_posts`, `instagram_posts`, `dzen_posts`, `cpost_posts`, `tw_posts`.
- **Действия Collector (collect):**
  - `SELECT ... FROM <таблица> WHERE status IN ('collected', 'created') FOR UPDATE SKIP LOCKED`
  - `INSERT INTO posts (... source_platform, source_id)` со статусом **collected**
  - `UPDATE <таблица> SET status = 'processing'`
- **Смысл:** пост попал в общую очередь на обработку и привязан к источнику (`source_platform`, `source_id`).

Разовый перенос старых записей, которые раньше создавались сразу в `posts`, описан в [migrate_legacy_cpost_tw_from_posts.sql](migrations/migrate_legacy_cpost_tw_from_posts.sql).

---

### 2. Взятие в обработку: **processing**

- **Кто ставит:** сервис **Processor** в начале цикла обработки.
- **Действия:**
  - `SELECT ... FROM posts WHERE status = 'collected' FOR UPDATE SKIP LOCKED`
  - `UPDATE posts SET status = 'processing'` по выбранным id.
- **Смысл:** пост зарезервирован процессором, чтобы другие воркеры его не дублировали. Статус **processing** временный — до конца обработки одной пачкой.

---

### 3. После обработки: **ready** или **review**

- **Кто ставит:** сервис **Processor** после применения правил (AI, эмодзи, HTML, платформенные тексты).
- **Логика:**
  - если в настройках профиля включено «на модерацию» → **review**
  - иначе → **ready**
- **Действия Processor:**
  - обновляет `post_text`, `images`, `platform_texts`
  - `UPDATE posts SET status = 'ready' | 'review'`
- **Смысл:** пост готов к распределению по целевым платформам (для **ready**) или ждёт ручной проверки (для **review**).

---

### 4. Распределение: **distributed**

- **Кто ставит:** сервис **Collector** (цикл distribute).
- **Действия:**
  - `SELECT ... FROM posts WHERE status = 'ready'`
  - для каждого поста по флагам `to_tg`, `to_wp`, `to_vk`:
    - если целевая платформа **та же**, что источник (например, пост из TG и to_tg):  
      `UPDATE tg_posts SET status = 'ready', post_text = ..., images = ... WHERE id = source_id`
    - если целевая платформа **другая**:  
      `INSERT INTO tg_posts (wp_posts, vk_posts, ...) (... status = 'ready')`
  - `UPDATE posts SET status = 'distributed'`
- **Смысл:** пост перенесён в платформенные таблицы со статусом **ready**; дальнейшая публикация идёт уже из `*_posts` (tg-bot, wp-bot, vk-bot и т.д.). В **posts** для него цикл завершён.

---

## Сводка переходов статусов в `posts`

| Статус        | Кто меняет   | Следующий шаг |
|---------------|--------------|----------------|
| **collected** | Collector    | Processor забирает в **processing** |
| **processing**| Processor    | После обработки → **ready** или **review** |
| **ready**     | Processor    | Collector (distribute) переносит в *_posts и ставит **distributed** |
| **review**    | Processor    | Ожидает ручного перевода в ready (вне текущего пайплайна) или доработки логики |
| **distributed**| Collector   | Финальный для центральной таблицы; публикация из tg_posts/wp_posts/... |

---

## Важные поля в `posts`

- **source_platform**, **source_id** — откуда пост попал (например `tg`, id в `tg_posts`). Нужны для дедупликации (ON CONFLICT) и для обновления той же строки при distribute (TG → TG).
- **to_tg**, **to_wp**, **to_vk** — в какие платформы распределять пост при статусе **ready**.
- **platform_texts** (JSONB) — тексты, подготовленные под каждую платформу (лимиты длины и т.д.); при distribute подставляются в целевые таблицы.

---

## Где пост «живёт» после `posts`

- Публикация в Telegram: **tg_posts** (status ready → published) — tg-bot.
- Публикация в WordPress / VK и т.д.: **wp_posts**, **vk_posts** (status ready → published) — соответствующие боты.

Статусы **published** и подсчёт «опубликовано» ведутся в платформенных таблицах, а не в **posts**; в **posts** после **distributed** запись больше не меняется этим пайплайном.
