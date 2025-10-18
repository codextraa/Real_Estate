from rest_framework import serializers


class LoginRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class LogoutRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    refresh = serializers.CharField(required=True)


class RefreshTokenRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    refresh = serializers.CharField(required=True)


class LoginResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Custom response structure for successful login (HTTP 200)."""

    access_token = serializers.CharField(
        help_text="The new access token for subsequent authenticated API requests."
    )
    refresh_token = serializers.CharField(
        help_text="The refresh token used to obtain a new access token without re-logging."
    )
    user_id = serializers.IntegerField(
        help_text="The ID of the authenticated user (used as the 'user_id' claim in the JWT)."
    )
    user_role = serializers.ChoiceField(
        choices=["Default", "Agent", "Admin", "Superuser", "UnAuthorized"],
        help_text="The resolved primary role/group of the authenticated user.",
    )
    access_token_expiry = serializers.DateTimeField(
        help_text="The exact time when the access token will expire (ISO format)."
    )


class ErrorResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Standard error response structure (HTTP 400, 429, 500)."""

    error = serializers.CharField(
        help_text="A descriptive error message explaining the failure or status."
    )


class UserCreateRequestSerializer(serializers.Serializer):
    """
    Serializer defining the expected fields for user creation (POST request body).
    """
    email = serializers.EmailField(required=True, help_text="User's unique email address.")
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements."
    )
    username = serializers.CharField(required=True, help_text="Mandatory unique username.")
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)


class UserUpdateRequestSerializer(serializers.Serializer):
    """
    Serializer defining the fields accepted for user profile updates (PATCH request body).
    All fields are optional for partial updates.
    """
    email = serializers.EmailField(required=False, help_text="New unique email address.")
    password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="New password (optional). Must meet complexity requirements if provided."
    )
    username = serializers.CharField(required=False, help_text="New unique username.")
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    is_active = serializers.BooleanField(required=False, help_text="User account status (Admin/Superuser only).")
    is_staff = serializers.BooleanField(required=False, help_text="Designates if user can log into this admin site (Superuser only).")
    is_agent = serializers.BooleanField(required=False, help_text="Designates if the user is an agent (Superuser only).")
