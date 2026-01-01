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
from core_db_ai.models import AIReport, Property
from .serializers import (
    AIReportSerializer,
    AIReportListSerializer,
    AIReportRetrieveSerializer,
    AIReportRequestSerializer,
    ErrorResponseSerializer,
)
from .paginations import AIReportPagination
from .filters import AIReportFilter
from .utils import extract_location
from .tasks import parallel_report_generator


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
        if self.action == "retrieve":
            return AIReportRetrieveSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Queryset for Report View."""
        user = self.request.user
        queryset = AIReport.objects.select_related("property", "user").order_by(
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
        summary="Create New Report",
        description="Creates a new report.",
        tags=["AI Reports"],
        request=AIReportRequestSerializer,
        responses={
            status.HTTP_202_ACCEPTED: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"success": {"type": "string"}},
                },
                description="Report generation started. Returns a success message.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("Bad Request. Occurs on missing required fields",),
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. Report cannot be created by staffs.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Report Creation",
                response_only=True,
                status_codes=["202"],
                value={"success": "Analysis Report 1 is being generated."},
            ),
            OpenApiExample(
                name="Property ID Required",
                response_only=True,
                status_codes=["400"],
                value={"error": "Property ID is required."},
            ),
            OpenApiExample(
                name="Report Already Exists",
                response_only=True,
                status_codes=["400"],
                value={"error": "Report for this property already exists (ID: 1)."},
            ),
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Creating Report Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to create a report."},
            ),
            OpenApiExample(
                name="Property Not Found",
                response_only=True,
                status_codes=["404"],
                value={"error": "Property not found."},
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """Create a new report."""
        current_user = request.user

        if current_user.is_staff and not current_user.is_superuser:
            return Response(
                {"error": "You do not have permission to create a report."},
                status=status.HTTP_403_FORBIDDEN,
            )

        property_id = request.data.get("property_id")

        if not property_id:
            return Response(
                {"error": "Property ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        property_obj = None

        try:
            property_obj = Property.objects.get(id=property_id)
        except Property.DoesNotExist:
            return Response(
                {"error": "Property not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        existing_report = AIReport.objects.filter(
            user=current_user, property=property_obj
        ).first()

        if existing_report:
            if existing_report.status != AIReport.Status.FAILED:
                return Response(
                    {
                        "error": (
                            "Report for this property already exists "
                            f"(ID: {existing_report.id})."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            existing_report.delete()

        area, city = extract_location(property_obj.address)

        report_data = {
            "user": current_user.id,
            "property": property_obj.pk,
            "extracted_area": area,
            "extracted_city": city,
        }

        serializer = self.get_serializer(data=report_data)
        serializer.is_valid(raise_exception=True)
        report = serializer.save()

        property_data = {
            "title": property_obj.title,
            "area": area,
            "city": city,
            "area_sqft": property_obj.area_sqft,
            "beds": property_obj.beds,
            "baths": property_obj.baths,
            "price": property_obj.price,
        }

        parallel_report_generator.delay(report.id, property_data)

        return Response(
            {"success": f"Analysis Report {report.id} is being generated."},
            status=status.HTTP_202_ACCEPTED,
        )

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
                value={"success": "Report with ID 1 deleted successfully."},
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
