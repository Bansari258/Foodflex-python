from django.test import TestCase
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from users.tests.factories import UserFactory, ProfileFactory
import logging

logger = logging.getLogger(__name__)

class ProfileModelTest(TestCase):
    def setUp(self):
        # Disconnect any post_save signals for User to prevent automatic Profile creation
        post_save.disconnect(sender=User, dispatch_uid="create_user_profile")
        
        # Create a fresh User and Profile
        self.user = UserFactory(email="bansarishah258@gmail.com")
        self.profile = ProfileFactory(user=self.user)

    def test_profile_creation(self):
        logger.info("Testing Profile model creation")
        self.assertEqual(self.profile.user.email, self.profile.user.username)
        self.assertTrue(isinstance(self.profile.phone, str))

    def test_profile_string_representation(self):
        logger.info("Testing Profile model string representation")
        expected_str = f"Profile of {self.profile.user.username}"
        self.assertEqual(str(self.profile), expected_str)