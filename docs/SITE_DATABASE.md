# База данных 9to18.ru

Контур сайта **отделён** от CopyParse.

| База | Кто использует | Что хранит |
|------|----------------|------------|
| `db_bot` | CopyParse (auth, core SMM, боты…) + Learn-курсы | пользователи SaaS, посты соцсетей, `learn_posts`, … |
| `db_9to18` | core → роутер `/site/*` | `site_users`, `site_apps`, `site_posts`, `site_app_admins`, `site_settings`, `site_contacts` |

## Создание

```powershell
psql -U postgres -f deploy/sql/create_db_9to18.sql
psql -U postgres -d db_9to18 -f deploy/sql/init_db_9to18.sql
```

## Роли

| Роль | В БД | Права |
|------|------|--------|
| **Пользователь** | `site_users.site_role = user` | Чтение всех опубликованных страниц и статей сервисов |
| **Админ сервиса** | строка в `site_app_admins` | Своя плашка, страница `/app/{slug}` и блог сервиса |
| **Супер-админ** | `site_users.site_role = site_admin` | Состав/порядок плашек, статьи всех сервисов, спотлайт, назначение админов |

API супер-админа: `GET/PUT /site/admin/apps`, `PUT /site/admin/apps/reorder`, `POST/DELETE /site/apps`, CRUD постов `/site/apps/{slug}/posts…`.

Выдать супер-админа:

```sql
UPDATE site_users SET site_role = 'site_admin' WHERE username = '…';
```

Админа сервиса назначает супер-админ в UI `/admin` или через `POST /site/admin/assign`.

## Env

Контур 9to18 — отдельный файл:

```powershell
cp .env.9to18.example .env.9to18
# отредактируйте SITE_DATABASE_URL
```

`docker-compose` подключает `.env.9to18` к сервису **core** (`env_file`).  
Если файла нет — core при пустом `SITE_DATABASE_URL` сам подставит `dbname=db_9to18` в DSN из `DATABASE_URL`.
