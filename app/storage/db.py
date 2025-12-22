import sqlite3
from typing import Optional, List, Tuple
import os
from pathlib import Path

DB_PATH = os.getenv("DB_PATH", "data/bot.db")
db_file = Path(DB_PATH)
if db_file.parent and str(db_file.parent) not in (".", ""):
    db_file.parent.mkdir(parents=True, exist_ok=True)


def connect() -> sqlite3.Connection:
    """
    Create a SQLite connection with foreign keys enabled.
    """
    con = sqlite3.connect(DB_PATH)
    con.execute("PRAGMA foreign_keys = ON;")
    return con


def init_db() -> None:
    """
    Create tables if they do not exist and apply simple migrations for older DB versions.
    """
    with connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            )
        """)

        con.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                qty REAL NOT NULL,
                limit_qty REAL DEFAULT NULL,
                below_limit INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
                UNIQUE(category_id, name)
            )
        """)

        # Notification subscribers
        con.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id INTEGER PRIMARY KEY
            )
        """)

        # --- TASKS table ---
        con.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                text TEXT NOT NULL,
                is_done INTEGER NOT NULL DEFAULT 0,
                created TEXT NOT NULL DEFAULT (datetime('now')),
                task_cat_id INTEGER NOT NULL CHECK(task_cat_id IN (1, 2, 3))
            )
        """)

        # Simple migrations for older DBs
        cols = [row[1] for row in con.execute("PRAGMA table_info(products)").fetchall()]
        if "limit_qty" not in cols:
            con.execute("ALTER TABLE products ADD COLUMN limit_qty REAL DEFAULT NULL")
        if "below_limit" not in cols:
            con.execute("ALTER TABLE products ADD COLUMN below_limit INTEGER NOT NULL DEFAULT 0")

        con.commit()


# ===== Subscribers =====

def add_subscriber(chat_id: int) -> None:
    with connect() as con:
        con.execute("INSERT OR IGNORE INTO subscribers(chat_id) VALUES (?)", (int(chat_id),))
        con.commit()


