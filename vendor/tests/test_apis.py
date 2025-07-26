from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from vendor.models import MenuItem
from vendor.tests.factories import VendorFactory, MenuItemFactory, OrderFactory, ReviewFactory
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from datetime import time
from django.core.files.uploadedfile import SimpleUploadedFile

logger = logging.getLogger(__name__)

class VendorAPIViewsTest(TestCase):
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
        self.token = RefreshToken.for_user(self.user)

    def test_vendor_signup_api(self):
        logger.info("Testing VendorSignupAPIView")
        response = self.client.post(reverse('vendor:api_signup'), {
            'vendor_email': 'newvendor@example.com',
            'password_register': 'B@ns@ri258',
            'confirm_password_register': 'B@ns@ri258',
            'fssai_number': '12345678925874',
            'gst_number': '24AAACH7409R2Z6',
            'health_trade_license_number': '1234567899685',
            'full_name': 'Bansari Shah',
            'owner_email': 'bansarishah258@gmail.com',
            'owner_phone': '06351115985'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['redirect_url'], reverse('vendor:profile_setup'))

    def test_vendor_login_api(self):
        logger.info("Testing VendorLoginAPIView")
        response = self.client.post(reverse('vendor:api_login'), {
            'email': 'bansarishah258@gmail.com',
            'password': 'B@ns@ri258'
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['redirect_url'], reverse('vendor:vendor_home'))

    def test_vendor_profile_setup_api_get(self):
        logger.info("Testing VendorProfileSetupAPIView GET")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        response = self.client.get(reverse('vendor:api_profile_setup'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['restaurant_email'], self.vendor.restaurant_email)

    def test_vendor_profile_setup_api_post(self):
        logger.info("Testing VendorProfileSetupAPIView POST")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        profile_image = SimpleUploadedFile(
            name='location_list_6_IFGgWm9.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('vendor:api_profile_setup'), {
            'restaurant_name': 'Cafe Bansari',
            'shop_no': '401, Gopal Complex',
            'floor': 'Surbhi Town',
            'area': 'Maninagar',
            'city': 'Ahmedabad',
            'landmark': '',
            'restaurant_phone': '06351115985',
            'restaurant_email': 'bansarishah258@gmail.com',
            'profile_image': profile_image,
            'description': '',
            'takeaway': False,
            'delivery': False,
            'category': 'cloud_kitchen',
            'open_time': '10:45:00',
            'close_time': '22:45:00'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['restaurant_name'], 'Cafe Bansari')

    def test_vendor_menu_setup_api(self):
        logger.info("Testing VendorMenuSetupAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_image = SimpleUploadedFile(
            name='menu_item.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('vendor:api_menu'), {
            'menu_items[0][name]': 'Test Item',
            'menu_items[0][price]': 15.99,
            'menu_items[0][description]': 'A test item',
            'menu_items[0][image]': menu_image,
            'menu_items[0][is_available]': True,
            'menu_items[0][category]': 'main'
        }, format='multipart')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['redirect_url'], reverse('vendor:vendor_home'))

    def test_vendor_dashboard_api(self):
        logger.info("Testing VendorDashboardAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        OrderFactory(vendor=self.vendor, total_amount=100.00)
        ReviewFactory(vendor=self.vendor, overall_rating=4.5)
        response = self.client.get(reverse('vendor:api_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['total_earnings'], 100.00)
        self.assertEqual(response.json()['data']['average_rating'], 4.5)

    def test_menu_item_list_api(self):
        logger.info("Testing MenuItemListAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_item = MenuItemFactory(vendor=self.vendor)
        response = self.client.get(reverse('vendor:menu_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(len(response.json()['data']), 1)

    def test_menu_item_create_api(self):
        logger.info("Testing MenuItemCreateAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_image = SimpleUploadedFile(
            name='new_item.jpg',
            content=b'file_content',
            content_type='image/jpeg'
        )
        response = self.client.post(reverse('vendor:menu_create'), {
            'name': 'New Item',
            'price': 20.00,
            'description': 'A new item',
            'image': menu_image,
            'is_available': True,
            'category': 'main'
        }, format='multipart')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['success'])

    def test_menu_item_update_api(self):
        logger.info("Testing MenuItemUpdateAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_item = MenuItemFactory(vendor=self.vendor)
        response = self.client.put(reverse('vendor:menu_update', args=[menu_item.id]), {
            'name': 'Updated Item',
            'price': 25.00
        }, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        menu_item.refresh_from_db()
        self.assertEqual(menu_item.name, 'Updated Item')

    def test_menu_item_delete_api(self):
        logger.info("Testing MenuItemDeleteAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_item = MenuItemFactory(vendor=self.vendor)
        response = self.client.delete(reverse('vendor:menu_delete', args=[menu_item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(MenuItem.objects.filter(id=menu_item.id).exists())

    def test_menu_item_detail_api(self):
        logger.info("Testing MenuItemDetailAPIView")
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token.access_token}')
        menu_item = MenuItemFactory(vendor=self.vendor)
        response = self.client.get(reverse('vendor:menu_detail', args=[menu_item.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['name'], menu_item.name)