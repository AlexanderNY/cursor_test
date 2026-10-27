import type { TopicDeck } from '@/data/learning-map/decks/types'

export const deckData: TopicDeck = {
  branchTitle: 'Данные',
  cards: [
    {
      id: 'pool:data:pg-basics',
      front: `PostgreSQL: зачем на собесе?`,
      back: `Транзакции, SQL, индексы, EXPLAIN — база для backend/аналитика. Версия и расширения — бонус.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:sql-join-agg',
      front: `JOIN и агрегаты?`,
      back: `Связь таблиц и GROUP BY/агрегатные функции. Частый практический блок собеса.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:normalization-map',
      front: `Нормализация на карте данных?`,
      back: `Моделируем сущности без избыточности; денорм — осознанно под нагрузку.`,
      learnSlug: 'sql-normalization',
    },
    {
      id: 'pool:data:sql-nosql',
      front: `SQL vs NoSQL?`,
      back: `Реляционная модель/транзакции vs гибкость/шардирование документных/KV. Выбор от запросов и consistency.`,
      learnSlug: 'sd-one-service',
    },
    {
      id: 'pool:data:redis-cache',
      front: `Redis как кэш на карте?`,
      back: `Ускорение чтения, TTL, риск stampede. Source of truth обычно Postgres.`,
      learnSlug: 'rd-kv-model',
    },
    {
      id: 'pool:data:acid-data',
      front: `ACID в Postgres?`,
      back: `Гарантии tx; изоляция и аномалии — частый follow-up. Связка с реализацией MVCC.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:index-data',
      front: `Когда добавить индекс?`,
      back: `Когда фильтр/join селективны и профилирование показывает seq scan. Пишите стоимость записи.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:fk',
      front: `Зачем внешние ключи?`,
      back: `Целостность на уровне БД. Иногда отключают ради скорости — цена на приложение.`,
      learnSlug: 'sql-normalization',
    },
    {
      id: 'pool:data:jsonb',
      front: `JSONB в Postgres?`,
      back: `Гибкие атрибуты + индексы GIN. Не замена нормальной модели для жёстких связей.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:migration',
      front: `Миграции схемы?`,
      back: `Версионируемые DDL, обратная совместимость expand/contract. Без них хаос на стендах.`,
      learnSlug: 'sd-one-service',
    },
    {
      id: 'pool:data:backup',
      front: `Бэкапы и RPO?`,
      back: `RPO — сколько данных готовы потерять. Питы/WAL архивы — часть эксплуатации данных.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:read-replica',
      front: `Read replica?`,
      back: `Масштаб чтения, лаг репликации. Не для строго свежих критичных чтений без учёта лага.`,
      learnSlug: 'sd-one-service',
    },
    {
      id: 'pool:data:cache-invalid',
      front: `Инвалидация кэша?`,
      back: `TTL и/или явный delete при записи. Стейл vs нагрузка на БД — явный trade-off.`,
      learnSlug: 'rd-kv-model',
    },
    {
      id: 'pool:data:etl',
      front: `ETL/ELT кратко?`,
      back: `Извлечение и преобразование данных в хранилище. ELT переносит трансформацию ближе к DWH.`,
      learnSlug: 'sd-one-service',
    },
    {
      id: 'pool:data:cardinality',
      front: `Кардинальность связи?`,
      back: `1:1, 1:N, M:N — влияет на ключи и join-таблицы. Ошибка модели дорого чинится.`,
      learnSlug: 'sql-normalization',
    },
    {
      id: 'pool:data:explain-data',
      front: `Когда смотреть EXPLAIN?`,
      back: `Медленный запрос, неожиданный seq scan, рост данных. ANALYZE — с осторожностью на проде.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:pooling',
      front: `Пул соединений к БД?`,
      back: `Ограничивает число соединений приложения/сервисов. PgBouncer часто снаружи app pool.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:txid',
      front: `Почему короткие транзакции?`,
      back: `Меньше блокировок и bloat. Не держите tx на время HTTP-вызова наружу.`,
      learnSlug: 's01e07-postgres',
    },
    {
      id: 'pool:data:nosql-keys',
      front: `Ключи в KV/документных?`,
      back: `Паттерн доступа определяет ключ. Скан «как SQL» обычно дорог — проектируйте под запросы.`,
      learnSlug: 'sd-one-service',
    },
    {
      id: 'pool:data:data-quality',
      front: `Качество данных?`,
      back: `Ограничения, валидация на входе, мониторинг аномалий. Мусор на входе = мусор в аналитике.`,
      learnSlug: 'sql-normalization',
    },
  ],
}
