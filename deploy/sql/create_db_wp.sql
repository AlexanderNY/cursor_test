-- Create dedicated PostgreSQL database for local WordPress (wp-site).
-- Run as superuser on the Postgres host:
--   psql -U postgres -f deploy/sql/create_db_wp.sql

SELECT 'CREATE DATABASE db_wp OWNER CURRENT_USER ENCODING ''UTF8'''
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'db_wp')\gexec
