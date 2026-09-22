# Канонический стек 9to18 переехал в [`nine-to-eighteen/`](../../nine-to-eighteen/).

Поднимайте оттуда:

```powershell
cd ../../nine-to-eighteen
cp .env.example .env   # DATABASE_URL → db_9to18, JWT_SECRET_KEY
docker compose up -d --build
```

Этот каталог оставлен как указатель; исходники UI и API — в `nine-to-eighteen/`.
