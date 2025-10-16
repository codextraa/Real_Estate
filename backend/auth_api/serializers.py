from django.contrib.auth import get_user_model
from rest_framework import serializers
from backend.validators import validate_password_complexity
from core_db.models import User, Agent


class UserSerializer(serializers.ModelSerializer):
    """User serializer for user model."""

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "is_superuser",
            "is_active",
            "is_staff",
            "is_agent",
            "password",
            "slug",
        ]

        read_only_fields = [
            "id",
            "is_superuser",
            "slug",
        ]

        extra_kwargs = {
            "password": {"write_only": True, "style": {"input_type": "password"}}
        }

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)

    def validate(self, attrs):
        """Validate all data"""
        password = attrs.get("password")

        if password:
            errors = validate_password_complexity(attrs.get("password"))
            if len(errors["password"]) > 0:
                raise serializers.ValidationError(errors)

        username = attrs.get("username")
        if username:
            if len(username) < 6:
                raise serializers.ValidationError(
                    {"username": "Username must be at least 6 characters long."}
                )

        attrs = super().validate(attrs)

        first_name = attrs.get("first_name")
        last_name = attrs.get("last_name")

        if first_name:
            attrs["first_name"] = attrs["first_name"].title()

        if last_name:
            attrs["last_name"] = attrs["last_name"].title()

        return attrs


class UserListSerializer(serializers.ModelSerializer):
    """List user serializer."""

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "username",
            "is_active",
            "is_agent",
            "is_staff",
            "is_superuser",
            "slug",
        ]

        read_only_fields = fields


class UserRetrieveSerializer(serializers.ModelSerializer):
    """Get user by id serializer."""

    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "slug",
        ]

        read_only_fields = fields


class AgentSerializer(serializers.ModelSerializer):
    """Agent serializer for agent model."""

    class Meta:
        model = Agent
        fields = [
            "id",
            "user",
            "company_name",
            "bio",
            "image_url",
        ]

        read_only_fields = [
            "id",
            "image_url",
        ]

    def create(self, validated_data):
        image_url = validated_data.pop("image_url", None)

        if not image_url:
            default_image_path = "profile_images/default_profile.jpg"
            validated_data["profile_img"] = default_image_path

        return Agent.objects.create(**validated_data)

    def validate(self, attrs):
        """Validate all data"""

        attrs = super().validate(attrs)

        company_name = attrs.get("company_name")

        if company_name:
            attrs["company_name"] = attrs["company_name"].title()
        else:
            attrs["company_name"] = None

        return attrs


class AgentImageSerializer(serializers.ModelSerializer):
    """Agent image serializer for agent model."""

    class Meta:
        model = Agent
        fields = ["id", "image_url"]
        read_only_fields = ["id"]

    def validate_image_url(self, value):
        """Validate image"""
        if not value:
            raise serializers.ValidationError("Image is required.")

        errors = {}
        max_size = 2 * 1024 * 1024  # 2MB
        valid_file_types = ["image/jpeg", "image/png"]  # valid image types

        if value.size > max_size:
            errors["size"] = "Image size should not exceed 2MB."

        if (
            hasattr(value, "content_type")
            and value.content_type not in valid_file_types
        ):
            errors["type"] = "Image type should be JPEG, PNG"

        if errors:
            raise serializers.ValidationError(errors)

        return value


class AgentListSerializer(serializers.ModelSerializer):
    """List agent serializer."""

    user = UserListSerializer(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "user",
            "company_name",
        ]

        read_only_fields = fields


class AgentRetrieveSerializer(serializers.ModelSerializer):
    """Get agent by id serializer."""

    user = UserRetrieveSerializer(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "user",
            "company_name",
            "bio",
            "image_url",
        ]

        read_only_fields = fields
