from rest_framework import serializers


class AIReportRequestSerializer(serializers.Serializer):  # pylint: disable=W0223
    """AI Report request serializer for report creation."""

    property_id = serializers.IntegerField(required=True)


class ErrorResponseSerializer(serializers.Serializer):  # pylint: disable=W0223
    """Standard error response structure (HTTP 400, 429, 500)."""

    error = serializers.CharField(
        help_text="A descriptive error message explaining the failure or status."
    )
