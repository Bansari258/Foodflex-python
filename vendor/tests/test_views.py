from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from vendor.tests.factories import VendorFactory, OrderFactory
from rest_framework.test import APIClient
import logging

logger = logging.getLogger(__name__)

class VendorTemplateViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='bansarishah258@gmail.com',
            email='bansarishah258@gmail.com',
            password='B@ns@ri258'
        )
        self.vendor = VendorFactory(
            user=self.user,
            restaurant_name='Cafe Bansari',
            restaurant_email='bansarishah258@gmail.com',
            restaurant_phone='06351115985',
            shop_no='401, Gopal Complex',
            floor='Surbhi Town',
            area='Maninagar',
            city='Ahmedabad',
            landmark='',
            takeaway=True,
            delivery=False,
            category='cloud_kitchen',
            open_time='10:45:00',
            close_time='22:45:00',
            full_name='Bansari Shah',
            owner_email='bansarishah258@gmail.com',
            owner_phone='06351115985',
            fssai_number='12345678925874',
            gst_number='24AAACH7409R2Z6',
            health_trade_license_number='1234567899685'
        )

    def test_vendor_landing(self):
        logger.info("Testing vendor_landing view")
        response = self.client.get(reverse('vendor:vendor_landing'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/vendor_landing.html')

    def test_vendor_signup(self):
        logger.info("Testing vendor_signup view")
        response = self.client.get(reverse('vendor:vendor_signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/vendor_signup.html')

    def test_vendor_profile_setup_authenticated(self):
        logger.info("Testing vendor_profile_setup view with authenticated user")
        self.client.force_login(self.user)  # Use force_login for session-based auth
        response = self.client.get(reverse('vendor:profile_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/vendor_profile_setup.html')

    def test_vendor_profile_setup_unauthenticated(self):
        logger.info("Testing vendor_profile_setup view with unauthenticated user")
        response = self.client.get(reverse('vendor:profile_setup'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vendor:vendor_signup'))


    def test_vendor_home_authenticated(self):
        logger.info("Testing vendor_home view with authenticated user")
        self.client.force_login(self.user)
        response = self.client.get(reverse('vendor:vendor_home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/vendor_home.html')
        self.assertIn('total_earnings', response.context)

    def test_vendor_logout(self):
        logger.info("Testing vendor_logout view")
        self.client.force_login(self.user)
        response = self.client.get(reverse('vendor:vendor_logout'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vendor:vendor_landing'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_orders_authenticated(self):
        logger.info("Testing orders view with authenticated user")
        self.client.force_login(self.user)
        OrderFactory(vendor=self.vendor, status='ongoing')
        response = self.client.get(reverse('vendor:orders'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/vendor_orders.html')
        self.assertIn('ongoing_orders', response.context)

    def test_complete_order(self):
        logger.info("Testing complete_order view")
        self.client.force_login(self.user)
        order = OrderFactory(vendor=self.vendor, status='ongoing')
        response = self.client.get(reverse('vendor:complete_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vendor:orders'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'completed')

    def test_cancel_order(self):
        logger.info("Testing cancel_order view")
        self.client.force_login(self.user)
        order = OrderFactory(vendor=self.vendor, status='ongoing')
        response = self.client.get(reverse('vendor:cancel_order', args=[order.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('vendor:orders'))
        order.refresh_from_db()
        self.assertEqual(order.status, 'cancelled')

    def test_vendor_earnings_authenticated(self):
        logger.info("Testing vendor_earnings view with authenticated user")
        self.client.force_login(self.user)
        OrderFactory(vendor=self.vendor, total_amount=100.00)
        response = self.client.get(reverse('vendor:earnings'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'vendor/earnings.html')
        self.assertIn('total_earnings', response.context)
        self.assertEqual(response.context['total_earnings'], 100.00)