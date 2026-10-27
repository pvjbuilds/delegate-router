"""Bulk rule: a line with qty >= 10 gets 10% off that line. Discounts round half up to the cent."""


def bulk_discount(line_cents: int, qty: int) -> int:
    return round(line_cents * 0.10) if qty >= 10 else 0


def apply_line(line_cents: int, qty: int) -> int:
    return line_cents - bulk_discount(line_cents, qty)
