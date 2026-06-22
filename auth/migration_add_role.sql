-- Миграция: добавление поля role в таблицу users
-- Выполните этот скрипт, если таблица users уже существует

-- Добавление поля role, если его еще нет
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'role'
    ) THEN
        ALTER TABLE users 
        ADD COLUMN role VARCHAR(20) DEFAULT 'guest' NOT NULL 
        CHECK (role IN ('guest', 'user', 'admin'));
        
        -- Обновление существующих пользователей (если они есть)
        UPDATE users SET role = 'guest' WHERE role IS NULL;
    END IF;
END $$;
