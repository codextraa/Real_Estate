"""Test Cases for Users"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError

# import logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


class UserModelTest(TestCase):
    """Test Cases for Users"""

    def error_raise(self, email, password, error_type):
        with self.assertRaises(error_type):
            get_user_model().objects.create_user(
                email=email,
                password=password,
            )

        # try:
        #     user = get_user_model().objects.create_user(
        #         email=email,
        #         password=password,
        #     )
        # except Exception as e:
        #     # LOGGING/PRINTING THE ACTUAL EXCEPTION
        #     print("\n--- ACTUAL EXCEPTION RAISED ---")
        #     print(f"Type: {type(e)}")
        #     print(f"Value: {e}")

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

    def test_staff_creation(self):
        """Test creating staff using email and password"""
        email = "admin@example.com"
        password = "Django@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            is_staff=True,
        )

        default_group = Group.objects.get_or_create(name="Admin")[0]

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_agent)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(default_group, user.groups.all())
        self.assertEqual(user.slug, "adminexamplecom")


    def test_superuser_creation(self):
        """Test creating superuser using email and password"""
        email = "superuser@example.com"
        password = "Django@123"

        user = get_user_model().objects.create_superuser(
            email=email,
            password=password,
        )

        default_group = Group.objects.get_or_create(name="Superuser")[0]

        self.assertTrue(user.is_active)
        self.assertFalse(user.is_agent)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(default_group, user.groups.all())
        self.assertEqual(user.slug, "superuserexamplecom")



    def test_user_creation_with_duplicate_email(self):
        """Test creating user with duplicate email"""
        email = "test@example.com"
        password = "Django@123"

        get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )


    def test_user_creation_with_no_email(self):
        """Test creating user with no email"""
        email = ""
        password = "Django@123"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValueError,)

        self.assertFalse(get_user_model().objects.filter(email=email).exists())


    def test_user_creation_with_email_exceeding_max_length(self):
        """Test creating user with email exceeding max length"""
        email = """testtoubespidermancockroachfjksjkjfkslfjlkjfklsjfk
        lsjfklsjflweir9eujkljfljhgjhgjhgjhk@example.com"""
        password = "Django@123"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

        self.assertFalse(get_user_model().objects.filter(email=email).exists())

    def test_user_creation_with_duplicate_username(self):
        """Test creating user with duplicate username"""
        email1 = "test@example.com"
        email2 = "test2@example.com"
        username = "test"
        password = "Django@123"

        get_user_model().objects.create_user(
            email=email1,
            password=password,
            username=username,
        )

        with self.assertRaises(ValidationError):
            get_user_model().objects.create_user(
                email=email2,
                password=password,
                username=username,
            )


    def test_user_creation_with_no_password(self):
        """Test creating user with no password"""
        email = "test@example.com"
        password = ""

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )


    def test_user_creation_with_password_length_less_than_eight(self):
        """Test creating user with password length less than eight"""
        email = "test@example.com"
        password = "Django"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

    def test_user_creation_with_no_digits_in_password(self):
        """Test creating user with no digits in password"""
        email = "test@example.com"
        password = "Django@"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

    def test_user_creation_with_no_special_characters_in_password(self):
        """Test creating user with no special characters in password"""
        email = "test@example.com"
        password = "Django123"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

    def test_user_creation_with_no_uppercase_letters_in_password(self):
        """Test creating user with no uppercase letters in password"""
        email = "test@example.com"
        password = "django123"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

    def test_user_creation_with_no_lowercase_letters_in_password(self):
        """Test creating user with no lowercase letters in password"""
        email = "test@example.com"
        password = "DJANGO123"

        self.error_raise(
            email=email,
            password=password,
            error_type=ValidationError,
        )

    def test_superuser_creation_without_password(self):
        """Test creating superuser without password"""
        email = "superuser@example.com"
        password = ""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email=email,
                password=password,
            )


    def test_superuser_creation_with_staff_being_false(self):
        """Test creating superuser with staff being false"""
        email = "superuser@example.com"
        password = "Django@123"

        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email=email,
                password=password,
                is_staff=False,
            )

    def test_superuser_creation_without_setting_is_superuser_to_true(self):
        """Test creating superuser without setting is_superuser to true"""
        email = "superuser@example.com"
        password = "Django@123"

        with self.assertRaises(ValueError):
            get_user_model().objects.create_superuser(
                email=email,
                password=password,
                is_superuser=False,
            )

    def test_create_slug_from_email(self):
        """Test creating slug from email"""
        email = "lana@example.com"
        password = "Django@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.slug, "lanaexamplecom")

    def test_create_slug_from_username(self):
        """Test creating slug from username"""
        email = "lana@example.com"
        username = "lanastory"
        password = "Django@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            username=username,
        )

        self.assertEqual(user.slug, username)

    def test_check_slug_field_is_not_overridden(self):
        """Test creating slug from the given slug"""
        email = "lana@example.com"
        slug = "lanastory"
        password = "Django@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            slug=slug,
        )

        self.assertEqual(user.slug, "lanaexamplecom")

    def test_slug_is_updated(self):
        """Test slug is lowercase"""
        email = "lana@example.com"
        slug = "LANASTORY"
        password = "Django@123"

        user = get_user_model().objects.create_user(
            email=email,
            password=password,
            slug=slug,
        )

        user.username = "AnnaStory"
        user.save()

        self.assertEqual(user.slug, "annastory")
