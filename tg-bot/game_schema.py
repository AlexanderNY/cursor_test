"""DDL для игрового Telegram-бота (PostgreSQL). Передаётся в database.init_db."""

GAME_TABLE_DDL: list[str] = [
    """
    CREATE TABLE IF NOT EXISTS game_players (
        id SERIAL PRIMARY KEY,
        telegram_user_id BIGINT NOT NULL UNIQUE,
        username TEXT,
        first_name TEXT,
        is_admin BOOLEAN NOT NULL DEFAULT FALSE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS game_modes (
        id SERIAL PRIMARY KEY,
        code TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        questions_per_game INT NOT NULL DEFAULT 10
            CHECK (questions_per_game > 0 AND questions_per_game <= 100),
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
    INSERT INTO game_modes (code, title, is_active, questions_per_game)
    VALUES ('demo', 'Демо-режим', TRUE, 3)
    ON CONFLICT (code) DO NOTHING
    """,
]
