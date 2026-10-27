from .catalog import price_cents
from .discounts import apply_line


def line_total(sku, qty) -> int:
    return apply_line(price_cents(sku) * qty, qty)


def total(lines: list[tuple[str, int]]) -> int:
    return sum(line_total(sku, qty) for sku, qty in lines)
