"""Number check (WBS 5.3, FR-12, SC-5): reject commentary containing a figure not in the context.

Every number in the text must equal (ignoring its sign) a figure in the context or a number
in the owner's cause. Period labels (e.g. "May 2026", "2026-05") and the item's local codes
(e.g. "CC1010", "440000") are not figures and are removed before checking (doc 04 §4.5).
Thousands separators and decimal marks are read according to the language.
"""

import re
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation

from src.commentary.context import MONTHS_DE, MONTHS_EN

NUMBER = re.compile(r"\d+(?:[.,]\d+)*")


@dataclass
class CheckResult:
    passed: bool
    numbers_found: list = field(default_factory=list)
    unknown_numbers: list = field(default_factory=list)


def _period_patterns(period):
    year, month = period.split("-")
    month_names = [MONTHS_EN[int(month) - 1], MONTHS_DE[int(month) - 1]]
    short = [name[:3] for name in month_names]
    return [
        rf"{year}-{month}",                                     # 2026-05
        rf"{month}[./]{year}",                                  # 05.2026, 05/2026
        rf"(?:{'|'.join(month_names + short)})[ -]?(?:{year}|{year[2:]})\b",  # May 2026, May-26
        rf"(?<![\d.,]){year}(?![\d.,])",                        # a bare year
    ]


def _to_decimal(token, language):
    if language == "de":
        token = token.replace(".", "").replace(",", ".")
    else:
        token = token.replace(",", "")
    try:
        return abs(Decimal(token))
    except InvalidOperation:
        return None


def _numbers(text, language):
    return [(token, _to_decimal(token, language)) for token in NUMBER.findall(text)]


def allowed_numbers(context, language="en"):
    allowed = {abs(Decimal(str(value))) for value in context["figures"].values()}
    if context.get("owner_cause"):
        allowed |= {value for _, value in _numbers(context["owner_cause"], language) if value is not None}
    return allowed


def strip_non_figures(text, context):
    """Remove period labels and the item's local codes, which are not figures."""
    for code in (context.get("local_cost_centre"), context.get("local_account_code")):
        if code:
            text = re.sub(rf"(?<![\w-]){re.escape(code)}(?![\w-])", " ", text)
    for pattern in _period_patterns(context["period"]):
        text = re.sub(pattern, " ", text, flags=re.IGNORECASE)
    return text


def check(text, context, language="en"):
    allowed = allowed_numbers(context, language)
    found = _numbers(strip_non_figures(text, context), language)
    unknown = [token for token, value in found if value is None or value not in allowed]
    return CheckResult(passed=not unknown, numbers_found=[t for t, _ in found], unknown_numbers=unknown)
