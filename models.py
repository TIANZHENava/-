
from dataclasses import dataclass

'''账单模板'''
@dataclass(frozen=True)
class Transaction:
    occurred_on: str
    merchant: str
    goods: str
    amount_cents: int
    source_hash: str
    category: str = "未分类"

'''报告模板'''
@dataclass(frozen=True)
class MonthReport:
    year: int
    month: int
    income_cents: int
    expense_cents: int
    balance_cents: int
    top_merchants: tuple[tuple[str, int], ...]
    empty: bool
