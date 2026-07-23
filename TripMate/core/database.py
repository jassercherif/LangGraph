import psycopg
from psycopg.rows import dict_row

from core.config import get_database_url


def get_db_connection():
    """Open a synchronous psycopg connection (caller must close it)."""
    return psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
        sslmode="disable",
    )


def setup_auth_tables() -> None:
    """Create users and user_sessions tables if they do not exist."""
    with get_db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id            SERIAL PRIMARY KEY,
                    username      VARCHAR(50)  UNIQUE NOT NULL,
                    email         VARCHAR(100) UNIQUE NOT NULL,
                    hashed_password VARCHAR(255) NOT NULL,
                    created_at    TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id         VARCHAR(64) PRIMARY KEY,
                    user_id    INTEGER REFERENCES users(id) ON DELETE CASCADE,
                    title      VARCHAR(255) DEFAULT 'New Trip',
                    last_answer TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            cur.execute("""
                ALTER TABLE user_sessions
                ADD COLUMN IF NOT EXISTS last_answer TEXT DEFAULT ''
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_sessions_user_updated
                ON user_sessions(user_id, updated_at DESC)
            """)
        conn.commit()
