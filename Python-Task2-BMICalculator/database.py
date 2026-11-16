"""
SQLite storage for BMI records (multi-user history).
"""

import os
import sqlite3
from datetime import datetime

DEFAULT_DB_PATH = os.environ.get(
    "BMI_DB_PATH",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmi_records.db"),
)


class DatabaseError(Exception):
    """Raised when reading from or writing to the database fails."""


class BMIDatabase:
    def __init__(self, path=DEFAULT_DB_PATH):
        self.path = path
        try:
            self.conn = sqlite3.connect(self.path)
            self.conn.execute("PRAGMA foreign_keys = ON")
            self._create_tables()
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not open the database: {err}") from err

    def _create_tables(self):
        with self.conn:
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS users (
                       id   INTEGER PRIMARY KEY AUTOINCREMENT,
                       name TEXT NOT NULL UNIQUE COLLATE NOCASE
                   )"""
            )
            self.conn.execute(
                """CREATE TABLE IF NOT EXISTS records (
                       id         INTEGER PRIMARY KEY AUTOINCREMENT,
                       user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                       weight_kg  REAL NOT NULL,
                       height_m   REAL NOT NULL,
                       bmi        REAL NOT NULL,
                       category   TEXT NOT NULL,
                       created_at TEXT NOT NULL
                   )"""
            )

    # ---------- users ----------
    def get_users(self):
        try:
            rows = self.conn.execute("SELECT name FROM users ORDER BY name").fetchall()
            return [r[0] for r in rows]
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not load users: {err}") from err

    def _get_or_create_user(self, name):
        row = self.conn.execute("SELECT id FROM users WHERE name = ?", (name,)).fetchone()
        if row:
            return row[0]
        cur = self.conn.execute("INSERT INTO users (name) VALUES (?)", (name,))
        return cur.lastrowid

    def delete_user(self, name):
        try:
            with self.conn:
                self.conn.execute("DELETE FROM users WHERE name = ?", (name,))
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not delete user: {err}") from err

    # ---------- records ----------
    def add_record(self, name, weight_kg, height_m, bmi, category, created_at=None):
        name = name.strip()
        if not name:
            raise DatabaseError("A user name is required to save a record.")
        created_at = created_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with self.conn:
                user_id = self._get_or_create_user(name)
                self.conn.execute(
                    """INSERT INTO records (user_id, weight_kg, height_m, bmi, category, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (user_id, weight_kg, height_m, bmi, category, created_at),
                )
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not save the record: {err}") from err

    def get_records(self, name):
        """Return a user's records, oldest first, as dicts."""
        try:
            rows = self.conn.execute(
                """SELECT r.id, r.created_at, r.weight_kg, r.height_m, r.bmi, r.category
                   FROM records r JOIN users u ON u.id = r.user_id
                   WHERE u.name = ?
                   ORDER BY r.created_at, r.id""",
                (name,),
            ).fetchall()
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not load records: {err}") from err
        keys = ("id", "created_at", "weight_kg", "height_m", "bmi", "category")
        return [dict(zip(keys, row)) for row in rows]

    def delete_record(self, record_id):
        try:
            with self.conn:
                self.conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        except sqlite3.Error as err:
            raise DatabaseError(f"Could not delete the record: {err}") from err

    def close(self):
        try:
            self.conn.close()
        except sqlite3.Error:
            pass
