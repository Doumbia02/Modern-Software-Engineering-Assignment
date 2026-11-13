
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Database file location
DB_PATH = Path(__file__).resolve().parent / "expenses.db"


# Establish a database connection
@contextmanager
def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


# Create the database table
def initialize_database():
    with get_connection() as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK(length(trim(name)) > 0),
                amount REAL NOT NULL CHECK(amount > 0),
                category TEXT NOT NULL CHECK(length(trim(category)) > 0),
                expense_date TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


# CREATE: Add a new expense
def create_expense(name, amount, category, expense_date):
    with get_connection() as connection:
        cursor = connection.execute("""
            INSERT INTO expenses (name, amount, category, expense_date)
            VALUES (?, ?, ?, ?)
        """, (name, amount, category, expense_date))

        expense_id = cursor.lastrowid

        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row)


# READ: Retrieve all expenses
def get_all_expenses():
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM expenses ORDER BY expense_date DESC, id DESC"
        ).fetchall()

        return [dict(row) for row in rows]


# READ: Retrieve one expense by ID
def get_expense_by_id(expense_id):
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row) if row else None


# UPDATE: Modify an existing expense
def update_expense(expense_id, updates):
    allowed_fields = {
        "name", "amount", "category", "expense_date"
    }

    if not updates or not set(updates).issubset(allowed_fields):
        return None

    fields = ", ".join(f"{field} = ?" for field in updates)
    values = list(updates.values())
    values.append(expense_id)

    with get_connection() as connection:
        cursor = connection.execute(
            f"""
            UPDATE expenses
            SET {fields}, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            values
        )

        if cursor.rowcount == 0:
            return None

        row = connection.execute(
            "SELECT * FROM expenses WHERE id = ?",
            (expense_id,)
        ).fetchone()

        return dict(row)


# DELETE: Remove an expense
def delete_expense(expense_id):
    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM expenses WHERE id = ?",
            (expense_id,)
        )

        return cursor.rowcount > 0
