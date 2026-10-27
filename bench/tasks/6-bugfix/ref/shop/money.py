from decimal import Decimal


def to_cents(price: str) -> int:
    return int(Decimal(price) * 100)


def fmt(cents: int) -> str:
    return f"{'-' if cents < 0 else ''}{abs(cents) // 100}.{abs(cents) % 100:02d}"
