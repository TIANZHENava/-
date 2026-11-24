"""建库和按交易单号去重插入。"""

import sqlite3
from pathlib import Path

from ledger.models import Transaction

_SCHEMA = """
CREATE TABLE IF NOT EXISTS transactions (
    id            INTEGER PRIMARY KEY,
    occurred_on   TEXT    NOT NULL,
    merchant      TEXT    NOT NULL,
    goods         TEXT    NOT NULL DEFAULT '',
    amount_cents  INTEGER NOT NULL,
    category      TEXT    NOT NULL DEFAULT '未分类',
    source_hash   TEXT    NOT NULL UNIQUE
);
"""


def connect(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(Path(path))
    conn.row_factory = sqlite3.Row
    conn.execute(_SCHEMA)
    conn.commit()
    return conn


def insert_transactions(
    conn: sqlite3.Connection, rows: list[Transaction]
) -> tuple[int, int]:
    """写入流水。source_hash 已存在时跳过，不更新旧行。"""
    inserted = 0
    skipped = 0
    for row in rows:
        try:
            conn.execute(
                """
                INSERT INTO transactions (
                    occurred_on, merchant, goods, amount_cents, category, source_hash
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    row.occurred_on,
                    row.merchant,
                    row.goods,
                    row.amount_cents,
                    row.category,
                    row.source_hash,
                ),
            )
        except sqlite3.IntegrityError as exc:
            if "unique" not in str(exc).lower():
                raise
            skipped += 1
        else:
            inserted += 1
    conn.commit()
    return inserted, skipped
