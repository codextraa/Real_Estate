import re
from rest_framework import serializers
from core_db.models import User, Agent
from django.contrib.auth import get_user_model


def validate_password(password):
    """Password Validation"""
    errors = {}

    if len(password) < 8:
        errors["short"] = "Password must be at least 8 characters long."

    if not re.search(r"[a-z]", password):
        errors["lower"] = "Password must contain at least one lowercase letter."

    if not re.search(r"[A-Z]", password):
        errors["upper"] = "Password must contain at least one uppercase letter."

    if not re.search(r"[0-9]", password):
        errors["number"] = "Password must contain at least one number."

    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors["special"] = "Password must contain at least one special character."

    return errors


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "address",
            "is_superuser",
            "is_active",
            "is_staff",
            "is_agent",
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

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def validate(self, attrs):
        """Validate all data"""
        password = attrs.get("password")

        if password:
            errors = validate_password(password)
            if errors:
                raise serializers.ValidationError({"password": errors})

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
        else:
            attrs["first_name"] = None

        if last_name:
            attrs["last_name"] = attrs["last_name"].title()
        else:
            attrs["last_name"] = None

        return attrs


class AgentSerializer(serializers.ModelSerializer):
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
        ]

    def create(self, validated_data):
        image_url = validated_data.pop("image_url", None)

        if not image_url:
            default_image_path = "profile_images/default_profile.jpg"
            validated_data["profile_img"] = default_image_path

        return Agent.objects.create(**validated_data)

    def update(self, instance, validated_data):
        return super().update(instance, validated_data)

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
    class Meta:
        model = Agent
        fields = ("id", "image_url")
        read_only_fields = ("id",)

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
