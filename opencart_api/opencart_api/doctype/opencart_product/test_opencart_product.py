import frappe
import unittest

test_records = frappe.get_test_records('Opencart Product')


class TestOpencartProduct(unittest.TestCase):
    pass
