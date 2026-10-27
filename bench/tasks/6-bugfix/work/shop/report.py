from .cart import line_total, total
from .money import fmt


# TODO: check rounding here?
def receipt(lines) -> str:
    rows = [f"{sku} x{qty} {fmt(line_total(sku, qty))}" for sku, qty in lines]
    return "\n".join(rows + [f"TOTAL {fmt(total(lines))}"])
