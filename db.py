"""数据库初始化与连接管理"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = (
    os.getenv("DATABASE_PRIVATE_URL") or
    os.getenv("DATABASE_URL") or
    ""
)


def get_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, sslmode="require")


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    file_id     TEXT PRIMARY KEY,
                    filename    TEXT NOT NULL,
                    total       INT  NOT NULL,
                    risk_counts JSONB,
                    file_hash   TEXT,
                    analyzed_at TIMESTAMPTZ DEFAULT NOW()
                );
            """)
            cur.execute("ALTER TABLE batches ADD COLUMN IF NOT EXISTS file_hash TEXT;")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS notes (
                    id              SERIAL PRIMARY KEY,
                    file_id         TEXT NOT NULL REFERENCES batches(file_id) ON DELETE CASCADE,
                    idx             INT  NOT NULL,
                    title           TEXT,
                    content         TEXT,
                    topics          TEXT,
                    note_url        TEXT,
                    likes           INT DEFAULT 0,
                    favs            INT DEFAULT 0,
                    comments        INT DEFAULT 0,
                    shares          INT DEFAULT 0,
                    influence_score INT DEFAULT 0,
                    influence_level TEXT,
                    risk_level      TEXT,
                    risk_reason     TEXT,
                    report_category TEXT,
                    report_text     TEXT,
                    report_status   TEXT DEFAULT '待投诉',
                    note_key        TEXT,
                    UNIQUE(file_id, idx)
                );
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS note_cache (
                    note_key        TEXT PRIMARY KEY,
                    risk_level      TEXT,
                    risk_reason     TEXT,
                    report_category TEXT,
                    report_text     TEXT,
                    updated_at      TIMESTAMPTZ DEFAULT NOW()
                );
            """)
        conn.commit()
