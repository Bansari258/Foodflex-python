from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from users.tests.factories import ProfileFactory
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models.signals import post_save
from rest_framework.test import APIClient
import logging

logger = logging.getLogger(__name__)

class UserLoginViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('users:login')
        self.user = User.objects.create_user(
            username='bansarishah258@gmail.com',
            email='bansarishah258@gmail.com',
            password='B@ns@ri258'
        )

    def test_login_success(self):
        logger.info("Testing successful user login")
        response = self.client.post(self.login_url, {
            'email': 'bansarishah258@gmail.com',
            'password': 'B@ns@ri258'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:home'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertIn('access_token', response.cookies)

    def test_login_invalid_credentials(self):
        logger.info("Testing login with invalid credentials")
        response = self.client.post(self.login_url, {
            'email': 'bansarishah258@gmail.com',
            'password': 'Wrong@123'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:landing'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_inactive_user(self):
        logger.info("Testing login with inactive user")
        self.user.is_active = False
        self.user.save()
        response = self.client.post(self.login_url, {
            'email': 'bansarishah258@gmail.com',
            'password': 'B@ns@ri258'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:landing'))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

class HomeViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.home_url = reverse('users:home')
        self.user = User.objects.create_user(
            username='bansarishah258@gmail.com',
            email='bansarishah258@gmail.com',
            password='B@ns@ri258'
        )

    def test_home_authenticated(self):
        logger.info("Testing home page with authenticated user")
        self.client.login(email=self.user.email, password='B@ns@ri258')
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/home.html')
        self.assertIn('top_vendors', response.context)

    def test_home_unauthenticated(self):
        logger.info("Testing home page with unauthenticated user")
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:landing'))

class ProfileViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse('users:profile')
        self.user = User.objects.create_user(
            username='bansarishah258@gmail.com',
            email='bansarishah258@gmail.com',
            password='B@ns@ri258'
        )
        # Disconnect signal to prevent automatic Profile creation
        post_save.disconnect(sender=User, dispatch_uid="create_user_profile")
        self.profile = ProfileFactory(user=self.user)

    def test_profile_get_authenticated(self):
        logger.info("Testing profile page GET with authenticated user")
        self.client.login(email=self.user.email, password='B@ns@ri258')
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')
        self.assertEqual(response.context['profile']['email'], self.user.email)

    def test_profile_post_update(self):
        logger.info("Testing profile page POST to update profile")
        self.client.login(email=self.user.email, password='B@ns@ri258')
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.access_token}')
        response = self.client.post(self.profile_url, {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': self.user.email,
            'phone': '1234567890'
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.profile_url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'User')
        self.assertEqual(self.client.session.get('phone'), '1234567890')

    def test_profile_unauthenticated(self):
        logger.info("Testing profile page with unauthenticated user")
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('users:landing'))