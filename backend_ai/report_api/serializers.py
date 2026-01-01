from rest_framework import serializers
from core_db_ai.models import User, Property, AIReport


class AIReportSerializer(serializers.ModelSerializer):
    """AI Report serializer for property model."""

    class Meta:
        model = AIReport
        fields = [
            "id",
            "property",
            "user",
            "extracted_area",
            "extracted_city",
        ]
        read_only_fields = ["id"]


class AIReportUserSerializer(serializers.ModelSerializer):
    """AI Report property serializer for property model."""

    class Meta:
        model = User
        fields = ["id", "username"]
        read_only_fields = fields


class AIReportPropertySerializer(serializers.ModelSerializer):
    """AI Report property serializer for property model."""

    class Meta:
        model = Property
        fields = ["id", "title"]
        read_only_fields = fields


class AIReportRetrieveSerializer(serializers.ModelSerializer):
    """AI Report serializer for property model."""

    property = AIReportPropertySerializer(read_only=True)
    user = AIReportUserSerializer(read_only=True)

    class Meta:
        model = AIReport
        fields = [
            "id",
            "property",
            "user",
            "status",
            "extracted_area",
            "extracted_city",
            "avg_beds",
            "avg_baths",
            "avg_market_price",
            "avg_price_per_sqft",
            "investment_rating",
            "ai_insight_summary",
            "created_at",
        ]
        read_only_fields = fields


class AIReportListSerializer(serializers.ModelSerializer):
    """AI Report serializer for property model."""

    class Meta:
        model = AIReport
        fields = [
            "id",
            "status",
            "extracted_area",
            "extracted_city",
            "avg_market_price",
            "avg_price_per_sqft",
            "investment_rating",
            "created_at",
        ]
        read_only_fields = fields


class AIReportRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """AI Report request serializer for report creation."""

    property_id = serializers.IntegerField(required=True)


class ErrorResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Standard error response structure (HTTP 400, 429, 500)."""

    error = serializers.CharField(
        help_text="A descriptive error message explaining the failure or status."
    )
