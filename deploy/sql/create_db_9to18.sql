-- Create dedicated PostgreSQL database for 9to18.ru (run as superuser on the Postgres host).
-- Example:
--   psql -U postgres -f deploy/sql/create_db_9to18.sql
--   psql -U postgres -d db_9to18 -f deploy/sql/init_db_9to18.sql

SELECT 'CREATE DATABASE db_9to18 OWNER CURRENT_USER ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'db_9to18')\gexec
