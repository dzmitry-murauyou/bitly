"""Работа с базой данных SQLite."""

import os
import secrets
import sqlite3
import string
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

ALPHABET = string.ascii_letters + string.digits

SCHEMA = """
CREATE TABLE IF NOT EXISTS links (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    code          TEXT    NOT NULL UNIQUE,
    url           TEXT    NOT NULL,
    created_at    TEXT    NOT NULL,
    clicks        INTEGER NOT NULL DEFAULT 0,
    last_click_at TEXT
);
"""


class AliasExistsError(Exception):
    pass


class Database:
    def __init__(self, path: str) -> None:
        self.path = path
        directory = os.path.dirname(os.path.abspath(path))
        os.makedirs(directory, exist_ok=True)
        # WAL не используем: он не работает на сетевых ФС (например, на PythonAnywhere)
        with self.connect() as conn:
            conn.executescript(SCHEMA)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="seconds")

    @staticmethod
    def generate_code(length: int) -> str:
        return "".join(secrets.choice(ALPHABET) for _ in range(length))

    def create(self, url: str, code: Optional[str], code_length: int) -> sqlite3.Row:
        with self.connect() as conn:
            if code:
                try:
                    conn.execute(
                        "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                        (code, url, self._now()),
                    )
                except sqlite3.IntegrityError as exc:
                    raise AliasExistsError(code) from exc
            else:
                # Генерируем случайный код; при коллизии пробуем снова,
                # а после нескольких неудач увеличиваем длину.
                length = code_length
                for attempt in range(20):
                    code = self.generate_code(length)
                    try:
                        conn.execute(
                            "INSERT INTO links (code, url, created_at) VALUES (?, ?, ?)",
                            (code, url, self._now()),
                        )
                        break
                    except sqlite3.IntegrityError:
                        if attempt % 5 == 4:
                            length += 1
                else:  # pragma: no cover
                    raise RuntimeError("Не удалось сгенерировать уникальный код")
            return conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()

    def get(self, code: str) -> Optional[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute("SELECT * FROM links WHERE code = ?", (code,)).fetchone()

    def hit(self, code: str) -> Optional[str]:
        """Возвращает исходный URL и увеличивает счётчик переходов."""
        with self.connect() as conn:
            row = conn.execute("SELECT url FROM links WHERE code = ?", (code,)).fetchone()
            if row is None:
                return None
            conn.execute(
                "UPDATE links SET clicks = clicks + 1, last_click_at = ? WHERE code = ?",
                (self._now(), code),
            )
            return row["url"]

    def list(self, limit: int = 100, offset: int = 0) -> list[sqlite3.Row]:
        with self.connect() as conn:
            return conn.execute(
                "SELECT * FROM links ORDER BY id DESC LIMIT ? OFFSET ?", (limit, offset)
            ).fetchall()

    def stats(self) -> dict:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS links, COALESCE(SUM(clicks), 0) AS clicks FROM links"
            ).fetchone()
            return {"links": row["links"], "clicks": row["clicks"]}

    def delete(self, code: str) -> bool:
        with self.connect() as conn:
            cur = conn.execute("DELETE FROM links WHERE code = ?", (code,))
            return cur.rowcount > 0
