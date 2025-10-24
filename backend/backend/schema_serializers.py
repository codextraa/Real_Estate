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


class UserCreateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the expected fields for user creation (POST request body).
    """

    email = serializers.EmailField(
        required=True, help_text="User's unique email address."
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    c_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    username = serializers.CharField(
        required=False, help_text="Mandatory unique username."
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    is_staff = serializers.BooleanField(
        required=False,
        default=False,
        help_text="Designates whether the user is a staff member.",
    )


class UserUpdateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the fields accepted for user profile updates (PATCH request body).
    All fields are optional for partial updates.
    """

    password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="New password (optional). Must meet complexity requirements if provided.",
    )
    c_password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    username = serializers.CharField(required=False, help_text="New unique username.")
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)


class PropertyCreateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the expected fields for property creation (POST request body).
    """

    title = serializers.CharField(
        required=True, max_length=255, help_text="The title of the property."
    )
    description = serializers.CharField(
        required=True, help_text="Detailed description of the property."
    )
    price = serializers.DecimalField(
        required=True,
        max_digits=10,
        decimal_places=2,
        help_text="The price of the property.",
    )
    property_type = serializers.CharField(
        required=True, help_text="e.g., House, Apartment, Land."
    )
    location = serializers.CharField(
        required=True, help_text="The location or city of the property."
    )
    bedrooms = serializers.IntegerField(
        required=False, min_value=0, help_text="Number of bedrooms."
    )
    bathrooms = serializers.IntegerField(
        required=False, min_value=0, help_text="Number of bathrooms."
    )
    area_sqft = serializers.IntegerField(
        required=False, min_value=0, help_text="Area in square feet."
    )

    # Representing the file upload for schema documentation
    property_image = serializers.FileField(
        required=False,
        write_only=True,
        help_text="The main image file for the property.",
        style={"type": "file"},
    )


class PropertyUpdateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the optional fields for property updates (PATCH request body).
    All fields are optional for partial updates.
    """

    title = serializers.CharField(
        required=False, max_length=255, help_text="The title of the property."
    )
    description = serializers.CharField(
        required=False, help_text="Detailed description of the property."
    )
    price = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        help_text="The price of the property.",
    )
    property_type = serializers.CharField(
        required=False, help_text="e.g., House, Apartment, Land."
    )
    location = serializers.CharField(
        required=False, help_text="The location or city of the property."
    )
    bedrooms = serializers.IntegerField(
        required=False, min_value=0, help_text="Number of bedrooms."
    )
    bathrooms = serializers.IntegerField(
        required=False, min_value=0, help_text="Number of bathrooms."
    )
    area_sqft = serializers.IntegerField(
        required=False, min_value=0, help_text="Area in square feet."
    )
    is_available = serializers.BooleanField(
        required=False, help_text="Availability status."
    )

    property_image = serializers.FileField(
        required=False,
        write_only=True,
        help_text="A new main image file for the property.",
        style={"type": "file"},
    )


class AgentCreateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the expected fields for creating a new Agent account.
    Combines User creation fields with Agent specific fields.
    """

    email = serializers.EmailField(
        required=True, help_text="User's unique email address."
    )
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    c_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    username = serializers.CharField(
        required=True, help_text="Mandatory unique username."
    )
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    company_name = serializers.CharField(
        required=True,
        max_length=255,
        help_text="The company/agency name the agent represents.",
    )


class AgentUpdateRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """
    Serializer defining the optional fields for updating an Agent profile.
    Combines User update fields with Agent specific fields.
    All fields are optional for partial updates (PATCH).
    """

    password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="New password (optional). Must meet complexity requirements if provided.",
    )
    c_password = serializers.CharField(
        required=False,
        write_only=True,
        style={"input_type": "password"},
        help_text="Mandatory password, must meet complexity requirements.",
    )
    username = serializers.CharField(required=False, help_text="New unique username.")
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    company_name = serializers.CharField(
        required=False,
        max_length=255,
        help_text="The company/agency name the agent represents.",
    )
    bio = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="A short biography/about section (max 150 chars).",
    )
    profile_image = serializers.FileField(
        required=False,
        write_only=True,
        help_text="A new profile image file for the agent (e.g., JPEG, PNG, max 2MB).",
        style={"type": "file"},
    )
