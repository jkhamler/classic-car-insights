"""Shared parsing utilities for scrapers."""
import re
from datetime import datetime


def parse_price(text: str | None) -> float | None:
    if not text:
        return None
    cleaned = re.sub(r"[^\d.]", "", text.replace(",", ""))
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def detect_currency(text: str | None) -> str:
    if not text:
        return "GBP"
    text = text.strip()
    if text.startswith("$") or "USD" in text.upper():
        return "USD"
    if text.startswith("€") or "EUR" in text.upper():
        return "EUR"
    if "¥" in text or "JPY" in text.upper():
        return "JPY"
    return "GBP"


# Rough conversion rates — good enough for scoring, not for invoicing
RATES_TO_GBP = {
    "GBP": 1.0,
    "USD": 0.79,
    "EUR": 0.86,
    "JPY": 0.0053,
}


def to_gbp(amount: float | None, currency: str = "GBP") -> float | None:
    if amount is None:
        return None
    rate = RATES_TO_GBP.get(currency, 1.0)
    return round(amount * rate, 2)


def parse_mileage(text: str | None) -> tuple[int | None, str]:
    if not text:
        return None, "miles"
    text_lower = text.lower()
    unit = "km" if "km" in text_lower or "kilo" in text_lower else "miles"
    digits = re.sub(r"[^\d]", "", text)
    try:
        return int(digits), unit
    except (ValueError, TypeError):
        return None, unit


def parse_year(text: str | None) -> int | None:
    if not text:
        return None
    match = re.search(r"\b(19[6-9]\d|20[0-2]\d)\b", str(text))
    if match:
        return int(match.group(1))
    return None


def parse_date(text: str | None, formats: list[str] | None = None) -> datetime | None:
    if not text:
        return None
    if formats is None:
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y", "%m/%d/%Y"]
    text = text.strip()
    for fmt in formats:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def clean_text(text: str | None) -> str | None:
    if not text:
        return None
    return " ".join(text.split()).strip()
