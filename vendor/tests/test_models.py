from datetime import time
from django.test import TestCase
from vendor.models import Vendor, MenuItem, Order, Review
from vendor.tests.factories import VendorFactory, MenuItemFactory, OrderFactory, ReviewFactory
import logging

logger = logging.getLogger(__name__)

class VendorModelTest(TestCase):
    def setUp(self):
        self.vendor = VendorFactory()

    def test_vendor_str(self):
        logger.info("Testing Vendor __str__ method")
        self.assertEqual(str(self.vendor), f"{self.vendor.restaurant_name} - {self.vendor.user.email}")

    def test_vendor_average_rating(self):
        logger.info("Testing Vendor average_rating property")
        # No reviews yet
        self.assertEqual(self.vendor.average_rating, 0.0)

        # Add reviews
        ReviewFactory(vendor=self.vendor, overall_rating=4.0)
        ReviewFactory(vendor=self.vendor, overall_rating=5.0)
        self.assertEqual(self.vendor.average_rating, 9.0)  # (4.0 + 5.0) / 2 * 2 = 9.0

    def test_vendor_fields(self):
        logger.info("Testing Vendor fields")
        self.assertEqual(self.vendor.category, 'restaurant')
        self.assertTrue(self.vendor.takeaway)
        self.assertTrue(self.vendor.delivery)
        self.assertEqual(self.vendor.open_time, time(9, 0))
        self.assertEqual(self.vendor.close_time, time(21, 0))

class MenuItemModelTest(TestCase):
    def setUp(self):
        self.menu_item = MenuItemFactory()

    def test_menu_item_str(self):
        logger.info("Testing MenuItem __str__ method")
        self.assertEqual(str(self.menu_item), self.menu_item.name)

    def test_menu_item_fields(self):
        logger.info("Testing MenuItem fields")
        self.assertEqual(self.menu_item.category, 'main')
        self.assertTrue(self.menu_item.is_available)
        self.assertEqual(self.menu_item.price, 10.99)

class OrderModelTest(TestCase):
    def setUp(self):
        self.order = OrderFactory()

    def test_order_str(self):
        logger.info("Testing Order __str__ method")
        self.assertEqual(str(self.order), f"Order {self.order.id} - {self.order.vendor.restaurant_name}")

    def test_order_fields(self):
        logger.info("Testing Order fields")
        self.assertEqual(self.order.status, 'ongoing')
        self.assertEqual(self.order.total_amount, 10.99)
        self.assertEqual(self.order.order_items, {"items": [{"name": "Test Item", "price": 10.99, "quantity": 1}]})

