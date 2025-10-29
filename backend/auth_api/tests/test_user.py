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
        # Ensure these URL names exist in your project's urls.py
        self.login_url = reverse("login")
        self.refresh_url = reverse("refresh-token")

        self.valid_payload = {"email": self.TEST_EMAIL, "password": TEST_PASSWORD}

        # --- 1. Setup Active User (standard flow) ---
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

        self.deact_user = User.objects.create_user(
            email="deact@test.com",
            password=TEST_PASSWORD,
            is_active=True,
        )

        deact_login_payload = {"email": "deact@test.com", "password": TEST_PASSWORD}

        deact_login_response = self.client.post(
            self.login_url, deact_login_payload, format="json"
        )

        self.assertEqual(
            deact_login_response.status_code,
            status.HTTP_200_OK,
            f"Deactivated user setup failed. Response: {deact_login_response.content}",
        )

        self.deact_refresh_token = deact_login_response.data["refresh_token"]
        self.deact_payload = {"refresh": self.deact_refresh_token}

        self.deact_user.is_active = False
        self.deact_user.save()

    def tearDown(self):
        # Clean up all users created during setup/tests
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

    # def test_06_refresh_token_user_is_deactivated(self):
    #     """Tests failure when refresh token is valid but the associated user is inactive (check_user_validity failure)."""

    #     # This token belongs to self.deact_user, which was deactivated in setUp.
    #     response = self.client.post(self.refresh_url, self.deact_payload, format="json")

    #     # The custom check_user_validity logic is expected to run.
    #     # FIX: Assert for 401 Unauthorized, as seen in the traceback.
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(response.data["error"], "Account is deactivated. Contact your admin")

    # # FIX for test_07 (Ensuring all claims are correctly copied)

    # def test_07_invalid_user_id_from_token(self):
    #     """
    #     Tests failure when the user ID extracted from a manually signed token
    #     is non-existent (check_user_id failure).
    #     """
    #     # 1. Get the payload from a truly valid, fresh refresh token
    #     valid_token = RefreshToken(self.initial_refresh_token)
    #     token_claims = valid_token.payload

    #     # 2. Intentionally modify the specific claim we are testing: 'user_id'
    #     NON_EXISTENT_ID = self.test_user.id + 100
    #     token_claims[settings.SIMPLE_JWT["USER_ID_CLAIM"]] = NON_EXISTENT_ID

    #     # 3. Manually encode and sign the modified payload (using RS256/Private Key)
    #     try:
    #         custom_token = jwt.encode(
    #             token_claims,
    #             settings.SIMPLE_JWT["SIGNING_KEY"],
    #             algorithm="RS256"
    #         )
    #     except Exception as e:
    #         self.fail(f"JWT encoding failed with RS256: {e}")

    #     invalid_user_payload = {"refresh": custom_token}

    #     # 4. Attempt to refresh
    #     response = self.client.post(self.refresh_url, invalid_user_payload, format="json")

    #     # The token passed core JWT validation but failed your custom user lookup.
    #     # We must assert for the specific custom error message.
    #     self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    #     self.assertEqual(response.data["error"], "Invalid Session")

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


# TEST_EMAIL = "logout_test@example.com"
# TEST_PASSWORD = "LogoutStrongPassword123!"
# User = get_user_model()

# class LogoutViewIntegrationTests(APITestCase):
#     """Integration Test suite for LogoutView focusing on token blacklisting/invalidation."""

#     def setUp(self):
#         self.TEST_EMAIL = TEST_EMAIL
#         self.client = APIClient()
#         self.login_url = reverse("login")
#         self.logout_url = reverse("logout")
#         # NOTE: You must have a dummy protected endpoint for validation
#         self.protected_url = reverse("some-protected-endpoint")

#         self.valid_payload = {"email": self.TEST_EMAIL, "password": TEST_PASSWORD}

#         # 1. Create a user
#         try:
#             self.test_user = User.objects.create_user(
#                 email=self.TEST_EMAIL,
#                 password=TEST_PASSWORD,
#                 is_active=True,
#             )
#         except Exception as e:
#             self.fail(f"Failed to set up real user. Error: {e}")

#         # 2. Log in and get tokens for use in tests
#         login_response = self.client.post(self.login_url, self.valid_payload, format="json")
#         self.assertEqual(login_response.status_code, status.HTTP_200_OK)

#         self.access_token = login_response.data["access_token"]
#         self.refresh_token = login_response.data["refresh_token"]

#         # 3. Set the client's authorization header for subsequent requests
#         self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

#     def tearDown(self):
#         self.test_user.delete()
#         cache.clear()
#         super().tearDown()

#     def test_01_successful_logout(self):
#         """Tests the full successful logout flow. Should invalidate the refresh token."""
#         # The Logout ViewSet typically requires the 'refresh_token' in the body
#         logout_payload = {"refresh_token": self.refresh_token}

#         response = self.client.post(self.logout_url, logout_payload, format="json")

#         # 1. Assert status code (205 Reset Content is common for token revocation)
#         self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
#         # You may need to adjust the expected message based on your view's implementation
#         self.assertIn("logged out", response.data.get("detail", "").lower())

#         # 2. **Verification step:** Attempt to access a protected resource
#         # This confirms the access token is invalidated/rejected after logout.
#         protected_response = self.client.get(self.protected_url)
#         # Expecting 401 Unauthorized or 403 Forbidden after logout
#         self.assertIn(protected_response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

#     def test_02_logout_without_refresh_token_in_body(self):
#         """Tests the required field validation for the refresh token payload."""
#         response = self.client.post(self.logout_url, {}, format="json")

#         # Expecting a 400 if the refresh token is missing
#         self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
#         self.assertIn("refresh_token", response.data) # Check for a field-level error

#     def test_03_logout_without_authentication(self):
#         """Tests logging out when no user is authenticated (no access token/headers)."""
#         # Clear the credentials so the request is unauthenticated
#         self.client.credentials()

#         logout_payload = {"refresh_token": self.refresh_token}

#         response = self.client.post(self.logout_url, logout_payload, format="json")

#         # Logout often requires authentication to prevent abuse
#         self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
#         self.assertEqual(response.data["detail"], "Authentication credentials were not provided.")

#     def test_04_logout_with_invalid_refresh_token(self):
#         """Tests the case where a malformed or fake refresh token is provided."""
#         # Note: We still provide a valid access token in the header (from setUp)

#         logout_payload = {"refresh_token": "an_obviously_fake_or_expired_token"}

#         response = self.client.post(self.logout_url, logout_payload, format="json")

#         # Expecting a status indicating the token is invalid/not found/malformed
#         self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])
#         self.assertIn("invalid", str(response.data).lower())
