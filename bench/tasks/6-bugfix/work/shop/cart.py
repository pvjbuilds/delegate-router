from .catalog import price_cents
from .discounts import apply_line, bulk_discount


def line_total(sku, qty) -> int:
    gross = price_cents(sku) * qty
    gross -= bulk_discount(gross, qty)
    return apply_line(gross, qty)


def total(lines: list[tuple[str, int]]) -> int:
    return sum(line_total(sku, qty) for sku, qty in lines)
