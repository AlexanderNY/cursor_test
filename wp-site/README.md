# Локальный WordPress (`wp-site`)

Отдельный Compose-стек: **WordPress 6.6 + PHP pgsql + [PG4WP](https://github.com/PostgreSQL-For-Wordpress/postgresql-for-wordpress)**.  
База — внешний PostgreSQL **`db_wp`** (как `db_bot` / `db_9to18`), не контейнер MySQL.

Ядро WordPress умеет только MySQL; PG4WP подменяет `mysqli` drop-in’ом `wp-content/db.php`. Ставить его нужно **до** мастера установки.

## Запуск

Нужны Docker и PostgreSQL 16 на хосте (тот же, что CopyParse).

```powershell
cd K:\Project\cursor_test
# один раз: создать пустую БД
& "K:\Pro\PostgreSQL\bin\psql.exe" -U postgres -h 127.0.0.1 -f deploy\sql\create_db_wp.sql

cd wp-site
copy .env.example .env
# заполните WORDPRESS_DB_PASSWORD (как в корневом DATABASE_URL)

docker compose up -d --build
```

Сайт: [http://127.0.0.1:8088](http://127.0.0.1:8088)  
Мастер установки: логин/пароль админа WP **не** совпадают с паролем Postgres.

Остановка: `docker compose stop`. `wp-content` в named volume. Полный сброс файлов темы/плагинов:

```powershell
docker compose down -v
```

Таблицы в `db_wp` при этом остаются, пока их не удалите в Postgres (`DROP DATABASE db_wp`).

## REST API и CopyParse `wp-bot`

1. Админка → **Пользователи → Профиль** → **Пароли приложений**.
2. В профиле WordPress CopyParse: URL `http://127.0.0.1:8088`, логин админа, application password.

`WP_ENVIRONMENT_TYPE=local` включает Application Passwords по HTTP.

```powershell
curl.exe -sf http://127.0.0.1:8088/wp-json/wp/v2
```

Из контейнера `wp-bot`: `http://host.docker.internal:8088`.

## Порты

| Сервис    | Хост             |
|-----------|------------------|
| WordPress | `127.0.0.1:8088` |
| Postgres  | хост, обычно `5432` (`db_wp`) |

Не занимайте `:80` — его использует `deploy/ui-edge`.
