import sqlite3
import os
from datetime import datetime

# Get the absolute path for the database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clipboard.db")


def get_connection():
    return sqlite3.connect(DB_PATH)


def create_table():
    conn = get_connection()
    c = conn.cursor()
    # Updated schema:
    # - tag: Stores 'Code', 'URL', or 'Text'
    # - is_favorite: 1 for pinned/favorite, 0 for normal
    c.execute("""
        CREATE TABLE IF NOT EXISTS clipboard_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tag TEXT DEFAULT 'Text',
            is_favorite INTEGER DEFAULT 0,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_item(content):
    # Determine tag automatically before saving
    tag = "Text"
    if content.strip().startswith(("http://", "https://", "www.")):
        tag = "URL"
    elif any(char in content for char in ["{", "}", "import ", "const ", "def ", "npm "]):
        tag = "Code"

    conn = get_connection()
    c = conn.cursor()
    # We use INSERT OR IGNORE or a check if you want to avoid duplicate consecutive entries
    c.execute("INSERT INTO clipboard_items (content, tag) VALUES (?, ?)", (content, tag))
    conn.commit()
    conn.close()


def toggle_favorite(item_id, status):
    """Pin or unpin an item"""
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE clipboard_items SET is_favorite = ? WHERE id = ?", (status, item_id))
    conn.commit()
    conn.close()


def get_recent_items(limit=20):
    conn = get_connection()
    c = conn.cursor()
    # Sort by favorites first, then by most recent time
    c.execute("""
        SELECT id, content, tag, is_favorite, timestamp 
        FROM clipboard_items 
        ORDER BY is_favorite DESC, timestamp DESC 
        LIMIT ?
    """, (limit,))
    items = c.fetchall()
    conn.close()
    return items


def get_time_ago(timestamp_str):
    """Helper to convert DB timestamp to '5 mins ago' style strings"""
    try:
        # SQLite DEFAULT CURRENT_TIMESTAMP uses YYYY-MM-DD HH:MM:SS
        past = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.utcnow()
        diff = now - past

        if diff.days > 0:
            return f"{diff.days}d ago"
        seconds = diff.seconds
        if seconds < 60:
            return "Just now"
        if seconds < 3600:
            return f"{seconds // 60}m ago"
        return f"{seconds // 3600}h ago"
    except:
        return "Recent"
