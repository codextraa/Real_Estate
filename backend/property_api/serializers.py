from rest_framework import serializers
from core_db.models import Agent, Property


class PropertySerializer(serializers.ModelSerializer):
    """Property serializer for property model."""

    class Meta:
        model = Property
        fields = [
            "id",
            "agent",
            "title",
            "description",
            "beds",
            "baths",
            "price",
            "area_sqft",
            "address",
            "slug",
            "image_url",
        ]

        read_only_fields = [
            "id",
            "image_url",
            "slug",
        ]

    def validate(self, attrs):
        """Validate all data"""

        attrs = super().validate(attrs)

        title = attrs.get("title")

        if title:
            attrs["title"] = attrs["title"].title()

        return attrs


class PropertyImageSerializer(serializers.ModelSerializer):
    """Property image serializer for property model."""

    class Meta:
        model = Property
        fields = ["id", "image_url"]
        read_only_fields = ["id"]

    def validate_image_url(self, value):
        """Validate property image"""
        if not value:
            raise serializers.ValidationError("Property image is required.")

        errors = {}
        max_size = 2 * 1024 * 1024  # 2MB
        valid_file_types = ["image/jpeg", "image/png"]  # valid image types

        if value.size > max_size:
            errors["size"] = "Property image size should not exceed 2MB."

        if (
            hasattr(value, "content_type")
            and value.content_type not in valid_file_types
        ):
            errors["type"] = "Property image type should be JPEG, PNG"

        if errors:
            raise serializers.ValidationError(errors)

        return value


class PropertyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = [
            "id",
            "slug",
            "title",
            "image_url",
            "description",
        ]

        read_only_fields = fields


class PropertyAgentRetrieveSerializer(serializers.ModelSerializer):
    """
    Serializer to retrieve the specific agent details needed for property view.
    Includes profile image, first_name, and last_name.
    """

    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    image_url = serializers.ImageField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "first_name",
            "last_name",
            "image_url",
        ]
        read_only_fields = fields


class PropertyRetrieveSerializer(serializers.ModelSerializer):
    """Get property by id serializer."""

    agent = PropertyAgentRetrieveSerializer(read_only=True)

    class Meta:
        model = Property
        fields = [
            "id",
            "agent",
            "title",
            "description",
            "beds",
            "baths",
            "price",
            "area_sqft",
            "address",
            "slug",
            "image_url",
        ]

        read_only_fields = fields
