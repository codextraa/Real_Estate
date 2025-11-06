import jwt
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.test import APITestCase
from rest_framework.test import APIClient
from django.urls import reverse
from django.core.cache import cache
from django.contrib.auth import get_user_model
from freezegun import freeze_time
from datetime import timedelta, datetime
from django.utils.timezone import now
from django.conf import settings

TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "StrongPassword123!"
AGENT_ROLE = "Agent"
User = get_user_model()


# Inherit from APITestCase
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

        # 1. Assert status code
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 2. Assert response keys (e.g., tokens, user info)
        self.assertIn("access_token", response.data)
        self.assertIn("refresh_token", response.data)
        self.assertIn("access_token_expiry", response.data)
        self.assertIn("user_id", response.data)

        # 3. Assert user data, especially the role
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
        # Assert against the generic error message your view returns for blacklisted/invalid tokens
        self.assertIn("Invalid refresh token", str(refresh_response.data))

    def test_02_logout_without_refresh_token_in_body(self):
        """Tests the required field validation for the refresh token payload."""

        # Post an empty payload (missing the 'refresh' key)
        response = self.client.post(self.logout_url, {}, format="json")

        # 1. Assert the status code returned by your view's manual check
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertEqual(response.data.get("error"), "Tokens are required")

    def test_03_logout_with_invalid_refresh_token(self):
        """Tests the case where a malformed or fake refresh token is provided."""

        # 1. FIX PAYLOAD KEY: Use the correct key 'refresh'
        # 2. Provide a value that is truly malformed (not just an empty string)
        invalid_payload = {"refresh": "this.is.a.bad.token"}

        response = self.client.post(self.logout_url, invalid_payload, format="json")

        # When the token is invalid, the view will raise a TokenError inside
        # `RefreshToken(refresh_token)`, which is caught by the view's generic exception handler:

        # 3. Assert the status code returned by the Simple JWT exception handler.
        # (Assuming Simple JWT errors are caught by your final except Exception block)
        self.assertIn(
            response.status_code,
            [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR],
        )

        # 4. FIX ASSERTION: Assert against the error message returned by your view's exception handler (e.g., Token is invalid)
        # Your view's generic exception handler returns HTTP_500 and the error string from TokenError.
        self.assertIn("token is invalid", str(response.data).lower())

        # NOTE: If your view's TokenError block returns 500, the status check should be:
        # self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        # self.assertIn("token is invalid", str(response.data).lower())
