# S01E05 · FastAPI: первый роутер и Pydantic

## Пост

S01E05 · FastAPI · роутер и Pydantic

API начинается не с базы, а с контракта: путь, вход, выход, ошибка. FastAPI как раз заставляет это написать типами.

Три понятия:

- Роутер — набор путей (`GET /health`, `GET /tickets`). Позже разрежете по модулям, сейчас хватит одного файла.
- Pydantic-модель — JSON, который вы обещаете. Лишнее поле клиента не должно молча ломать сервер; недостающее — 422, не 500.
- Обработчик — функция. Пока можно вернуть список из памяти. База будет в E07.

Зачем это в живом сервисе. В CopyParse сервисы на FastAPI: шлюз и core говорят JSON-контрактами, а не «как получилось в print».

Граница. Не подключайте ORM, JWT и Docker в этом выпуске. Один процесс, `uvicorn`, две ручки. Swagger сам появится на `/docs` — это нормально, не отдельный микросервис.

Следующий выпуск: Insomnia — те же ручки без браузера и без React.

## Лаба

40 минут. В ветке репозитория заявок:

1. Минимальный FastAPI: `GET /health` → `{"status": "ok"}`.
2. Модель `Ticket` (id, title, status) и `GET /tickets` — верните 2–3 объекта из списка в коде.
3. Запуск: `uvicorn`. Откройте `/docs`.

В группу: скрин `/docs` и URL локально (localhost достаточно).

Проверка: OpenAPI в `/docs` совпадает с таблицей из вашего ТЗ хотя бы по `GET /tickets`. Если нет — поправьте либо код, либо ТЗ, не оба «на потом».

## Ссылки

- CopyParse (регистрация, учебный контур): https://www.copyparse.ru/sign-up?utm_source=tg&utm_campaign=s01e05
- First Steps — https://fastapi.tiangolo.com/tutorial/first-steps/
- Pydantic-модели в FastAPI — https://fastapi.tiangolo.com/tutorial/body/
- Автодокументация OpenAPI / Swagger UI — https://fastapi.tiangolo.com/tutorial/metadata/
- Русское зеркало туториала (сообщество) — https://fastapi.tiangolo.com/ru/tutorial/first-steps/

## Схема

```mermaid
flowchart LR
  Client[Клиент] --> Route["GET /tickets"]
  Route --> Model[Pydantic]
  Model --> Handler[Обработчик]
  Handler --> JSON[JSON]
```
