from . import money

PRICES = {"PEN": "1.15", "INK": "4.35", "PAD": "19.99", "CLIP": "0.07", "TAPE": "2.45"}


def price_cents(sku) -> int:
    return money.to_cents(PRICES[sku])
