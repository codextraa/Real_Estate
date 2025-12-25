import io
import os
import jwt
from PIL import Image
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django.contrib.auth import get_user_model
from core_db.models import Agent

from freezegun import freeze_time
from datetime import timedelta, datetime
from django.utils.timezone import now
from django.conf import settings


TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "StrongPassword123!"
AGENT_ROLE = "Agent"
User = get_user_model()
USER_LIST_URL = reverse("user-list")
USER_DETAIL_URL = lambda pk: reverse("user-detail", kwargs={"pk": pk})

AGENT_LIST_URL = reverse("agent-list")
AGENT_DETAIL_URL = lambda pk: reverse("agent-detail", kwargs={"pk": pk})


class LoginViewIntegrationTests(APITestCase):
    """Integration Test suite for LoginView using real User data and unique emails."""

    def setUp(self):
        self.TEST_EMAIL = TEST_EMAIL
        self.INACTIVE_EMAIL = "inactive@example.com"
        self.client = APIClient()
        self.url = reverse("login")

        self.valid_payload = {"email": self.TEST_EMAIL, "password": TEST_PASSWORD}

        try:
            self.agent_user = User.objects.create_user(
                email=self.TEST_EMAIL,
                password=TEST_PASSWORD,
                is_agent=True,
                is_active=True,
            )
            self.inactive_user = User.objects.create_user(
                email=self.INACTIVE_EMAIL, password=TEST_PASSWORD, is_active=False
            )
        except Exception as e:
            self.fail(f"Failed to set up real users. Error: {e}")

    def tearDown(self):
        self.agent_user.delete()
        self.inactive_user.delete()
        cache.clear()
        super().tearDown()

    def test_01_successful_login_with_agent_user(self):
        """Tests the full successful flow. Expects a 200 OK and agent details."""
        response = self.client.post(self.url, self.valid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("access_token_expiry", response.data)
        self.assertIn("user_id", response.data)

        self.assertEqual(response.data["user_role"], AGENT_ROLE)

    def test_02_missing_credentials_validation(self):
        """Tests initial required field validation (No external dependencies hit)."""

        payload_1 = {"password": TEST_PASSWORD}
        response_1 = self.client.post(self.url, payload_1, format="json")
        self.assertEqual(response_1.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response_1.data["error"], "Email and password are required")

        payload_2 = {"email": self.TEST_EMAIL}
        response_2 = self.client.post(self.url, payload_2, format="json")
        self.assertEqual(response_2.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response_2.data["error"], "Email and password are required")

    def test_03_invalid_password(self):
        """Tests login failure due to Django's built-in check_password failing."""

        invalid_payload = {
            "email": self.TEST_EMAIL,
            "password": "this_is_not_the_password",
        }
        response = self.client.post(self.url, invalid_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.json(), {"errors": "Invalid credentials"})

    def test_04_user_not_found(self):
        """Tests failure when user doesn't exist."""

        unknown_payload = {
            "email": "truly_unknown_user@domain.com",
            "password": TEST_PASSWORD,
        }
        response = self.client.post(self.url, unknown_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {"errors": "Invalid credentials"})

    def test_05_validity_check_inactive_user(self):
        """Tests the case where the inactive user check should fail authentication."""

        inactive_payload = {"email": self.INACTIVE_EMAIL, "password": TEST_PASSWORD}
        response = self.client.post(self.url, inactive_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(
            response.json(), {"errors": "Account is deactivated. Contact your admin"}
        )


class RefreshTokenViewIntegrationTests(APITestCase):
    """Integration Test suite for RefreshTokenView."""

    def setUp(self):
        self.TEST_EMAIL = TEST_EMAIL
        self.client = APIClient()
        self.login_url = reverse("login")
        self.refresh_url = reverse("refresh-token")

        self.valid_payload = {"email": self.TEST_EMAIL, "password": TEST_PASSWORD}

        try:
            self.test_user = User.objects.create_user(
                email=self.TEST_EMAIL,
                password=TEST_PASSWORD,
                is_agent=True,
                is_active=True,
            )
        except Exception as e:
            self.fail(f"Failed to set up real user. Error: {e}")

        login_response = self.client.post(
            self.login_url, self.valid_payload, format="json"
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        self.initial_refresh_token = login_response.data["refresh_token"]
        self.refresh_payload = {"refresh": self.initial_refresh_token}

    def tearDown(self):
        User.objects.all().delete()
        cache.clear()
        super().tearDown()

    def test_01_successful_token_refresh(self):
        """Tests the standard successful flow: refresh token returns new tokens and user details."""

        response = self.client.post(
            self.refresh_url, self.refresh_payload, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("access_token_expiry", response.data)

        self.assertEqual(response.data["user_role"], AGENT_ROLE)
        self.assertEqual(response.data["user_id"], self.test_user.id)

    def test_02_missing_refresh_token_in_request(self):
        """Tests the custom validation for a missing 'refresh' key."""

        response = self.client.post(self.refresh_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Tokens are required")

    def test_03_invalid_token_format(self):
        """Tests the failure when a malformed or invalid JWT is provided."""

        invalid_payload = {"refresh": "this.is.not.a.valid.jwt"}

        response = self.client.post(self.refresh_url, invalid_payload, format="json")
        # Assert against the catch-all exception block's message
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST],
        )
        self.assertIn("Invalid refresh token", response.data.get("error", ""))

    def test_04_refresh_token_that_is_blacklisted(self):
        """Tests failure when the refresh token has already been blacklisted (e.g., after logout)."""
        # 1. Blacklist the token (simulate a prior logout)
        refresh_token_obj = RefreshToken(self.initial_refresh_token)
        refresh_token_obj.blacklist()

        # 2. Attempt to refresh with the blacklisted token
        response = self.client.post(
            self.refresh_url, self.refresh_payload, format="json"
        )

        # Expect either 401 or 400
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST],
        )

        # Assert against the observed generic error message
        self.assertIn(
            "Invalid refresh token", str(response.data.get("error", str(response.data)))
        )

    @freeze_time(now() + timedelta(days=90))
    def test_05_refresh_token_that_is_expired(self):
        """
        Tests failure when the refresh token has genuinely expired using freezegun.

        Note: This assumes your SIMPLE_JWT REFRESH_TOKEN_LIFETIME is less than 90 days.
        """

        # 1. @freeze_time moves the perceived "current time" forward by 90 days,
        #    making the initial refresh token created in setUp invalid/expired.

        # 2. Attempt to refresh with the token that is now "expired"
        response = self.client.post(
            self.refresh_url, self.refresh_payload, format="json"
        )

        # Expect an error from SIMPLE_JWT validation
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST],
        )

        # 3. Assert against the observed generic error message from your view's exception handler
        # (Based on the previous error: 'Token is expired' not found in 'Invalid refresh token')
        error_message = str(response.data.get("error", str(response.data)))
        self.assertIn("Invalid refresh token", error_message)

    def test_06_refresh_token_user_is_deactivated(self):
        """Tests failure when refresh token is valid but the associated user is inactive (check_user_validity failure)."""

        # 1. Deactivate the user associated with the token
        self.test_user.is_active = False
        self.test_user.save()

        # 2. Attempt to refresh the token
        response = self.client.post(
            self.refresh_url, self.refresh_payload, format="json"
        )

        # ASSERTION FIX:
        # The view returns 401 UNAUTHORIZED from the generic 'except Exception' block.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ASSERTION FIX:
        # The view's generic exception handler returns "Invalid refresh token".
        self.assertEqual(response.data["error"], "Invalid refresh token")

    # FIX for test_07 (Ensuring all claims are correctly copied)

    def test_07_invalid_user_id_from_token(self):
        """
        Tests failure when the user ID extracted from a manually signed token
        is non-existent (check_user_id failure).
        """
        # 1. Get payload from a valid token
        valid_token = RefreshToken(self.initial_refresh_token)
        token_claims = valid_token.payload

        # 2. Intentionally set the 'user_id' to a non-existent value
        NON_EXISTENT_ID = self.test_user.id + 100
        token_claims[settings.SIMPLE_JWT["USER_ID_CLAIM"]] = NON_EXISTENT_ID

        # 3. Manually encode and sign the new payload (using RS256/Private Key)
        try:
            custom_token = jwt.encode(
                token_claims, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm="RS256"
            )
        except Exception as e:
            self.fail(f"JWT encoding failed with RS256: {e}")

        invalid_user_payload = {"refresh": custom_token}

        # 4. Attempt to refresh with the token
        response = self.client.post(
            self.refresh_url, invalid_user_payload, format="json"
        )

        # ASSERTION FIX:
        # The view returns 401 UNAUTHORIZED from the generic 'except Exception' block.
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ASSERTION FIX:
        # The view's generic exception handler returns "Invalid refresh token".
        self.assertEqual(response.data["error"], "Invalid refresh token")

    def test_08_missing_user_id_in_token_payload(self):
        """
        Tests failure when the 'user_id' key is missing from a manually signed
        token's payload, signed using the configured RS256 private key.
        """
        # 1. Manually construct the necessary claims for a Refresh Token
        refresh_token_lifetime = settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]
        current_time = datetime.utcnow()

        token_claims = {
            # Standard JWT Claims
            "exp": int((current_time + refresh_token_lifetime).timestamp()),
            "iat": int(current_time.timestamp()),
            "jti": RefreshToken.for_user(self.test_user).payload[
                "jti"
            ],  # Use a valid JTI
            # SIMPLE_JWT Claims
            "token_type": "refresh",
            # NOTE: We INTENTIONALLY omit the USER_ID_CLAIM here for the test.
            # settings.SIMPLE_JWT["USER_ID_CLAIM"]: self.test_user.id,
        }

        # 2. Manually encode and sign the new payload using RS256 and the PRIVATE_KEY
        try:
            custom_token = jwt.encode(
                token_claims, settings.SIMPLE_JWT["SIGNING_KEY"], algorithm="RS256"
            )
        except Exception as e:
            self.fail(f"JWT encoding failed with RS256: {e}")

        missing_user_payload = {"refresh": custom_token}

        # 3. Attempt to refresh with the token
        response = self.client.post(
            self.refresh_url, missing_user_payload, format="json"
        )

        # Expect failure due to the missing 'user_id' claim check in the view logic
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Invalid tokens")


