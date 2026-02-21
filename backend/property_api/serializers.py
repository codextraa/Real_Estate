from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from core_db.models import Agent, Property
from backend.validators import validate_property_integers


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

        beds = attrs.get("beds")
        baths = attrs.get("baths")
        area_sqft = attrs.get("area_sqft")

        errors = validate_property_integers(beds, baths, area_sqft)
        if errors:
            raise serializers.ValidationError(errors)

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
        valid_file_types = ["image/jpeg", "image/jpg", "image/png"]  # valid image types

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

    @extend_schema_field(serializers.CharField)
    def get_user_role(self, obj):  # pylint: disable=W0613
        return "Agent"

    user_id = serializers.IntegerField(source="user.id", read_only=True)
    first_name = serializers.CharField(source="user.first_name", read_only=True)
    last_name = serializers.CharField(source="user.last_name", read_only=True)
    slug = serializers.CharField(source="user.slug", read_only=True)
    user_role = serializers.SerializerMethodField()
    image_url = serializers.ImageField(read_only=True)

    class Meta:
        model = Agent
        fields = [
            "id",
            "user_id",
            "first_name",
            "last_name",
            "user_role",
            "image_url",
            "slug",
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
