from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APIClient
import logging

logger = logging.getLogger(__name__)

class UserSignupAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.signup_url = reverse('users:api_signup')

    def test_signup_success(self):
        logger.info("Testing UserSignupAPIView with valid data")
        # Use a unique email for each test to avoid conflicts
        unique_email = 'bansarishah258+test1@gmail.com'
        response = self.client.post(self.signup_url, {
            'first_name': 'Test',
            'last_name': 'User',
            'email': unique_email,
            'password': 'B@ns@ri258',
            'confirm_password': 'B@ns@ri258'
        }, format='json')  # Use format='json' instead of content_type
        self.assertEqual(response.status_code, 201, msg=response.json())
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['data']['user']['email'], unique_email)

    def test_signup_invalid_data(self):
        logger.info("Testing UserSignupAPIView with invalid data")
        response = self.client.post(self.signup_url, {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'bansarishah258+test2@gmail.com',
            'password': 'weak',
            'confirm_password': 'weak'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('password', response.json()['errors'])

class UserLoginAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:api_login')
        self.user = User.objects.create_user(
            username='bansarishah258@gmail.com',
            email='bansarishah258@gmail.com',
            password='temp'
        )
        self.user.set_password('B@ns@ri258')
        self.user.save()

    def test_login_success(self):
        logger.info("Testing UserLoginAPIView with valid data")
        response = self.client.post(self.login_url, {
            'email': 'bansarishah258@gmail.com',
            'password': 'B@ns@ri258'
        }, format='json')
        self.assertEqual(response.status_code, 200, msg=response.json())
        self.assertTrue(response.json()['success'])
        self.assertIn('access', response.json()['data'])
        self.assertEqual(response.json()['data']['user']['email'], 'bansarishah258@gmail.com')

    def test_login_invalid_credentials(self):
        logger.info("Testing UserLoginAPIView with invalid credentials")
        response = self.client.post(self.login_url, {
            'email': 'bansarishah258@gmail.com',
            'password': 'Wrong@123'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])
        self.assertIn('non_field_errors', response.json()['errors'])
        self.assertEqual(str(response.json()['errors']['non_field_errors'][0]), 'Invalid email or password.')

class UserSessionAPIViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.session_url = reverse('users:api_user_session')
        self.user = User.objects.create_user(
            username='bansarishah258+session@gmail.com',
            email='bansarishah258+session@gmail.com',
            password='B@ns@ri258'
        )

    def test_session_authenticated(self):
        logger.info("Testing UserSessionAPIView with authenticated user")
        self.client.login(email=self.user.email, password='B@ns@ri258')
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertEqual(response.json()['user']['email'], self.user.email)

    def test_session_unauthenticated(self):
        logger.info("Testing UserSessionAPIView with unauthenticated user")
        response = self.client.get(self.session_url)
        self.assertEqual(response.status_code, 401)  # Updated to match the API view