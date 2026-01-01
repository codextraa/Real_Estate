from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from django_filters.rest_framework import DjangoFilterBackend
from backend_ai.mixins import http_method_mixin
from backend_ai.renderers import ViewRenderer
from core_db_ai.models import AIReport
from .serializers import (
    AIReportSerializer,
    AIReportListSerializer,
    ErrorResponseSerializer,
)
from .paginations import AIReportPagination
from .filters import AIReportFilter


class AIReportViewSet(ModelViewSet):
    """AI Report ViewSet."""

    queryset = AIReport.objects.all()
    serializer_class = AIReportSerializer
    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = AIReportFilter
    pagination_class = AIReportPagination
    http_method_names = ["get", "post", "delete"]

    def get_serializer_class(self):
        """Assign serializer based on action."""
        if self.action in ("list", "my_reports"):
            return AIReportListSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Queryset for Report View."""
        user = self.request.user
        queryset = AIReport.objects.select_related("report", "user").order_by(
            "-created_at"
        )

        if self.action == "list" and user.is_staff:
            return queryset

        if self.action == "my_reports" and not user.is_staff:
            return queryset.filter(user=user)

        if self.action in ("retrieve", "destroy"):
            if user.is_staff:
                return queryset
            return queryset.filter(user=user)

        return queryset.none()

    def http_method_not_allowed(self, request, *args, **kwargs):
        return http_method_mixin(request, *args, **kwargs)

    @extend_schema(
        summary="List All Reports",
        description=("Returns a paginated list of all Reports."),
        tags=["AI Reports"],
        request=None,
        responses={
            status.HTTP_200_OK: AIReportListSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. Report is not an staff.",
            ),
        },
        examples=[
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Forbidden Field Error",
                response_only=True,
                status_codes=["403"],
                value={
                    "error": "Only users with an staff profile can access this endpoint."
                },
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List all reports."""
        user = request.user

        if not user.is_staff:
            return Response(
                {"error": "Only staff users can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="List All Reports of an Report",
        description=("Returns a paginated list of all reports of an Report."),
        tags=["AI Reports"],
        request=None,
        responses={
            status.HTTP_200_OK: AIReportListSerializer(many=True),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. Report is not a non-staff.",
            ),
        },
        examples=[
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Forbidden Field Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "Only non-staff users can access this endpoint."},
            ),
        ],
    )
    @action(detail=False, methods=["GET"], url_path="my-reports")
    def my_reports(self, request, *args, **kwargs):
        """List all reports of an user"""
        user = request.user

        if user.is_staff:
            return Response(
                {"error": "Only non-staff users can access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        queryset = self.get_queryset()

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Retrieve Single Report Details",
        description="Returns the details of a specific report by ID.",
        tags=["AI Reports"],
        request=None,
        responses={
            status.HTTP_200_OK: AIReportSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("Not Found. " "The Report ID does not exist "),
            ),
        },
        examples=[
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Not found."},
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific report."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Delete Report",
        description="Deletes a Report by ID.",
        tags=["AI Reports"],
        request=None,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"success": {"type": "string"}},
                },
                description="Report Deleted Successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("Report ID Not Found or Does not exist. "),
            ),
        },
        examples=[
            OpenApiExample(
                name="Successful Report Deletion",
                response_only=True,
                status_codes=["200"],
                value={"success": "Report Deleted Successfully."},
            ),
            OpenApiExample(
                name="Unauthorized Report Delete Error",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Report ID Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Report ID Not Found or Does not exist."},
            ),
            OpenApiExample(
                name="Unauthorized Report Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You are not authorized to delete this report."},
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        """Allow superusers and users who own the report to delete it."""
        current_user = self.request.user
        report_to_delete = self.get_object()

        if report_to_delete.user != current_user or not current_user.is_superuser:
            return Response(
                {"error": "You are not authorized to delete this report."},
                status=status.HTTP_403_FORBIDDEN,
            )

        report_id = report_to_delete.id
        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": f"Report with ID {report_id} deleted successfully."},
                status=status.HTTP_200_OK,
            )

        return response
