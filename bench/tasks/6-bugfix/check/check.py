import hashlib
from pathlib import Path
import sys
import unittest

work = Path(sys.argv[1]).resolve()
TEST_SHA256 = "82428ed5d313ffbcd1ea861572200581df939c322308e108a82802b948f2ad11"
assert hashlib.sha256((work / "test_shop.py").read_bytes()).hexdigest() == TEST_SHA256, "test_shop.py changed"
sys.dont_write_bytecode = True
sys.path.insert(0, str(work))
for name in list(sys.modules):
    if name.startswith("shop") or name == "test_shop":
        del sys.modules[name]
suite = unittest.defaultTestLoader.loadTestsFromName("test_shop")
assert unittest.TextTestRunner().run(suite).wasSuccessful(), "visible tests failed"
from shop.money import to_cents
from shop.cart import line_total, total
from shop.discounts import bulk_discount
from shop.report import receipt

for price, cents in [("0.07", 7), ("2.45", 245), ("1.15", 115), ("4.35", 435),
                     ("19.99", 1999), ("0.29", 29), ("1.13", 113), ("9.95", 995), ("0.57", 57)]:
    assert to_cents(price) == cents, f"to_cents({price})"
for sku, qty, expected in [("INK", 10, 3915), ("TAPE", 10, 2205), ("CLIP", 15, 94)]:
    assert line_total(sku, qty) == expected, f"line_total({sku}, {qty})"
for cents, qty, expected in [(2005, 12, 201), (45, 10, 5), (44, 10, 4), (999, 9, 0)]:
    assert bulk_discount(cents, qty) == expected, f"bulk_discount({cents}, {qty})"
assert total([("PAD", 2), ("INK", 10), ("CLIP", 15)]) == 8007, "wrong total"
assert receipt([("CLIP", 15), ("TAPE", 3)]) == "CLIP x15 0.94\nTAPE x3 7.35\nTOTAL 8.29", "wrong receipt"
