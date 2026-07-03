"""DDL для игрового Telegram-бота (PostgreSQL). Передаётся в database.init_db."""

GAME_TABLE_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS game_bots (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        token TEXT NOT NULL UNIQUE,
        username TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_players (
        id SERIAL PRIMARY KEY,
        telegram_user_id BIGINT NOT NULL,
        bot_id INT REFERENCES game_bots(id) ON DELETE CASCADE,
        username TEXT,
        first_name TEXT,
        is_admin BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_modes (
        id SERIAL PRIMARY KEY,
        code TEXT NOT NULL,
        title TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        questions_per_game INT NOT NULL DEFAULT 10
            CHECK (questions_per_game > 0 AND questions_per_game <= 300),
        bot_id INT REFERENCES game_bots(id) ON DELETE RESTRICT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_questions (
        id SERIAL PRIMARY KEY,
        mode_id INT NOT NULL REFERENCES game_modes(id) ON DELETE CASCADE,
        prompt_text TEXT NOT NULL,
        image_file_id TEXT,
        image_url TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_question_options (
        id SERIAL PRIMARY KEY,
        question_id INT NOT NULL REFERENCES game_questions(id) ON DELETE CASCADE,
        option_index SMALLINT NOT NULL CHECK (option_index >= 1 AND option_index <= 6),
        option_text TEXT NOT NULL,
        is_correct BOOLEAN NOT NULL DEFAULT FALSE,
        UNIQUE (question_id, option_index)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_sessions (
        id SERIAL PRIMARY KEY,
        player_id INT NOT NULL REFERENCES game_players(id) ON DELETE CASCADE,
        mode_id INT NOT NULL REFERENCES game_modes(id) ON DELETE CASCADE,
        status TEXT NOT NULL DEFAULT 'in_progress'
            CHECK (status IN ('in_progress', 'completed', 'aborted')),
        score INT NOT NULL DEFAULT 0,
        correct_count INT NOT NULL DEFAULT 0,
        total_questions INT NOT NULL,
        current_step INT NOT NULL DEFAULT 0,
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMPTZ,
        duration_sec INT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_session_questions (
        id SERIAL PRIMARY KEY,
        session_id INT NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
        step_index INT NOT NULL CHECK (step_index >= 0),
        question_id INT NOT NULL REFERENCES game_questions(id) ON DELETE CASCADE,
        UNIQUE (session_id, step_index)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_answers (
        id SERIAL PRIMARY KEY,
        session_id INT NOT NULL REFERENCES game_sessions(id) ON DELETE CASCADE,
        question_id INT NOT NULL REFERENCES game_questions(id) ON DELETE CASCADE,
        selected_option_id INT REFERENCES game_question_options(id) ON DELETE SET NULL,
        is_correct BOOLEAN NOT NULL,
        answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (session_id, question_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_game_questions_mode ON game_questions(mode_id) WHERE is_active = TRUE",
    "CREATE INDEX IF NOT EXISTS idx_game_sessions_player_status ON game_sessions(player_id, status)",
    "CREATE INDEX IF NOT EXISTS idx_game_sessions_finished ON game_sessions(status, finished_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS game_media_assets (
        id SERIAL PRIMARY KEY,
        filename TEXT NOT NULL UNIQUE,
        s3_key TEXT NOT NULL UNIQUE,
        original_filename TEXT,
        title TEXT NOT NULL DEFAULT '',
        description TEXT,
        content_type TEXT,
        size_bytes BIGINT NOT NULL DEFAULT 0,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    ALTER TABLE game_modes
        ADD COLUMN IF NOT EXISTS bot_id INT REFERENCES game_bots(id) ON DELETE RESTRICT
    """,
    """
    ALTER TABLE game_players
        ADD COLUMN IF NOT EXISTS bot_id INT REFERENCES game_bots(id) ON DELETE CASCADE
    """,
    "ALTER TABLE game_modes DROP CONSTRAINT IF EXISTS game_modes_code_key",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_game_modes_bot_code
        ON game_modes(bot_id, code)
    """,
    "ALTER TABLE game_players DROP CONSTRAINT IF EXISTS game_players_telegram_user_id_key",
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_game_players_bot_user
        ON game_players(bot_id, telegram_user_id)
    """,
    """
    INSERT INTO game_modes (code, title, is_active, questions_per_game)
    SELECT 'demo', 'Демо-режим', TRUE, 3
    WHERE NOT EXISTS (SELECT 1 FROM game_modes WHERE code = 'demo')
    """,
    """
    ALTER TABLE game_modes
        DROP CONSTRAINT IF EXISTS game_modes_questions_per_game_check
    """,
    """
    ALTER TABLE game_modes
        ADD CONSTRAINT game_modes_questions_per_game_check
        CHECK (questions_per_game > 0 AND questions_per_game <= 300)
    """,
    """
    ALTER TABLE game_modes
        ADD COLUMN IF NOT EXISTS mode_type TEXT NOT NULL DEFAULT 'quiz'
    """,
    """
    ALTER TABLE game_modes
        DROP CONSTRAINT IF EXISTS game_modes_mode_type_check
    """,
    """
    ALTER TABLE game_modes
        ADD CONSTRAINT game_modes_mode_type_check
        CHECK (mode_type IN ('quiz', 'menu'))
    """,
    """
    CREATE TABLE IF NOT EXISTS game_menu_nodes (
        id SERIAL PRIMARY KEY,
        mode_id INT NOT NULL REFERENCES game_modes(id) ON DELETE CASCADE,
        parent_id INT REFERENCES game_menu_nodes(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        body_text TEXT,
        image_url TEXT,
        image_file_id TEXT,
        sort_order INT NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS idx_game_menu_nodes_mode_parent ON game_menu_nodes(mode_id, parent_id)",
    """
    ALTER TABLE game_menu_nodes
        ADD COLUMN IF NOT EXISTS price NUMERIC(12, 2) NOT NULL DEFAULT 0
    """,
    """
    CREATE TABLE IF NOT EXISTS game_menu_carts (
        id SERIAL PRIMARY KEY,
        bot_id INT NOT NULL REFERENCES game_bots(id) ON DELETE CASCADE,
        telegram_user_id BIGINT NOT NULL,
        mode_id INT NOT NULL REFERENCES game_modes(id) ON DELETE CASCADE,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        UNIQUE (bot_id, telegram_user_id, mode_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_menu_cart_items (
        id SERIAL PRIMARY KEY,
        cart_id INT NOT NULL REFERENCES game_menu_carts(id) ON DELETE CASCADE,
        node_id INT NOT NULL REFERENCES game_menu_nodes(id) ON DELETE CASCADE,
        quantity INT NOT NULL DEFAULT 1 CHECK (quantity > 0),
        UNIQUE (cart_id, node_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_menu_orders (
        id SERIAL PRIMARY KEY,
        order_number TEXT NOT NULL UNIQUE,
        bot_id INT NOT NULL REFERENCES game_bots(id) ON DELETE RESTRICT,
        mode_id INT NOT NULL REFERENCES game_modes(id) ON DELETE RESTRICT,
        telegram_user_id BIGINT NOT NULL,
        username TEXT,
        first_name TEXT,
        status TEXT NOT NULL DEFAULT 'placed'
            CHECK (status IN ('placed', 'cancelled')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    ALTER TABLE game_menu_orders
        ADD COLUMN IF NOT EXISTS total_amount NUMERIC(12, 2) NOT NULL DEFAULT 0
    """,
    """
    CREATE TABLE IF NOT EXISTS game_menu_order_items (
        id SERIAL PRIMARY KEY,
        order_id INT NOT NULL REFERENCES game_menu_orders(id) ON DELETE CASCADE,
        node_id INT REFERENCES game_menu_nodes(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        quantity INT NOT NULL CHECK (quantity > 0),
        unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0
    )
    """,
    """
    ALTER TABLE game_menu_order_items
        ADD COLUMN IF NOT EXISTS unit_price NUMERIC(12, 2) NOT NULL DEFAULT 0
    """,
    "CREATE INDEX IF NOT EXISTS idx_game_menu_orders_mode ON game_menu_orders(mode_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_game_menu_orders_bot ON game_menu_orders(bot_id, created_at DESC)",
]
