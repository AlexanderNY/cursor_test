import { CUSTOMERS_SCHEMA, SHOP_SCHEMA } from '@/game/sql/schemas'
import type { SqlCheckSpec } from '@/game/sql/sandbox-sqlite'
import type { SqlRow } from '@/game/sql/compare-rows'

export type SqlTask = {
  id: string
  title: string
  episode: string
  learnSlug: string
  level: 'junior' | 'middle'
  prompt: string
  examples: string[]
  /** Hidden seed applied before student SQL (fresh DB each run). */
  schemaSql: string
  starterSql: string
  /** Shown in the task brief (optional preview of seed). */
  schemaHint?: string
  check: SqlCheckSpec
}

export const SQL_TASKS: SqlTask[] = [
  {
    id: 'items-ddl-dml',
    title: 'CREATE + INSERT + UPDATE',
    episode: 'SQL01',
    learnSlug: 'sql-ddl-dml-dcl',
    level: 'junior',
    prompt:
      'Создайте таблицу items(id INTEGER PRIMARY KEY, name TEXT NOT NULL, qty INTEGER NOT NULL). Вставьте три строки (1/apple/10, 2/banana/5, 3/cherry/8). Обновите qty у banana до 7. Последним запросом сделайте SELECT id, name, qty FROM items ORDER BY id.',
    examples: [
      'DDL: CREATE TABLE items …',
      'DML: INSERT ×3, UPDATE qty, SELECT',
    ],
    schemaSql: '',
    schemaHint: 'Пустая БД — схему создаёте вы.',
    starterSql: `-- DDL + DML
-- CREATE TABLE items (...);
-- INSERT ...
-- UPDATE ...
SELECT 1 AS todo;
`,
    check: {
      mode: 'query',
      expectedRows: [
        { id: 1, name: 'apple', qty: 10 },
        { id: 2, name: 'banana', qty: 7 },
        { id: 3, name: 'cherry', qty: 8 },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'tables-keys-fk',
    title: 'PK и FK',
    episode: 'SQL02',
    learnSlug: 'sql-ddl-dml-dcl',
    level: 'junior',
    prompt:
      'Создайте users(id INTEGER PRIMARY KEY, name TEXT NOT NULL) и orders(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id), total REAL NOT NULL). Вставьте одного пользователя и один заказ. Проверка смотрит sqlite_master и наличие FK.',
    examples: [
      'CREATE TABLE users (... PRIMARY KEY ...)',
      'CREATE TABLE orders (... REFERENCES users(id) ...)',
    ],
    schemaSql: '',
    schemaHint: 'Пустая БД.',
    starterSql: `-- users + orders с PK/FK
`,
    check: {
      mode: 'verify',
      verifySql: `
SELECT
  CASE
    WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users') = 1
     AND (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='orders') = 1
     AND (SELECT sql FROM sqlite_master WHERE name='orders') LIKE '%REFERENCES%users%'
     AND (SELECT COUNT(*) FROM users) >= 1
     AND (SELECT COUNT(*) FROM orders) >= 1
    THEN 1 ELSE 0
  END AS ok,
  'users/orders с FK и данными' AS detail;
`,
    },
  },
  {
    id: 'delete-one-row',
    title: 'DELETE одной строки',
    episode: 'SQL03',
    learnSlug: 'sql-delete-truncate-drop',
    level: 'junior',
    prompt:
      'В таблице products уже есть 3 строки. Удалите продукт с id = 2. Таблица должна остаться. Последний SELECT: SELECT id, name FROM products ORDER BY id.',
    examples: ['DELETE FROM products WHERE id = 2', 'Не DROP TABLE'],
    schemaSql: `
CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);
INSERT INTO products (id, name) VALUES (1, 'pen'), (2, 'pencil'), (3, 'eraser');
`,
    schemaHint: 'products: (1,pen), (2,pencil), (3,eraser)',
    starterSql: `-- DELETE FROM products WHERE ...
SELECT id, name FROM products ORDER BY id;
`,
    check: {
      mode: 'query',
      expectedRows: [
        { id: 1, name: 'pen' },
        { id: 3, name: 'eraser' },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'inner-join-orders',
    title: 'INNER JOIN заказов',
    episode: 'SQL04',
    learnSlug: 'sql-delete-truncate-drop',
    level: 'junior',
    prompt:
      'Верните id заказа, имя пользователя и total для всех заказов через INNER JOIN users и orders. Столбцы: order_id, user_name, total. Порядок: ORDER BY order_id.',
    examples: [
      'INNER JOIN … ON orders.user_id = users.id',
      'Bob без заказов не попадёт в результат',
    ],
    schemaSql: SHOP_SCHEMA,
    schemaHint: 'users / orders / order_items (магазин)',
    starterSql: `-- SELECT o.id AS order_id, u.name AS user_name, o.total
-- FROM orders o
-- INNER JOIN users u ON ...
`,
    check: {
      mode: 'query',
      expectedRows: [
        { order_id: 10, user_name: 'Alice', total: 100 },
        { order_id: 11, user_name: 'Alice', total: 50 },
        { order_id: 12, user_name: 'Carol', total: 200 },
        { order_id: 13, user_name: 'Carol', total: 80 },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'left-join-no-orders',
    title: 'LEFT JOIN без заказов',
    episode: 'SQL04',
    learnSlug: 'sql-delete-truncate-drop',
    level: 'junior',
    prompt:
      'Через LEFT JOIN от users к orders найдите пользователей без заказов. Верните name. Ожидается одна строка: Bob.',
    examples: [
      'LEFT JOIN … WHERE orders.id IS NULL',
      'Не INNER — иначе Bob пропадёт',
    ],
    schemaSql: SHOP_SCHEMA,
    schemaHint: 'users / orders (у Bob 0 заказов)',
    starterSql: `-- SELECT u.name
-- FROM users u
-- LEFT JOIN orders o ON ...
-- WHERE o.id IS NULL;
`,
    check: {
      mode: 'query',
      expectedRows: [{ name: 'Bob' }] as SqlRow[],
      compare: { ordered: false },
    },
  },
  {
    id: 'is-null-filter',
    title: 'IS NULL',
    episode: 'SQL05',
    learnSlug: 'sql-types-null',
    level: 'junior',
    prompt:
      'Выберите name пользователей, у которых email IS NULL. Не используйте = NULL.',
    examples: ['WHERE email IS NULL', 'Bob'],
    schemaSql: SHOP_SCHEMA,
    schemaHint: 'users: у Bob email NULL',
    starterSql: `SELECT name FROM users WHERE /* TODO */;
`,
    check: {
      mode: 'query',
      expectedRows: [{ name: 'Bob' }] as SqlRow[],
      compare: { ordered: false },
    },
  },
  {
    id: 'create-index',
    title: 'CREATE INDEX',
    episode: 'SQL06',
    learnSlug: 'sql-types-null',
    level: 'junior',
    prompt:
      'На таблице orders уже есть данные. Создайте индекс idx_orders_user_id на столбце user_id. Проверка смотрит sqlite_master.',
    examples: ['CREATE INDEX idx_orders_user_id ON orders(user_id);'],
    schemaSql: `
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  total REAL NOT NULL
);
INSERT INTO orders (id, user_id, total) VALUES (1, 10, 1.0), (2, 20, 2.0);
`,
    schemaHint: 'orders(id, user_id, total) без индекса',
    starterSql: `-- CREATE INDEX ...
`,
    check: {
      mode: 'verify',
      verifySql: `
SELECT
  CASE
    WHEN EXISTS (
      SELECT 1 FROM sqlite_master
      WHERE type = 'index'
        AND name = 'idx_orders_user_id'
        AND tbl_name = 'orders'
    )
    THEN 1 ELSE 0
  END AS ok,
  'индекс idx_orders_user_id' AS detail;
`,
    },
  },
  {
    id: 'filter-operators',
    title: 'AND / OR / IS NULL',
    episode: 'SQL09',
    learnSlug: 'sql-triggers-operators',
    level: 'junior',
    prompt:
      'Выберите name из users, у кого email IS NULL ИЛИ name = \"Carol\". Столбец: name. Порядок не важен.',
    examples: [
      'WHERE email IS NULL OR name = \'Carol\'',
      'Bob и Carol',
    ],
    schemaSql: SHOP_SCHEMA,
    schemaHint: 'users',
    starterSql: `SELECT name FROM users
WHERE /* TODO: IS NULL / OR */;
`,
    check: {
      mode: 'query',
      expectedRows: [{ name: 'Bob' }, { name: 'Carol' }] as SqlRow[],
      compare: { ordered: false },
    },
  },
  {
    id: 'orders-above-avg',
    title: 'Подзапрос: выше среднего',
    episode: 'SQL10',
    learnSlug: 'sql-triggers-operators',
    level: 'middle',
    prompt:
      'Выберите id и total заказов, у которых total больше среднего total по всей таблице orders. Столбцы: id, total. Порядок: ORDER BY id.',
    examples: [
      'WHERE total > (SELECT AVG(total) FROM orders)',
      'Среднее = 107.5 → id 12 (200)',
    ],
    schemaSql: CUSTOMERS_SCHEMA,
    schemaHint: 'customers / orders',
    starterSql: `SELECT id, total
FROM orders
WHERE total > (SELECT AVG(total) FROM orders)
ORDER BY id;
`,
    check: {
      mode: 'query',
      expectedRows: [{ id: 12, total: 200 }] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'count-group-by',
    title: 'COUNT + GROUP BY',
    episode: 'SQL11',
    learnSlug: 'sql-agg-dates-count',
    level: 'junior',
    prompt:
      'Посчитайте число заказов по каждому user_id. Столбцы: user_id, order_count. Включите только пользователей с заказами. ORDER BY user_id.',
    examples: [
      'SELECT user_id, COUNT(*) AS order_count FROM orders GROUP BY user_id',
    ],
    schemaSql: SHOP_SCHEMA,
    schemaHint: 'orders',
    starterSql: `SELECT user_id, COUNT(*) AS order_count
FROM orders
GROUP BY user_id
ORDER BY user_id;
`,
    check: {
      mode: 'query',
      expectedRows: [
        { user_id: 1, order_count: 2 },
        { user_id: 3, order_count: 2 },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'paid-sum-by-customer',
    title: 'Сводный отчёт paid',
    episode: 'SQL12',
    learnSlug: 'sql-agg-dates-count',
    level: 'middle',
    prompt:
      'Для каждого клиента посчитайте сумму total только по заказам status = \'paid\'. Столбцы: customer_id, paid_sum. Только клиенты с хотя бы одним paid. ORDER BY customer_id.',
    examples: [
      'WHERE status = \'paid\' GROUP BY customer_id',
      'Alice: 150, Carol: 80',
    ],
    schemaSql: CUSTOMERS_SCHEMA,
    schemaHint: 'customers / orders',
    starterSql: `SELECT customer_id, SUM(total) AS paid_sum
FROM orders
WHERE status = 'paid'
GROUP BY customer_id
ORDER BY customer_id;
`,
    check: {
      mode: 'query',
      expectedRows: [
        { customer_id: 1, paid_sum: 150 },
        { customer_id: 3, paid_sum: 80 },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
  {
    id: 'last-order-window',
    title: 'ROW_NUMBER: последний заказ',
    episode: 'SQL13',
    learnSlug: 'sql-cte-window',
    level: 'middle',
    prompt:
      'Через оконную функцию ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) выберите последний заказ каждого клиента. Столбцы: customer_id, id, created_at. ORDER BY customer_id.',
    examples: [
      'WITH ranked AS (SELECT …, ROW_NUMBER() OVER (…) AS rn FROM orders)',
      'WHERE rn = 1',
    ],
    schemaSql: CUSTOMERS_SCHEMA,
    schemaHint: 'customers / orders',
    starterSql: `WITH ranked AS (
  SELECT
    customer_id,
    id,
    created_at,
    ROW_NUMBER() OVER (
      PARTITION BY customer_id
      ORDER BY created_at DESC
    ) AS rn
  FROM orders
)
SELECT customer_id, id, created_at
FROM ranked
WHERE rn = 1
ORDER BY customer_id;
`,
    check: {
      mode: 'query',
      expectedRows: [
        { customer_id: 1, id: 11, created_at: '2024-02-01' },
        { customer_id: 3, id: 13, created_at: '2024-03-01' },
      ] as SqlRow[],
      compare: { ordered: true },
    },
  },
]

const byId = new Map(SQL_TASKS.map((task) => [task.id, task]))

export function getSqlTask(id: string): SqlTask | undefined {
  return byId.get(id)
}

export function sqlTasksByEpisode(episode: string): SqlTask[] {
  const code = episode.toUpperCase()
  return SQL_TASKS.filter((task) => task.episode.toUpperCase() === code)
}

/** Related practice tasks when the episode has no dedicated graded tasks. */
const RELATED_BY_EPISODE: Record<string, string[]> = {
  SQL07: ['tables-keys-fk', 'inner-join-orders'],
  SQL08: ['items-ddl-dml', 'delete-one-row'],
  SQL14: ['create-index', 'inner-join-orders'],
  SQL15: ['orders-above-avg', 'last-order-window', 'is-null-filter'],
  SQL16: ['paid-sum-by-customer', 'last-order-window'],
}

export function sqlTasksForLearnEpisode(episode: string): {
  tasks: SqlTask[]
  related: boolean
} {
  const direct = sqlTasksByEpisode(episode)
  if (direct.length > 0) {
    return { tasks: direct, related: false }
  }
  const relatedIds = RELATED_BY_EPISODE[episode.toUpperCase()] || []
  const tasks = relatedIds
    .map((id) => getSqlTask(id))
    .filter((task): task is SqlTask => Boolean(task))
  return { tasks, related: tasks.length > 0 }
}