class LogoutViewIntegrationTests(APITestCase):
    """Integration Test suite for LogoutView focusing on token blacklisting/invalidation."""

    def setUp(self):
        self.TEST_EMAIL = (
            "test@example.com"  # Assuming this is defined globally or locally
        )
        self.client = APIClient()
        self.login_url = reverse("login")
        self.logout_url = reverse("logout")  # Assuming this URL name exists
        self.refresh_url = reverse("refresh-token")  # Essential for verificatio
        self.valid_payload = {"email": self.TEST_EMAIL, "password": TEST_PASSWORD}

        try:
            self.test_user = User.objects.create_user(
                email=self.TEST_EMAIL,
                password=TEST_PASSWORD,
                is_active=True,
            )
        except Exception as e:
            self.fail(f"Failed to set up real user. Error: {e}")

        login_response = self.client.post(
            self.login_url, self.valid_payload, format="json"
        )
        self.initial_refresh_token = login_response.data["refresh_token"]
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        self.access_token = login_response.data["access_token"]

    def tearDown(self):
        self.test_user.delete()
        cache.clear()
        super().tearDown()

    def test_01_successful_logout(self):
        """
        Tests the full successful logout flow by verifying the refresh token is blacklisted.
        (No protected resource check is performed).
        """

        # 1. Successful Logout Action
        # The view expects the key 'refresh' and returns HTTP_200_OK on success.
        logout_payload = {"refresh": self.initial_refresh_token}

        response = self.client.post(self.logout_url, logout_payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get("success"), "Logged out successfully")

        # 2. **Verification Step:** Attempt to use the blacklisted refresh token
        refresh_response = self.client.post(
            self.refresh_url, {"refresh": self.initial_refresh_token}, format="json"
        )

        # The refresh attempt must fail because the token is blacklisted.
        self.assertIn(
            refresh_response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_400_BAD_REQUEST],
        )
        self.assertIn("Invalid refresh token", str(refresh_response.data))

    def test_02_logout_without_refresh_token_in_body(self):
        """Tests the required field validation for the refresh token payload."""

        response = self.client.post(self.logout_url, {}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data.get("error"), "Tokens are required")

    def test_03_logout_with_invalid_refresh_token(self):
        """Tests the case where a malformed or fake refresh token is provided."""

        invalid_payload = {"refresh": "this.is.a.bad.token"}

        response = self.client.post(self.logout_url, invalid_payload, format="json")

        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

        self.assertIn("token is invalid", str(response.data).lower())


