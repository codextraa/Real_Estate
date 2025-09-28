"""Test Cases for User"""

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.core.exceptions import ValidationError


class UserModelTest(TestCase):
    """Test Cases for User"""

    def test_user_creation(self):
        """Test creating normal user using email and password"""
        email = "anna@example.com"
        password = "Password@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        default_group = Group.objects.get_or_create(name="Default")[0]

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.username, email)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_agent)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertIn(default_group, user.groups.all())
        self.assertEqual(user.slug, "annaexamplecom")

    def test_create_user_without_valid_email(self):
        """Test creating user without valid email"""
        email = "email"
        password = "Password@123"
        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user(email=email, password=password)
        self.assertFalse(get_user_model().objects.filter(email=email).exists())
