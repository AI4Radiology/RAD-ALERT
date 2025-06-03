import os
from contextlib import contextmanager
from psycopg2 import connect, sql
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from . import settings
import os

load_dotenv()  





TABLE_REPORTS = sql.Identifier(settings.DB_SCHEMA, 'reports')
TABLE_CONFIG  = sql.Identifier(settings.DB_SCHEMA, 'config')


@contextmanager
def get_conn():
    conn = connect(
        dbname=settings.PG_DBNAME,
        user=settings.PG_USER,
        password=settings.PG_PASSWORD,
        host=settings.PG_HOST,
        port=settings.PG_PORT,
        sslmode="require",
        cursor_factory=RealDictCursor
    )
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            
            cur.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                  id       SERIAL PRIMARY KEY,
                  text     TEXT    NOT NULL,
                  verdict  TEXT    NOT NULL,
                  prob     REAL,
                  ts       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """).format(TABLE_REPORTS))
            
            cur.execute(sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                  key   TEXT PRIMARY KEY,
                  value TEXT
                );
            """).format(TABLE_CONFIG))
            
            cur.execute(
                sql.SQL("INSERT INTO {} (key,value) VALUES ('email', %s) ON CONFLICT DO NOTHING")
                   .format(TABLE_CONFIG),
                (settings.DEFAULT_EMAIL,)
            )
            cur.execute(
                sql.SQL("INSERT INTO {} (key,value) VALUES ('whatsapp', %s) ON CONFLICT DO NOTHING")
                   .format(TABLE_CONFIG),
                (settings.WHATSAPP_TO,)
            )
            conn.commit()
    except Exception as e:
        print("[db] Warning: init_db failed:", e)


init_db()


def insert_report(text: str, verdict: str, prob: float = None) -> dict:

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            sql.SQL("INSERT INTO {} (text, verdict, prob) VALUES (%s, %s, %s) RETURNING *")
               .format(TABLE_REPORTS),
            (text, verdict, prob)
        )
        report = cur.fetchone()
        conn.commit()
        return report

def get_reports(limit: int = 100) -> list:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            sql.SQL("SELECT * FROM {} ORDER BY ts DESC LIMIT %s")
               .format(TABLE_REPORTS),
            (limit,)
        )
        return cur.fetchall()


def get_config(key: str) -> str:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            sql.SQL("SELECT value FROM {} WHERE key = %s")
               .format(TABLE_CONFIG),
            (key,)
        )
        row = cur.fetchone()
        return row['value'] if row else None

def set_config(key: str, value: str) -> None:
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(
            sql.SQL("""
              INSERT INTO {} (key, value) VALUES (%s, %s)
              ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
            """).format(TABLE_CONFIG),
            (key, value)
        )
        conn.commit()