def remove_subscriber(chat_id: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM subscribers WHERE chat_id=?", (int(chat_id),))
        con.commit()


def is_subscriber(chat_id: int) -> bool:
    with connect() as con:
        cur = con.execute("SELECT 1 FROM subscribers WHERE chat_id=? LIMIT 1", (int(chat_id),))
        return cur.fetchone() is not None


def list_subscribers() -> List[int]:
    with connect() as con:
        cur = con.execute("SELECT chat_id FROM subscribers")
        return [int(row[0]) for row in cur.fetchall()]


# ===== Categories =====

def add_category(name: str) -> None:
    with connect() as con:
        con.execute("INSERT INTO categories(name) VALUES (?)", (name.strip(),))
        con.commit()


def list_categories() -> List[Tuple[int, str]]:
    with connect() as con:
        cur = con.execute("SELECT id, name FROM categories ORDER BY id ASC")
        return cur.fetchall()


def get_category(cat_id: int) -> Optional[Tuple[int, str]]:
    with connect() as con:
        cur = con.execute("SELECT id, name FROM categories WHERE id=?", (int(cat_id),))
        return cur.fetchone()


def update_category(cat_id: int, new_name: str) -> None:
    with connect() as con:
        con.execute("UPDATE categories SET name=? WHERE id=?", (new_name.strip(), int(cat_id)))
        con.commit()


def delete_category(cat_id: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM categories WHERE id=?", (int(cat_id),))
        con.commit()


# ===== Products =====

def add_product(category_id: int, name: str, qty: float, limit_qty: float | None = None) -> None:
    clean_name = name.strip()
    qty_f = float(qty)
    limit_f = None if limit_qty is None else float(limit_qty)

    # Determine initial below_limit state
    below_limit = 1 if (limit_f is not None and qty_f <= limit_f) else 0

    with connect() as con:
        con.execute(
            """INSERT INTO products (category_id, name, qty, limit_qty,below_limit)
            VALUES (?, ?, ?, ?, ?)
            """,
            (int(category_id), clean_name, qty_f, limit_f, below_limit),
        )
        con.commit()


def list_products_by_category(category_id: int) -> List[Tuple[int, str, float, float | None]]:
    with connect() as con:
        cur = con.execute(
            "SELECT id, name, qty, limit_qty FROM products WHERE category_id=? ORDER BY id ASC",
            (int(category_id),),
        )
        return cur.fetchall()


def get_product(product_id: int) -> Optional[Tuple[int, int, str, float, float | None, int]]:
    with connect() as con:
        cur = con.execute(
            "SELECT id, category_id, name, qty, limit_qty, below_limit FROM products WHERE id=?",
            (int(product_id),),
        )
        return cur.fetchone()


def update_product_name(product_id: int, new_name: str) -> None:
    with connect() as con:
        con.execute("UPDATE products SET name=? WHERE id=?", (new_name.strip(), int(product_id)))
        con.commit()


def update_product_qty(product_id: int, new_qty: float) -> None:
    with connect() as con:
        con.execute("UPDATE products SET qty=? WHERE id=?", (float(new_qty), int(product_id)))
        con.commit()


def update_product_limit(product_id: int, new_limit_qty: float | None) -> None:
    with connect() as con:
        con.execute(
            "UPDATE products SET limit_qty=? WHERE id=?",
            (None if new_limit_qty is None else float(new_limit_qty), int(product_id)),
        )
        con.commit()


def set_below_limit(product_id: int, below: int) -> None:
    with connect() as con:
        con.execute(
            "UPDATE products SET below_limit=? WHERE id=?",
            (1 if below else 0, int(product_id)),
        )
        con.commit()


def delete_product(product_id: int) -> None:
    with connect() as con:
        con.execute("DELETE FROM products WHERE id=?", (int(product_id),))
        con.commit()


# ===== Reorder list =====

def list_reorder_items() -> List[Tuple[int, str, int, str, float, float]]:
    """
    Return items that should be reordered:
    (cat_id, cat_name, prod_id, prod_name, qty, limit_qty)
    """
    with connect() as con:
        cur = con.execute("""
            SELECT c.id, c.name, p.id, p.name, p.qty, p.limit_qty
            FROM products p
            JOIN categories c ON c.id = p.category_id
            WHERE p.limit_qty IS NOT NULL
              AND p.qty <= p.limit_qty
            ORDER BY c.name ASC, p.name ASC
        """)
        return cur.fetchall()


# ===== Tasks =====

def add_task(user_id: int, text: str, task_cat_id: int) -> int:
    """
    Create a task. Returns new task id.
    """
    text = text.strip()
    if not text:
        raise ValueError("Task text is empty")

    with connect() as con:
        cur = con.execute(
            "INSERT INTO tasks(user_id, text, task_cat_id) VALUES (?, ?, ?)",
            (int(user_id), text, int(task_cat_id)),
        )
        con.commit()
        return int(cur.lastrowid)


def list_all_tasks_by_category(task_cat_id: int, include_done: bool = False) -> List[Tuple[int, str]]:
    """
    List tasks for a category. If include_done=False -> only not done.
    """
    with connect() as con:
        if include_done:
            cur = con.execute(
                """
                SELECT id, text, task_cat_id
                FROM tasks
                WHERE task_cat_id=?
                ORDER BY is_done ASC, id DESC
                """,
                (int(task_cat_id),),
            )
        else:
            cur = con.execute(
                """
                SELECT id, text, task_cat_id
                FROM tasks
                WHERE task_cat_id=? AND is_done=0
                ORDER BY id DESC
                """,
                (int(task_cat_id),),
            )
        return [(task_id, text, task_cat_id) for (task_id, text, task_cat_id) in cur.fetchall()]


def get_task(task_id: int) -> Optional[tuple[int, str, int]]:
    """
    Get one task by id.
    """
    with connect() as con:
        cur = con.execute(
            """
            SELECT id, text, task_cat_id
            FROM tasks
            WHERE id=?
            """,
            (int(task_id),),
        )
        return cur.fetchone()


def update_task(task_id: int, new_text: str) -> None:
    """
    Update task text.
    """
    new_text = new_text.strip()
    if not new_text:
        raise ValueError("Task text is empty")

    with connect() as con:
        con.execute("UPDATE tasks SET text=? WHERE id=?", (new_text, int(task_id)))
        con.commit()


def set_task_done(task_id: int, is_done: bool) -> None:
    """
    Set done status explicitly.
    """
    with connect() as con:
        con.execute(
            "UPDATE tasks SET is_done=? WHERE id=?",
            (1 if is_done else 0, int(task_id)),
        )
        con.commit()
