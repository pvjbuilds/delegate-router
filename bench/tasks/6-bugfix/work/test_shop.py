import unittest

from shop.cart import line_total
from shop.discounts import bulk_discount
from shop.money import to_cents
from shop.report import receipt


class ShopTests(unittest.TestCase):
    def test_to_cents(self):
        self.assertEqual(to_cents("19.99"), 1999)
        self.assertEqual(to_cents("4.35"), 435)

    def test_pad(self):
        self.assertEqual(line_total("PAD", 1), 1999)

    def test_bulk_pen(self):
        self.assertEqual(line_total("PEN", 10), 1035)

    def test_tape(self):
        self.assertEqual(line_total("TAPE", 5), 1225)

    def test_half_up(self):
        self.assertEqual(bulk_discount(1225, 10), 123)

    def test_receipt(self):
        self.assertEqual(receipt([("PAD", 1), ("PEN", 10)]),
                         "PAD x1 19.99\nPEN x10 10.35\nTOTAL 30.34")
