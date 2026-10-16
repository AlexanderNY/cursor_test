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
