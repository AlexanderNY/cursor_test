# База данных 9to18.ru

Контур сайта **независим** от CopyParse: сервис [`nine-to-eighteen/`](../nine-to-eighteen/README.md)
(`site-api` + UI) и БД `db_9to18`.

| База | Кто использует | Что хранит |
|------|----------------|------------|
| `db_bot` | CopyParse (auth, core SMM, боты…) | пользователи SaaS, посты соцсетей; старые `learn_posts` — архив |
| `db_9to18` | `site-api` + `resume-api` (`nine-to-eighteen/`) | `site_users`, apps/posts, `learn_posts`, прогресс Learn, study, `site_resumes` / профили |
| `db_wp` | локальный WordPress (`wp-site/`, PG4WP) | таблицы `wp_*` |

## Создание

```powershell
psql -U postgres -f deploy/sql/create_db_9to18.sql
# DDL таблиц применяется site-api при старте; либо:
# psql -U postgres -d db_9to18 -f deploy/sql/init_db_9to18.sql
```

## Env

```powershell
cd nine-to-eighteen
cp .env.example .env
# DATABASE_URL=dbname=db_9to18 ...
# JWT_SECRET_KEY=…  (свой секрет, не обязан совпадать с CopyParse)
```

## Learn

Контент и CMS — в `db_9to18` / `site-api`. Админка: супер-админ сайта (`site_role = site_admin`).

Миграция из старого `db_bot.learn_posts`: [`nine-to-eighteen/sql/migrate_learn_from_db_bot.sql`](../nine-to-eighteen/sql/migrate_learn_from_db_bot.sql).

## Прогресс ученика

`site_learn_progress` через `GET/PUT /site/learn/progress` и site JWT (`aud=9to18`).