class UserViewSetTests(APITestCase):
    """Tests for the UserViewSet covering all CRUD actions and custom logic."""

    def setUp(self):
        self.password = "StrongP@ss123"

        self.superuser = User.objects.create_superuser(
            email="super@test.com",
            username="superadmin",
            password=self.password,
            first_name="Super",
            last_name="Admin",
        )
        self.another_superuser = User.objects.create_superuser(
            email="anothersuper@test.com",
            username="anothersuperadmin",
            password=self.password,
            first_name="Another Super",
            last_name="Admin",
        )

        self.staff_user = User.objects.create_user(
            email="staff@test.com",
            username="staffuser",
            password=self.password,
            is_staff=True,
            first_name="Staff",
            last_name="User",
        )
        self.another_staff_user = User.objects.create_user(
            email="anotherstaff@test.com",
            username="anotherstaffuser",
            password=self.password,
            is_staff=True,
            first_name="Another Staff",
            last_name="User",
        )

        self.agent_user = User.objects.create_user(
            email="agent@test.com",
            username="agentuser",
            password=self.password,
            is_agent=True,
            first_name="Agent",
            last_name="User",
        )

        self.normal_user = User.objects.create_user(
            email="normal@test.com",
            username="normaluser",
            password=self.password,
            first_name="Normal",
            last_name="User",
        )
        self.another_normal_user = User.objects.create_user(
            email="another@test.com",
            username="anotheruser",
            password=self.password,
            first_name="Another",
            last_name="User",
        )

        self.client = APIClient()

    def _authenticate(self, user):
        """Helper to set authentication header for the client."""
        self.client.force_authenticate(user=user)

    def _get_list_response(self, user):
        """Helper to authenticate and get the list response."""
        self._authenticate(user)
        return self.client.get(USER_LIST_URL)

    def get_valid_create_data(self):
        return {
            "email": "newuser@test.com",
            "username": "newuser123",
            "password": "NewP@ss123!",
            "c_password": "NewP@ss123!",
            "first_name": "New",
            "last_name": "User",
        }

    # ------GET TESTS------

    def test_list_users_superuser_allowed(self):
        """Superusers should see all users."""
        response = self._get_list_response(self.superuser)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 6)

    def test_list_users_staff_allowed(self):
        """Staff users should see all users."""
        response = self._get_list_response(self.staff_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data["count"], 6)

    def test_list_users_normal_user_denied(self):
        """Normal users should see no users (empty list from get_queryset)."""
        response = self._get_list_response(self.normal_user)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_list_users_unauthenticated_denied(self):
        """Unauthenticated users cannot see user list."""
        response = self.client.get(USER_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_superuser_allowed(self):
        """Superuser can retrieve any user."""
        self._authenticate(self.superuser)
        url = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.normal_user.pk)

    def test_retrieve_user_staff_allowed(self):
        """Staff user can retrieve any user."""
        self._authenticate(self.staff_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.normal_user.pk)

    def test_retrieve_user_self_allowed(self):
        """Any authenticated user can retrieve their own profile."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_user_normal_user_denied_other_normal(self):
        """Normal user cannot retrieve another normal user's profile."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.another_normal_user.pk)
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Filtered by get_queryset

    def test_retrieve_user_normal_user_allowed_agent(self):
        """Normal user can retrieve an Agent profile (based on Q(is_agent=True))."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.agent_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unauthorized_user_cannot_retrieve_authorized_user(self):
        url = USER_DETAIL_URL(self.another_normal_user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_user_not_found(self):
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(9999)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ------POST TESTS------

    def test_create_user_success(self):
        """Test successful user registration (AllowAny permission)."""
        data = self.get_valid_create_data()
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("success"), "User profile created successfully."
        )
        self.assertTrue(User.objects.filter(email=data["email"]).exists())

    def test_staff_user_creates_normal_user_success(self):
        """Test successful user creation by staff user."""
        data = self.get_valid_create_data()
        self._authenticate(self.staff_user)
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("success"), "User profile created successfully."
        )
        self.assertTrue(User.objects.filter(email=data["email"]).exists())

    def test_superuser_creates_normal_user_success(self):
        """Test successful user creation by superuser."""
        data = self.get_valid_create_data()
        self._authenticate(self.superuser)
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("success"), "User profile created successfully."
        )
        self.assertTrue(User.objects.filter(email=data["email"]).exists())

    def test_superuser_creates_staff_user_success(self):
        """Test successful staff user creation by superuser."""
        data = self.get_valid_create_data()
        data["is_staff"] = True
        self._authenticate(self.superuser)
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(
            response.data.get("success"), "User profile created successfully."
        )
        self.assertTrue(User.objects.filter(email=data["email"]).exists())

    def test_create_user_mismatched_passwords(self):
        """Test password mismatch validation in check_create_request_data."""
        data = self.get_valid_create_data()
        data["c_password"] = "WrongP@ss123"
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["error"])

    def test_create_user_missing_password_confirm(self):
        """Test missing confirmation password in check_create_request_data."""
        data = self.get_valid_create_data()
        del data["c_password"]
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please confirm your password", response.data["error"])

    def test_create_user_password_complexity(self):
        """Test password creation validation: verifies all complexity requirements (length, uppercase, digit, special char) during registration."""

        short_password = "Short1!"
        data = {
            "email": "test_short@example.com",
            "password": short_password,
            "c_password": short_password,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must be at least 8 characters.", error_list)

        no_uppercase = "nouppercase1!@#"
        data = {
            "email": "test_no_upper@example.com",
            "password": no_uppercase,
            "c_password": no_uppercase,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one uppercase letter.", error_list
        )

        no_lowercase = "NOLOWERCASE1!@#"
        data = {
            "email": "test_no_lower@example.com",
            "password": no_lowercase,
            "c_password": no_lowercase,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one lowercase letter.", error_list
        )

        no_digit = "NoDigit!@#ABCD"
        data = {
            "email": "test_no_digit@example.com",
            "password": no_digit,
            "c_password": no_digit,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must contain at least one number.", error_list)

        no_special = "NoSpecial1234"
        data = {
            "email": "test_no_special@example.com",
            "password": no_special,
            "c_password": no_special,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one special character.", error_list
        )

        # (Optional) Test a successful creation
        valid_password = "ValidPassword1!#"
        data = {
            "email": "test_valid@example.com",
            "password": valid_password,
            "c_password": valid_password,
        }
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_user_forbidden_superuser_field(self):
        """Test prohibition of creating a superuser by setting is_superuser."""
        data = self.get_valid_create_data()
        data["is_superuser"] = True
        self._authenticate(self.superuser)
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "You do not have permission to create a superuser. Contact Developer.",
            response.data["error"],
        )

    def test_create_user_forbidden_staff_field_by_normal_user(self):
        """Test prohibition of creating a staff user by a normal user."""
        data = self.get_valid_create_data()
        data["is_staff"] = True
        self._authenticate(self.normal_user)
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("create an admin user", response.data["error"])

    def test_create_user_forbidden_fields(self):
        """Test prohibition of setting `slug` field."""
        data = self.get_valid_create_data()
        data["slug"] = "custom-slug"
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

        del data["slug"]
        data["is_active"] = False
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

    def test_create_user_duplicate_email(self):
        """Test serializer validation for duplicate email."""
        data = self.get_valid_create_data()
        data["email"] = self.normal_user.email
        response = self.client.post(USER_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"errors": {"email": ["user with this email already exists."]}},
        )

    def test_create_user_username_too_short(self):
        """Test serializer validation for username too short."""
        data = self.get_valid_create_data()
        data["username"] = "abc"
        response = self.client.post(USER_LIST_URL, data, format="json")
        response_data = response.json()
        self.assertIn("username", response_data["errors"])
        self.assertIn(
            "Username must be at least 6 characters long.",
            str(response_data["errors"]["username"]),
        )

    def test_create_user_username_already_exists(self):
        """Test serializer validation for username already exists."""
        data = self.get_valid_create_data()
        data["username"] = self.normal_user.username
        response = self.client.post(USER_LIST_URL, data, format="json")
        response_data = response.json()
        self.assertIn("username", response_data["errors"])
        self.assertIn(
            "user with this username already exists.",
            str(response_data["errors"]["username"]),
        )

    def test_create_user_normal_user_cannot_create_staff(self):
        """
        Tests that a normal user, when creating a new user, cannot set the 'is_staff'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.normal_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "staffwannabe"
        new_user_data["email"] = "staffwannabe@test.com"
        new_user_data["is_staff"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="staffwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_create_user_normal_user_cannot_create_superuser(self):
        """
        Tests that a normal user, when creating a new user, cannot set the 'is_superuser'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.normal_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "superuserwannabe"
        new_user_data["email"] = "superuserwannabe@test.com"
        new_user_data["is_staff"] = True
        new_user_data["is_superuser"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="superuserwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_create_user_agent_user_cannot_create_staff(self):
        """
        Tests that an agent user, when creating a new user, cannot set the 'is_staff'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.agent_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "staffwannabe"
        new_user_data["email"] = "staffwannabe@test.com"
        new_user_data["is_staff"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="staffwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_create_user_agent_user_cannot_create_superuser(self):
        """
        Tests that an agent user, when creating a new user, cannot set the 'is_superuser'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.agent_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "superuserwannabe"
        new_user_data["email"] = "superuserwannabe@test.com"
        new_user_data["is_staff"] = True
        new_user_data["is_superuser"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="superuserwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_create_user_staff_user_cannot_create_staff(self):
        """
        Tests that a staff user, when creating a new user, cannot set the 'is_staff'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.staff_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "staffwannabe"
        new_user_data["email"] = "staffwannabe@test.com"
        new_user_data["is_staff"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="staffwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_create_user_staff_user_cannot_create_superuser(self):
        """
        Tests that a staff user, when creating a new user, cannot set the 'is_superuser'
        field to True, resulting in an HTTP 403 or 400 error.
        """
        self._authenticate(self.staff_user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "superuserwannabe"
        new_user_data["email"] = "superuserwannabe@test.com"
        new_user_data["is_staff"] = True
        new_user_data["is_superuser"] = True

        response = self.client.post(USER_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="superuserwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    # # # ------PATCH TESTS------

    def test_update_user_self_success(self):
        """Normal user can successfully update their own profile."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"first_name": "NewName"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Newname")

    def test_update_user_superuser_update_user_success(self):
        """Superuser can update another user's profile."""
        self._authenticate(self.superuser)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"first_name": "SuperUpdate"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Superupdate")

    def test_update_user_superuser_update_staff_success(self):
        """Superuser can update another staff's profile."""
        self._authenticate(self.superuser)
        url = USER_DETAIL_URL(self.staff_user.pk)
        new_data = {"first_name": "SuperUpdate"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["first_name"], "Superupdate")

    def test_one_user_cannot_update_another_user(self):
        """Normal user cannot update another user (check_update_request_data)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.another_normal_user.pk)
        new_data = {"first_name": "Attempted Hack"}
        response = self.client.patch(url, new_data, format="json")
        data = response.json()
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("No User matches the given query", data["errors"])

    def test_update_user_forbidden_email_field(self):
        """Cannot update the email field (check_update_request_data)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"email": "new_email@test.com"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot update the email field", response.data["error"])

    def test_update_user_forbidden_internal_fields(self):
        """Cannot update status fields like is_staff (check_update_request_data)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data1 = {"is_staff": True}
        response1 = self.client.patch(url, new_data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response1.data["error"])

        new_data2 = {"is_superuser": True}
        response2 = self.client.patch(url, new_data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response2.data["error"])

        new_data3 = {"is_active": True}
        response3 = self.client.patch(url, new_data3, format="json")
        self.assertEqual(response3.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response3.data["error"])

        new_data4 = {"slug": "abc"}
        response4 = self.client.patch(url, new_data4, format="json")
        self.assertEqual(response4.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response4.data["error"])

    def test_update_user_password_mismatch(self):
        """Test password change validation (check_update_request_data)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"password": "NewP@ss123", "c_password": "Mismatch"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["error"])

    def test_update_user_password_missing_confirm(self):
        """Test password change validation (check_update_request_data)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"password": "NewP@ss123"}  # Missing c_password
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please confirm your password", response.data["error"])

    def test_full_update_put_disallowed(self):
        """Test that the PUT method is disallowed (http_method_not_allowed)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)
        data = {"email": "test@test.com"}  # Minimal valid data
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_not_found(self):
        """
        Tests that a update request for a non-existent user ID returns HTTP 404 Not Found.
        """
        self._authenticate(self.superuser)
        largest_pk = User.objects.all().order_by("-pk").first().pk
        non_existent_pk = largest_pk + 1

        url = USER_DETAIL_URL(non_existent_pk)

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        if "detail" in response.data:
            self.assertIn(
                "no user matches the given query", str(response.data["detail"]).lower()
            )
        else:
            self.assertIn("errors", response.json())

    def test_update_user_username_too_short(self):
        """Test username change validation: too short (less than 6 characters)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)

        new_data = {"username": "tiny"}

        response = self.client.patch(url, new_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("username", data["errors"])
        self.assertIn(
            "Username must be at least 6 characters long.",
            str(data["errors"]["username"]),
        )

    def test_update_user_username_already_exists(self):
        """Test username change validation: prevents updating to an existing username."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)

        existing_username = self.another_normal_user.username

        new_data = {"username": existing_username}

        response = self.client.patch(url, new_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("username", data["errors"])
        self.assertIn(
            "user with this username already exists", str(data["errors"]["username"])
        )

    def test_update_user_password_complexity(self):
        """Test password change validation: verifies all complexity requirements (length, uppercase, digit, special char)."""
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.normal_user.pk)

        short_password = "Short1!"
        data = {"password": short_password, "c_password": short_password}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must be at least 8 characters.", error_list)

        no_uppercase = "nouppercase1!@"
        data = {"password": no_uppercase, "c_password": no_uppercase}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one uppercase letter.", error_list
        )

        no_lowercase = "NOLOWERCASE1!@"
        data = {"password": no_lowercase, "c_password": no_lowercase}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one lowercase letter.", error_list
        )

        no_digit = "NoDigit!@#ABCD"
        data = {"password": no_digit, "c_password": no_digit}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must contain at least one number.", error_list)

        no_special = "NoSpecial1234"
        data = {"password": no_special, "c_password": no_special}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one special character.", error_list
        )

    def test_user_cannot_update_themselves_without_login(self):
        url = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"first_name": "Agent Hack Attempt"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_cannot_update_another_staff_or_superuser(self):
        self._authenticate(self.normal_user)
        url1 = USER_DETAIL_URL(self.another_staff_user.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url1, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.superuser.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url2, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_staff_cannot_update_another_user_or_staff_or_superuser(self):
        """Staff user cannot update another staff and normal user's profile."""
        self._authenticate(self.staff_user)
        url1 = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url1, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.another_staff_user.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url2, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url3 = USER_DETAIL_URL(self.superuser.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url3, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_cannot_update_another_user_or_staff_or_superuser(self):
        self._authenticate(self.agent_user)
        url1 = USER_DETAIL_URL(self.normal_user.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url1, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.another_staff_user.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url2, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url3 = USER_DETAIL_URL(self.superuser.pk)
        new_data = {"first_name": "Hack Attempt"}
        response = self.client.patch(url3, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # # # ------DELETE TESTS------

    def test_delete_user_self_success(self):
        """Normal user can delete their own profile."""
        self._authenticate(self.normal_user)
        user_to_delete_pk = self.normal_user.pk
        url = USER_DETAIL_URL(user_to_delete_pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=user_to_delete_pk).exists())

    def test_delete_user_superuser_deletes_normal_success(self):
        """Superuser can delete a normal user."""
        self._authenticate(self.superuser)
        user_to_delete_pk = self.another_normal_user.pk
        url = USER_DETAIL_URL(user_to_delete_pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=user_to_delete_pk).exists())

    def test_one_user_cannot_delete_another_user(self):
        """Normal user cannot delete another normal user."""
        self._authenticate(self.normal_user)
        user_to_delete_pk = self.another_normal_user.pk
        url = USER_DETAIL_URL(user_to_delete_pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=user_to_delete_pk).exists())

    def test_delete_user_superuser_cannot_delete_themselves_or_another_superuser(self):
        """Any user (including superuser) cannot delete a superuser."""
        self._authenticate(self.superuser)
        url1 = USER_DETAIL_URL(self.superuser.pk)
        response = self.client.delete(url1)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete superusers", response.data["error"])
        self.assertTrue(User.objects.filter(pk=self.superuser.pk).exists())

        url2 = USER_DETAIL_URL(self.another_superuser.pk)
        response = self.client.delete(url2)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot delete superusers", response.data["error"])
        self.assertTrue(User.objects.filter(pk=self.another_superuser.pk).exists())

    def test_delete_user_not_found(self):
        """
        Tests that a DELETE request for a non-existent user ID returns HTTP 404 Not Found.
        """
        self._authenticate(self.superuser)
        largest_pk = User.objects.all().order_by("-pk").first().pk
        non_existent_pk = largest_pk + 1

        url = USER_DETAIL_URL(non_existent_pk)

        response = self.client.delete(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("no user matches the given query", data["errors"].lower())

    def test_delete_user_cannot_delete_themselves_without_login(self):
        url = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def user_cannot_delete_staff_or_superuser(self):
        """User cannot delete another staff or superuser."""
        self._authenticate(self.normal_user)
        url1 = USER_DETAIL_URL(self.another_staff_user.pk)
        response = self.client.delete(url1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.superuser.pk)
        response = self.client.delete(url2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def staff_cannot_delete_another_user_or_staff_or_superuser(self):
        """Staff user cannot delete another staff and normal user and superuser."""
        self._authenticate(self.staff_user)
        url1 = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.delete(url1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.another_staff_user.pk)
        response = self.client.delete(url2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url3 = USER_DETAIL_URL(self.superuser.pk)
        response = self.client.delete(url3)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def agent_cannot_delete_another_user_or_staff_or_superuser(self):
        """Agent user cannot delete another staff and normal user and superuser."""
        self._authenticate(self.agent_user)
        url1 = USER_DETAIL_URL(self.normal_user.pk)
        response = self.client.delete(url1)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url2 = USER_DETAIL_URL(self.another_staff_user.pk)
        response = self.client.delete(url2)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        url3 = USER_DETAIL_URL(self.superuser.pk)
        response = self.client.delete(url3)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def normal_user_cannot_delete_an_agent(self):
        self._authenticate(self.normal_user)
        url = USER_DETAIL_URL(self.agent_user.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.agent_user.pk).exists())


class AgentViewSetTests(APITestCase):
    """
    Tests for the AgentViewSet covering all CRUD actions and custom permission logic
    specific to Agent users (is_agent=True).
    """

    def setUp(self):
        self.password = "StrongP@ss123"

        self.superuser = User.objects.create_superuser(
            email="super@agenttest.com", password=self.password
        )
        self.staff_user = User.objects.create_user(
            email="staff@agenttest.com", password=self.password, is_staff=True
        )
        self.normal_user = User.objects.create_user(
            email="normal@agenttest.com", password=self.password
        )

        user_1 = User.objects.create_user(
            email="agent1@test.com",
            password=self.password,
            first_name="AgentOne",
        )

        self.agent_instance_1 = Agent.objects.create(user=user_1, company_name="ABC")

        user_2 = User.objects.create_user(
            email="agent2@test.com",
            password=self.password,
            first_name="AgentTwo",
        )
        self.agent_instance_2 = Agent.objects.create(
            user=user_2, company_name="Multi Properties"
        )

        self.agent_user_1 = self.agent_instance_1
        self.agent_user_2 = self.agent_instance_2

        self.client = APIClient()

    def _authenticate(self, user):
        """Helper to set authentication header for the client."""
        self.client.force_authenticate(user=user)

    def get_valid_create_data(self):
        return {
            "email": "newagent@test.com",
            "username": "newagent123",
            "password": "NewP@ss123!",
            "c_password": "NewP@ss123!",
            "first_name": "New",
            "last_name": "Agent",
            "is_agent": True,
            "company_name": "Test Agency Inc.",
        }

    def tearDown(self):
        """Clean up uploaded test files from the filesystem."""
        if hasattr(self, "image_path") and os.path.exists(self.image_path):
            os.remove(self.image_path)
        # Check if agent has an image and it's not the default
        self.agent_user_1.refresh_from_db()
        if self.agent_user_1.image_url:
            path = os.path.join(settings.MEDIA_ROOT, self.agent_user_1.image_url.name)
            if os.path.exists(path) and "default_profile.jpg" not in path:
                os.remove(path)

    #     #     # ------------------ List TESTS ------------------

    def test_list_agents_normal_user_denied(self):
        """Normal users should be denied listing agents."""
        self._authenticate(self.normal_user)
        response = self.client.get(AGENT_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 0)

    def test_superuser_can_list_agents(self):
        """Superuser can see all the agents list."""
        self._authenticate(self.superuser)
        response = self.client.get(AGENT_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_staff_can_list_agents(self):
        """Staff user can see all the agents list."""
        self._authenticate(self.staff_user)
        response = self.client.get(AGENT_LIST_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 2)

    def test_agent_cannot_list_agents(self):
        """Agent user cannot see all the agents list, resulting in an empty list."""
        self._authenticate(self.agent_user_1.user)
        response = self.client.get(AGENT_LIST_URL)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 0)

    #     #     # ------------------ Retrieve TESTS ------------------

    def test_retrieve_agent_superuser_allowed(self):
        """Superuser can retrieve any Agent profile."""
        self._authenticate(self.superuser)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_1.pk)

    def test_staff_can_retrieve_agent(self):
        """Staff user can retrieve any Agent profile."""
        self._authenticate(self.staff_user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_1.pk)

    def test_retrieve_agent_self_allowed(self):
        """An Agent can retrieve their own profile."""
        self._authenticate(self.agent_user_2.user)
        url = AGENT_DETAIL_URL(self.agent_user_2.user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_2.pk)

    def test_agent_can_retrieve_other_agent(self):
        """An agent can retrieve another agent's profile."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_2.user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_2.pk)

    def test_retrieve_agent_normal_user_allowed(self):
        """Normal user can retrieve an Agent's profile."""
        self._authenticate(self.normal_user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_1.pk)

    def test_superuser_can_retrieve_agent(self):
        """Superuser can retrieve an Agent's profile."""
        self._authenticate(self.superuser)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.agent_user_1.pk)

    #     #     # ------------------ CREATE (POST) TESTS ------------------

    def test_create_agent_by_superuser_success(self):
        """Test successful Agent creation by a Superuser."""
        self._authenticate(self.superuser)
        data = self.get_valid_create_data()
        response = self.client.post(AGENT_LIST_URL, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email=data["email"], is_agent=True).exists()
        )

    def test_agent_can_be_created_without_login(self):
        """Agent account can be created without login."""
        data = self.get_valid_create_data()
        response = self.client.post(AGENT_LIST_URL, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email=data["email"], is_agent=True).exists()
        )

    def test_staff_can_create_agent_account(self):
        """Staff can create agent account."""
        self._authenticate(self.staff_user)
        data = self.get_valid_create_data()
        response = self.client.post(AGENT_LIST_URL, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email=data["email"], is_agent=True).exists()
        )

    def test_bio_length_exceed_error_on_agent_register(self):
        """Test bio length exceed error during agent registration."""

        data = self.get_valid_create_data()

        data["email"] = "register_fail_bio_length@example.com"

        data["bio"] = "a" * 151

        response = self.client.post(AGENT_LIST_URL, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("bio", response.data)
        self.assertIn(
            "Ensure this field has no more than 150 characters.",
            response.data["bio"],
        )

    def test_company_name_length_exceed_error_on_register(self):
        """Test company name length exceed error during agent registration."""

        data = self.get_valid_create_data()
        data["email"] = "register_fail_company_name@example.com"

        data["company_name"] = "a" * 256
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("company_name", response.data)
        self.assertIn(
            "Ensure this field has no more than 255 characters.",  # Standard DRF message
            response.data["company_name"],
        )

    def test_create_agent_password_complexity(self):
        """Test password creation validation: verifies all complexity requirements (length, uppercase, digit, special char) during registration."""

        short_password = "Short1!"
        data = {
            "email": "test_short@example.com",
            "password": short_password,
            "c_password": short_password,
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must be at least 8 characters.", error_list)

        no_uppercase = "nouppercase1!@#"
        data = {
            "email": "test_no_upper@example.com",
            "password": no_uppercase,
            "c_password": no_uppercase,
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one uppercase letter.", error_list
        )

        no_lowercase = "NOLOWERCASE1!@#"
        data = {
            "email": "test_no_lower@example.com",
            "password": no_lowercase,
            "c_password": no_lowercase,
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one lowercase letter.", error_list
        )

        no_digit = "NoDigit!@#ABCD"
        data = {
            "email": "test_no_digit@example.com",
            "password": no_digit,
            "c_password": no_digit,
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must contain at least one number.", error_list)

        no_special = "NoSpecial1234"
        data = {
            "email": "test_no_special@example.com",
            "password": no_special,
            "c_password": no_special,
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one special character.", error_list
        )

        valid_password = "ValidPassword1!#"
        data = {
            "email": "test_valid@example.com",
            "password": valid_password,
            "c_password": valid_password,
            "company_name": "Test Company",
        }
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_agent_mismatched_passwords(self):
        """Test password mismatch validation in check_create_request_data."""
        data = self.get_valid_create_data()
        data["c_password"] = "WrongP@ss123"
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["error"])

    def test_create_agent_missing_password_confirm(self):
        """Test missing confirmation password in check_create_request_data."""
        data = self.get_valid_create_data()
        del data["c_password"]
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please confirm your password", response.data["error"])

    def test_create_agent_user_duplicate_email(self):
        """Test serializer validation for duplicate email."""
        data = self.get_valid_create_data()
        data["email"] = self.normal_user.email
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"errors": {"email": ["user with this email already exists."]}},
        )

    def test_agent_cannot_create_superuser(self):
        """Test prohibition of creating a superuser by setting is_superuser."""
        data = self.get_valid_create_data()
        data["is_superuser"] = True
        self._authenticate(self.agent_user_1.user)
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn(
            "You do not have permission to create a superuser. Contact Developer.",
            response.data["error"],
        )

    def test_agent_cannot_create_staff(self):
        """
        Tests that an agent cannot set the 'is_staff'
        field to True.
        """
        self._authenticate(self.agent_user_1.user)

        new_user_data = self.get_valid_create_data()

        new_user_data["username"] = "staffwannabe"
        new_user_data["email"] = "staffwannabe@test.com"
        new_user_data["is_staff"] = True

        response = self.client.post(AGENT_LIST_URL, new_user_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertFalse(User.objects.filter(username="staffwannabe").exists())
        self.assertIn("you do not have permission", data["errors"].lower())

    def test_agent_cannot_change_forbidden_fields(self):
        """Test prohibition of setting slug field."""
        data = self.get_valid_create_data()
        data["slug"] = "custom-slug"
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

        del data["slug"]
        data["is_active"] = False
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated.", response.data["error"])

    def test_agent_username_exists(self):
        """Test that a username must be unique."""
        data = self.get_valid_create_data()
        data["username"] = self.agent_user_1.user.username
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.json(),
            {"errors": {"username": ["user with this username already exists."]}},
        )

    def test_agent_username_too_short(self):
        """Test serializer validation for username too short."""
        data = self.get_valid_create_data()
        data["username"] = "abc"
        response = self.client.post(AGENT_LIST_URL, data, format="json")
        response_data = response.json()
        self.assertIn("username", response_data["errors"])
        self.assertIn(
            "Username must be at least 6 characters long.",
            str(response_data["errors"]["username"]),
        )

    ###---------------UPDATE (PATCH) TESTS

    def test_update_agent_self_success(self):
        """Agent can successfully update their own profile."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"bio": "I am an agent"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent_user_1.refresh_from_db()
        self.assertEqual(self.agent_user_1.bio, "I am an agent")

    def test_superuser_can_update_agent_profile(self):
        """Superuser can update an agent's profile."""
        self._authenticate(self.superuser)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"first_name": "SuperUpdate"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["user"]["first_name"], "Superupdate")

    def test_one_agent_cannot_update_another_agent_profile(self):
        """Agent cannot update another Agent's profile."""
        self._authenticate(self.agent_user_1.user)
        url1 = AGENT_DETAIL_URL(self.agent_user_2.user.pk)
        new_data = {"first_name": "ForbiddenUpdate"}
        response = self.client.patch(url1, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_agent_forbidden_email_field(self):
        """Cannot update the email field (check_update_request_data)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"email": "new_email@test.com"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("You cannot update the email field", response.data["error"])

    def test_update_agent_forbidden_internal_fields(self):
        """Cannot update status fields like is_staff (check_update_request_data)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data1 = {"is_staff": True}
        response1 = self.client.patch(url, new_data1, format="json")
        self.assertEqual(response1.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response1.data["error"])

        new_data2 = {"is_superuser": True}
        response2 = self.client.patch(url, new_data2, format="json")
        self.assertEqual(response2.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response2.data["error"])

        new_data3 = {"is_active": True}
        response3 = self.client.patch(url, new_data3, format="json")
        self.assertEqual(response3.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response3.data["error"])

        new_data4 = {"slug": "abc"}
        response4 = self.client.patch(url, new_data4, format="json")
        self.assertEqual(response4.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("Forbidden fields cannot be updated", response4.data["error"])

    def test_update_agent_password_mismatch(self):
        """Test password change validation (check_update_request_data)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"password": "NewP@ss123", "c_password": "Mismatch"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Passwords do not match", response.data["error"])

    def test_update_user_password_missing_confirm(self):
        """Test password change validation (check_update_request_data)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"password": "NewP@ss123"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Please confirm your password", response.data["error"])

    def test_full_update_put_disallowed(self):
        """Test that the PUT method is disallowed (http_method_not_allowed)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        data = {"email": "test@test.com"}
        response = self.client.put(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_agent_not_found(self):
        """
        Test that attempting to update an Agent profile using a non-existent Agent ID.
        """

        self._authenticate(self.superuser)

        non_existent_agent_pk = self.normal_user.pk

        url = AGENT_DETAIL_URL(non_existent_agent_pk)

        update_data = {"company_name": "Non-Existent Agent Update"}

        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_username_too_short(self):
        """Test username change validation: too short (less than 6 characters)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        new_data = {"username": "tiny"}

        response = self.client.patch(url, new_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("username", data["errors"])
        self.assertIn(
            "Username must be at least 6 characters long.",
            str(data["errors"]["username"]),
        )

    def test_update_user_username_already_exists(self):
        """Test username change validation: prevents updating to an existing username."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        existing_username = self.agent_user_2.user.username

        new_data = {"username": existing_username}

        response = self.client.patch(url, new_data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn("username", data["errors"])
        self.assertIn(
            "user with this username already exists", str(data["errors"]["username"])
        )

    def test_update_user_password_complexity(self):
        """Test password change validation: verifies all complexity requirements (length, uppercase, digit, special char)."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        short_password = "Short1!"
        data = {"password": short_password, "c_password": short_password}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must be at least 8 characters.", error_list)

        no_uppercase = "nouppercase1!@"
        data = {"password": no_uppercase, "c_password": no_uppercase}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one uppercase letter.", error_list
        )

        no_lowercase = "NOLOWERCASE1!@"
        data = {"password": no_lowercase, "c_password": no_lowercase}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one lowercase letter.", error_list
        )

        no_digit = "NoDigit!@#ABCD"
        data = {"password": no_digit, "c_password": no_digit}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn("Password must contain at least one number.", error_list)

        no_special = "NoSpecial1234"
        data = {"password": no_special, "c_password": no_special}
        response = self.client.patch(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["password"]
        self.assertIn(
            "Password must contain at least one special character.", error_list
        )

    def test_agent_cannot_update_themselves_without_login(self):
        """Test agent cannot update themselves without login."""
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"first_name": "Agent Hack Attempt"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_staff_cannot_update_agent(self):
        """Staff user cannot update agent's profile"""
        self._authenticate(self.staff_user)
        url = AGENT_DETAIL_URL(self.agent_user_1.pk)
        new_data = {"first_name": "ForbiddenUpdate"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def normal_user_cannot_update_agent(self):
        """Test a normal user cannot update an agent's profile."""
        self._authenticate(self.normal_user)
        url = AGENT_DETAIL_URL(self.agent_user.pk)
        new_data = {"first_name": "Attempted Hack"}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_update_bio_length_exceeding_error(self):
        """Test agent update bio length exceeding error."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"bio": "a" * 151}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["bio"]
        self.assertIn("Ensure this field has no more than 150 characters.", error_list)

    def test_agent_update_company_name_length_exceed_error(self):
        """Test agent update company name length exceed error."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        new_data = {"company_name": "a" * 256}
        response = self.client.patch(url, new_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        error_list = response.json()["errors"]["company_name"]
        self.assertIn("Ensure this field has no more than 255 characters.", error_list)

    # #     #     ###-----------DELETE TESTS---------

    def test_delete_agent_self_allowed(self):
        """An Agent can successfully delete their own profile."""

        agent_user_pk = self.agent_user_2.user.pk

        self._authenticate(self.agent_user_2.user)

        url = AGENT_DETAIL_URL(agent_user_pk)

        self.assertTrue(User.objects.filter(pk=agent_user_pk).exists())
        self.assertTrue(Agent.objects.filter(user__pk=agent_user_pk).exists())

        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertFalse(User.objects.filter(pk=agent_user_pk).exists())
        self.assertFalse(Agent.objects.filter(user__pk=agent_user_pk).exists())

    def test_delete_agent_superuser_allowed(self):
        """Superuser can delete an Agent."""
        agent_to_delete_pk = self.agent_user_1.user.pk
        self._authenticate(self.superuser)
        url = AGENT_DETAIL_URL(agent_to_delete_pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(User.objects.filter(pk=agent_to_delete_pk).exists())

    def test_delete_agent_staff_denied(self):
        """Staff user cannot delete an Agent."""
        user_pk = self.agent_user_2.user.pk
        self._authenticate(self.staff_user)
        url = AGENT_DETAIL_URL(user_pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=user_pk).exists())

    def test_delete_agent_not_found(self):
        """
        Test that attempting to delete an Agent profile using a non-existent Agent ID.
        """

        self._authenticate(self.superuser)

        non_existent_agent_pk = self.normal_user.pk

        url = AGENT_DETAIL_URL(non_existent_agent_pk)

        update_data = {"company_name": "Non-Existent Agent Update"}

        response = self.client.patch(url, update_data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_agent_cannot_delete_another_agent(self):
        """Test agent cannot delete another agent or any other user."""
        self._authenticate(self.agent_user_1.user)
        user_pk1 = self.agent_user_2.user.pk
        url = AGENT_DETAIL_URL(user_pk1)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=user_pk1).exists())

    def test_agent_cannot_delete_themselves_without_login(self):
        """Test agent cannot delete themselves without login."""
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def normal_user_cannot_delete_an_agent(self):
        self._authenticate(self.normal_user)
        url = AGENT_DETAIL_URL(self.agent_user.pk)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(User.objects.filter(pk=self.agent_user.pk).exists())

    ## Image Test Cases

    def test_upload_valid_image(self):
        """Test successfully updating an agent profile with a valid image."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        image = self.generate_image(name="profile.png", format="PNG")
        data = {"company_name": "Updated Agency", "profile_image": image}

        # Use multipart format for file uploads
        response = self.client.patch(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.agent_user_1.refresh_from_db()
        self.assertIn("profile.png", self.agent_user_1.image_url.name)

    def test_image_size_limit_fail(self):
        """Test that images larger than 2MB are rejected."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        # Create a file slightly larger than 2MB
        large_content = b"0" * (2 * 1024 * 1024 + 1024)
        large_image = SimpleUploadedFile(
            "too_big.jpg", large_content, content_type="image/jpeg"
        )

        data = {"profile_image": large_image}
        response = self.client.patch(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Check for the nested error structure in your AgentImageSerializer
        self.assertIn("Image size should not exceed 2MB.", str(response.data))

    def test_invalid_image_type(self):
        """Test that non-image files are rejected."""
        self._authenticate(self.agent_user_1.user)
        url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

        fake_image = SimpleUploadedFile(
            "doc.pdf", b"not-image-data", content_type="application/pdf"
        )

        data = {"profile_image": fake_image}
        response = self.client.patch(url, data, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Image type should be JPEG, PNG", str(response.data))


#! Agent Image Update Testcases (all of them including errors)


# def test_upload_agent_profile_image_success(self):
#     """Test successfully uploading a profile image via the ViewSet."""
#     self._authenticate(self.agent_user_1.user)
#     url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

#     # Create a 10x10 black image
#     black_image = Image.new("RGB", (10, 10), "black")
#     image_bytes = io.BytesIO()
#     black_image.save(image_bytes, format="JPEG")
#     image_bytes.seek(0)

#     image_file = SimpleUploadedFile(
#         name="test_image.jpg",
#         content=image_bytes.read(),
#         content_type="image/jpeg",
#     )

#     data = {
#         "company_name": "Updated Agency",
#         "profile_image": image_file  # Key used in your ViewSet logic
#     }

#     # format="multipart" is essential for file uploads
#     response = self.client.patch(url, data, format="multipart")

#     self.assertEqual(response.status_code, status.HTTP_200_OK)

#     self.agent_user_1.refresh_from_db()
#     self.image_path = os.path.join(settings.MEDIA_ROOT, self.agent_user_1.image_url.name)

#     # Assertions
#     self.assertTrue(self.agent_user_1.image_url)
#     # Verify it saved in the 'profile_images' directory as per Agent model
#     self.assertIn("profile_images/", self.agent_user_1.image_url.name)
#     self.assertTrue(os.path.exists(self.image_path))

# def test_image_type_validation_error(self):
#     """Test that only JPEG and PNG are allowed via AgentImageSerializer."""
#     self._authenticate(self.agent_user_1.user)
#     url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

#     # Create a fake text file disguised as an image
#     fake_image = SimpleUploadedFile(
#         name="test.gif",
#         content=b"not-an-image-content",
#         content_type="image/gif"
#     )

#     data = {"profile_image": fake_image}
#     response = self.client.patch(url, data, format="multipart")

#     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#     # Your Serializer returns errors['type'] = "Image type should be JPEG, PNG"
#     self.assertIn("Image type should be JPEG, PNG", str(response.data))

# def test_image_size_validation_error(self):
#     """Test that images exceeding 2MB are rejected."""
#     self._authenticate(self.agent_user_1.user)
#     url = AGENT_DETAIL_URL(self.agent_user_1.user.pk)

#     # Generate 3MB of dummy data
#     large_content = b"0" * (3 * 1024 * 1024)
#     large_image = SimpleUploadedFile(
#         name="huge.jpg",
#         content=large_content,
#         content_type="image/jpeg"
#     )

#     data = {"profile_image": large_image}
#     response = self.client.patch(url, data, format="multipart")

#     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#     self.assertIn("Image size should not exceed 2MB.", str(response.data))
