"""读取微信支付账单 CSV，映射成流水记录。"""

import csv
import re
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path

from ledger.models import Transaction

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def load_wechat_csv(path: Path) -> tuple[list[Transaction], int]:
    """返回 (有效记录, 跳过的坏行数)。表头之前的说明行不计入坏行。"""
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as handle:
        lines = handle.readlines()

    header_at = next(
        (index for index, line in enumerate(lines) if line.startswith("交易时间")),
        None,
    )
    if header_at is None:
        return [], 0

    records: list[Transaction] = []
    bad = 0
    for row in csv.DictReader(lines[header_at:]):
        parsed = _parse_row(row)
        if parsed is None:
            bad += 1
        else:
            records.append(parsed)
    return records, bad


def _cell(row: dict[str, str | None], key: str) -> str:
    value = row.get(key)
    if value is None:
        return ""
    return str(value).strip()


def _parse_row(row: dict[str, str | None]) -> Transaction | None:
    occurred_raw = _cell(row, "交易时间")
    merchant = _cell(row, "交易对方")
    direction = _cell(row, "收/支")
    amount_raw = _cell(row, "金额(元)")
    source_hash = _cell(row, "交易单号")
    if not occurred_raw or not merchant or not direction or not amount_raw or not source_hash:
        return None

    occurred_on = occurred_raw[:10]
    if _DATE_RE.fullmatch(occurred_on) is None:
        return None
    if direction not in ("收入", "支出"):
        return None

    amount_cents = _amount_cents(amount_raw, direction)
    if amount_cents is None:
        return None

    goods = _cell(row, "商品")
    return Transaction(
        occurred_on=occurred_on,
        merchant=merchant,
        goods=goods,
        amount_cents=amount_cents,
        source_hash=source_hash,
    )


def _amount_cents(raw: str, direction: str) -> int | None:
    cleaned = raw.replace("¥", "").replace("￥", "").replace(",", "").replace(" ", "")
    if not cleaned:
        return None
    try:
        yuan = Decimal(cleaned)
    except InvalidOperation:
        return None
    if not yuan.is_finite():
        return None
    # 元转分，四舍五入。Decimal 默认是银行家舍入，这里指定 ROUND_HALF_UP。
    cents = (abs(yuan) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    value = int(cents)
    if direction == "支出":
        return -value
    return value
