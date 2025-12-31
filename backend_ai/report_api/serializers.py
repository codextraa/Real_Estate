from rest_framework import serializers
from core_db_ai.models import AIReport


class AIReportSerializer(serializers.ModelSerializer):
    """AI Report serializer for property model."""

    class Meta:
        model = AIReport
        fields = [
            "id",
            "property",
            "user",
            "status",
            "extracted_area",
            "extracted_city",
            "comparable_data",
            "avg_beds",
            "avg_baths",
            "avg_market_price",
            "avg_price_per_sqft",
            "investment_rating",
            "ai_insight_summary",
            "created_at",
        ]

        read_only_fields = "__all__"


class AIReportListSerializer(serializers.ModelSerializer):
    """AI Report serializer for property model."""

    class Meta:
        model = AIReport
        fields = [
            "id",
            "property",
            "status",
            "extracted_area",
            "extracted_city",
            "avg_market_price",
            "investment_rating",
            "created_at",
        ]

        read_only_fields = "__all__"


class AIReportRequestSerializer(serializers.ModelSerializer):
    """AI Report request serializer for property model."""

    property_id = serializers.IntegerField(required=True)
    user_id = serializers.IntegerField(required=True)
