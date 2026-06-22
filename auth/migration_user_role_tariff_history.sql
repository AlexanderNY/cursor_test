-- Миграция: таблица истории изменений роли и тарифа пользователей
-- Выполните этот скрипт, если auth БД уже развёрнута без этой таблицы

CREATE TABLE IF NOT EXISTS user_role_tariff_history (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INTEGER NULL REFERENCES users(id) ON DELETE SET NULL,
    role_old VARCHAR(20) NULL,
    role_new VARCHAR(20) NULL,
    tariff_old VARCHAR(50) NULL,
    tariff_new VARCHAR(50) NULL
);

CREATE INDEX IF NOT EXISTS idx_user_role_tariff_history_user_id ON user_role_tariff_history(user_id);
