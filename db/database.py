import re
import sqlite3
import os
from datetime import datetime

# Get the absolute path for the database file
from app_config import config, get_writable_path

# Use the same AppData folder as the config
DB_PATH = get_writable_path("clipboard.db")


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


def add_item(content, manual_tag=None):
    if not content.strip(): return

    # --- Enhanced Tag Detection ---
    if manual_tag:
        tag = manual_tag
    else:
        tag = "Text"
        content_strip = content.strip()

        # 1. Email Check (Regex)
        if re.match(r"[^@]+@[^@]+\.[^@]+", content_strip):
            tag = "Email"
        # 2. URL Check
        elif content_strip.startswith(("http://", "https://", "www.")) or content_strip.endswith(
                (".com", ".org", ".io", ".net")):
            tag = "URL"
        # 3. Code Check
        elif any(char in content for char in ["{", "}", "import ", "def ", "const ", "static ", "public class", "<html>"]):
            tag = "Code"

    conn = get_connection()
    c = conn.cursor()
    # Optional: Avoid saving the exact same content twice in a row
    c.execute("SELECT content FROM clipboard_items ORDER BY timestamp DESC LIMIT 1")
    last = c.fetchone()
    if last and last[0] == content:
        conn.close()
        return

    c.execute("INSERT INTO clipboard_items (content, tag) VALUES (?, ?)", (content, tag))
    conn.commit()
    conn.close()


def toggle_favorite(item_id, status):
    """Pin or unpin an item"""
    conn = get_connection()
    c = conn.cursor()
    # Force boolean to integer for SQLite compatibility
    val = 1 if status else 0
    c.execute("UPDATE clipboard_items SET is_favorite = ? WHERE id = ?", (val, item_id))
    conn.commit()
    conn.close()


def delete_item(item_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM clipboard_items WHERE id=?", (item_id,))
    conn.commit()
    conn.close()

def update_item(item_id, new_content):
    conn = get_connection()
    c = conn.cursor()
    c.execute("UPDATE clipboard_items SET content = ? WHERE id = ?", (new_content, item_id))
    conn.commit()
    conn.close()


def get_item_count():
    """Returns the total number of saved clipboard items."""
    with get_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM clipboard_items")
        return cursor.fetchone()[0]


def delete_oldest_items(n):
    """Deletes the 'n' oldest items from the database."""
    with get_connection() as conn:
        # We find the IDs of the oldest N items and delete them
        conn.execute("""
            DELETE FROM clipboard_items 
            WHERE id IN (
                SELECT id FROM clipboard_items 
                ORDER BY timestamp ASC 
                LIMIT ?
            )
        """, (n,))
        conn.commit()


def get_recent_items(limit=50, search_query=None, filter_type="ALL", mode="main"):
    """
    Unified fetcher for the premium dashboard.
    Handles searching, category filtering, and sorting modes.
    """
    conn = get_connection()
    c = conn.cursor()

    # 1. Sorting Logic
    # Favorites first if in dashboard mode, otherwise strictly by time
    order_logic = "is_favorite DESC, timestamp DESC" if mode == "dashboard" else "timestamp DESC"

    # 2. Build Query Dynamically
    # Using 'WHERE 1=1' allows us to append 'AND' clauses easily
    query = f"SELECT id, content, tag, is_favorite, timestamp FROM clipboard_items WHERE 1=1"
    params = []

    # Filter by Search
    if search_query and search_query.strip():
        query += " AND content LIKE ?"
        params.append(f"%{search_query}%")

    # Filter by Category (Matching the UI Chip IDs)
    if filter_type == "FAVORITES":
        query += " AND is_favorite = 1"
    elif filter_type == "TEXT":
        query += " AND tag = 'Text'"
    elif filter_type == "CODE":
        query += " AND tag = 'Code'"
    elif filter_type == "URL":
        query += " AND tag = 'URL'"
    elif filter_type == "EMAIL":
        query += " AND tag = 'Email'"
    elif filter_type == "IMAGE":
        query += " AND tag = 'Image'"

    # Finalize Query
    query += f" ORDER BY {order_logic} LIMIT ?"
    params.append(limit)

    c.execute(query, params)
    items = c.fetchall()
    conn.close()
    return items


def enforce_database_limits():
    """
    1. Removes data older than 30 days.
    2. Enforces the 'History Limit' from config.settings.
    """
    # Parse History Limit from config (e.g., "100 Records" -> 100)
    limit_str = config.settings.get("history_limit", "100 Records")
    if "Unlimited" in limit_str:
        max_rows = 5000  # Safety cap to prevent memory issues
    else:
        try:
            max_rows = int(limit_str.split()[0])
        except (ValueError, IndexError):
            max_rows = 100

    with get_connection() as conn:
        # A. Delete items older than 30 days
        conn.execute("DELETE FROM clipboard_items WHERE timestamp < datetime('now', '-30 days')")

        # B. Delete items exceeding the numerical limit (keeping Favorites)
        # We use a subquery to find IDs that are NOT in the 'Top N' most recent
        conn.execute("""
            DELETE FROM clipboard_items 
            WHERE id NOT IN (
                SELECT id FROM clipboard_items 
                ORDER BY timestamp DESC 
                LIMIT ?
            )
        """, (max_rows,))
        conn.commit()


def get_time_ago(timestamp_str):
    try:
        # SQLite format: 2023-10-27 10:00:00
        past = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        now = datetime.utcnow()  # Match SQLite's UTC default
        diff = now - past

        seconds = int(diff.total_seconds())  # total_seconds() is more reliable
        if seconds < 0: return "Just now"  # Handle slight sync drifts
        if seconds < 60: return f"{seconds}s ago"
        if seconds < 3600: return f"{seconds // 60}m ago"
        if seconds < 86400: return f"{seconds // 3600}h ago"
        return f"{diff.days}d ago"
    except Exception as e:
        print(f"Time error: {e}")
        return "Recent"


def clear_all_data():
    """Irreversibly wipes the entire database."""
    with get_connection() as conn:
        conn.execute("DELETE FROM clipboard_items")
        conn.commit()


def get_total_count():
    """Returns the total number of items in the clipboard_items table."""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            # Use the correct table name: clipboard_items
            cursor.execute("SELECT COUNT(*) FROM clipboard_items")
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        print(f"Database Count Error: {e}")
        return 0

def get_category_counts():
    """Returns a dict of counts for each category and favorites."""
    counts = {"ALL": 0, "FAVORITES": 0, "TEXT": 0, "CODE": 0, "URL": 0, "EMAIL": 0, "IMAGE": 0}
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM clipboard_items")
            counts["ALL"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM clipboard_items WHERE is_favorite = 1")
            counts["FAVORITES"] = cursor.fetchone()[0]
            
            cursor.execute("SELECT tag, COUNT(*) FROM clipboard_items GROUP BY tag")
            for row in cursor.fetchall():
                tag = str(row[0]).upper()
                if tag in counts:
                    counts[tag] = row[1]
    except Exception as e:
        print(f"Database Category Count Error: {e}")
    return counts