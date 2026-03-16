import sqlite3
import os
from datetime import datetime, timedelta

DB_PATH = os.path.join(os.path.dirname(__file__), "clipboard.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    return conn


def create_table():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            type TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_item(content, type_="text"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO clipboard_items (content, type) VALUES (?, ?)", (content, type_))
    conn.commit()
    conn.close()


def get_recent_items(limit=20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id, content, type, timestamp FROM clipboard_items ORDER BY timestamp DESC LIMIT ?", (limit,))
    items = c.fetchall()
    conn.close()
    return items
