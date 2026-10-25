/** Shared shop schema for join / subquery / window tasks (SQLite). */
export const SHOP_SCHEMA = `
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  total REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  sku TEXT NOT NULL,
  qty INTEGER NOT NULL
);

INSERT INTO users (id, name, email) VALUES
  (1, 'Alice', 'alice@example.com'),
  (2, 'Bob', NULL),
  (3, 'Carol', 'carol@example.com');

INSERT INTO orders (id, user_id, total, status, created_at) VALUES
  (10, 1, 100.0, 'paid', '2024-01-01'),
  (11, 1, 50.0, 'paid', '2024-02-01'),
  (12, 3, 200.0, 'pending', '2024-01-15'),
  (13, 3, 80.0, 'paid', '2024-03-01');

INSERT INTO order_items (id, order_id, sku, qty) VALUES
  (1, 10, 'A', 2),
  (2, 10, 'B', 1),
  (3, 11, 'A', 1),
  (4, 12, 'C', 4),
  (5, 13, 'B', 2);
`

/** Customers/orders alias used in subquery labs (same data, names from lectures). */
export const CUSTOMERS_SCHEMA = `
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  total REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);

INSERT INTO customers (id, name) VALUES
  (1, 'Alice'),
  (2, 'Bob'),
  (3, 'Carol');

INSERT INTO orders (id, customer_id, total, status, created_at) VALUES
  (10, 1, 100.0, 'paid', '2024-01-01'),
  (11, 1, 50.0, 'paid', '2024-02-01'),
  (12, 3, 200.0, 'pending', '2024-01-15'),
  (13, 3, 80.0, 'paid', '2024-03-01');
`

/**
 * Demo shop for the free sandbox and Learn snippets.
 * `orders` has both user_id and customer_id so lecture queries of either shape run.
 */
export const SANDBOX_DEMO_SCHEMA = `
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  middle_name TEXT
);
CREATE TABLE customers (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT,
  city TEXT
);
CREATE TABLE orders (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  customer_id INTEGER NOT NULL REFERENCES customers(id),
  total REAL NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE order_items (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES orders(id),
  sku TEXT NOT NULL,
  qty INTEGER NOT NULL
);
CREATE TABLE sizes (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE colors (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);

INSERT INTO users (id, name, email, middle_name) VALUES
  (1, 'Alice', 'alice@example.com', 'Ann'),
  (2, 'Bob', NULL, NULL),
  (3, 'Carol', 'carol@example.com', '');

INSERT INTO customers (id, name, email, city) VALUES
  (1, 'Alice', 'alice@example.com', 'Moscow'),
  (2, 'Bob', NULL, NULL),
  (3, 'Carol', 'carol@example.com', 'Kazan');

INSERT INTO orders (id, user_id, customer_id, total, status, created_at) VALUES
  (10, 1, 1, 100.0, 'paid', '2024-01-01'),
  (11, 1, 1, 50.0, 'paid', '2024-02-01'),
  (12, 3, 3, 200.0, 'pending', '2024-01-15'),
  (13, 3, 3, 80.0, 'paid', '2024-03-01');

INSERT INTO order_items (id, order_id, sku, qty) VALUES
  (1, 10, 'A', 2),
  (2, 10, 'B', 1),
  (3, 11, 'A', 1),
  (4, 12, 'C', 4),
  (5, 13, 'B', 2);

INSERT INTO sizes (id, name) VALUES (1, 'S'), (2, 'M');
INSERT INTO colors (id, name) VALUES (1, 'red'), (2, 'blue');
`

const DEMO_TABLES = ['users', 'customers', 'orders', 'order_items', 'sizes', 'colors']

function stripSqlComments(sql: string): string {
  return sql.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/--[^\n]*/g, ' ')
}

function sqlNames(sql: string, pattern: RegExp): Set<string> {
  const names = new Set<string>()
  for (const match of sql.matchAll(pattern)) {
    names.add(match[1].toLowerCase())
  }
  return names
}

/**
 * Seed the demo shop when a free-form script reads those tables
 * and does not create them itself.
 */
export function schemaForFreeSql(studentSql: string): string {
  const sql = stripSqlComments(studentSql)
  const created = sqlNames(
    sql,
    /\bCREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?["'`]?([A-Za-z_][A-Za-z0-9_]*)/gi,
  )
  const referenced = sqlNames(
    sql,
    /\b(?:FROM|JOIN|UPDATE|INTO|TABLE)\s+["'`]?([A-Za-z_][A-Za-z0-9_]*)/gi,
  )
  const needed = DEMO_TABLES.filter((name) => referenced.has(name))
  if (needed.length === 0 || needed.some((name) => created.has(name))) {
    return ''
  }
  return SANDBOX_DEMO_SCHEMA
}
