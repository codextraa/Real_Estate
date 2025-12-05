import os
from django.conf import settings
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from core_db.models import Property
from backend.mixins import http_method_mixin
from backend.renderers import ViewRenderer
from backend.schema_serializers import (
    PropertyCreateRequestSerializer,
    PropertyUpdateRequestSerializer,
    ErrorResponseSerializer,
)
from .filters import PropertyFilter
from .paginations import PropertyPagination
from .serializers import (
    PropertyImageSerializer,
    PropertyListSerializer,
    PropertyRetrieveSerializer,
    PropertySerializer,
)


class PropertyViewSet(ModelViewSet):
    """Property Viewset."""

    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    renderer_classes = [ViewRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyFilter
    pagination_class = PropertyPagination
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        """Assign serializer based on action."""
        if self.action == "list":
            return PropertyListSerializer
        if self.action == "retrieve":
            return PropertyRetrieveSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        """Queryset for User View."""
        user = self.request.user
        base_queryset = Property.objects.select_related("agent", "agent__user")

        if self.action in ("list", "retrieve") or user.is_staff:
            return base_queryset.all()

        if user.is_agent:
            return base_queryset.filter(agent__user=user)

        return Property.objects.none()

    def http_method_not_allowed(self, request, *args, **kwargs):
        return http_method_mixin(request, *args, **kwargs)

    @extend_schema(
        summary="List All Properties",
        description=("Returns a paginated list of all Properties. "),
        tags=["Property Management"],
        request=None,
        responses={
            status.HTTP_200_OK: PropertyListSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List all properties."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve Single Property Details",
        description="Returns the details of a specific property by ID.",
        tags=["Property Management"],
        request=None,
        responses={
            status.HTTP_200_OK: PropertyRetrieveSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("Not Found. " "The Property ID does not exist "),
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
        """Retrieve a specific property."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create New Property",
        description="Allows an authenticated **Agent** to create a new property listing.",
        tags=["Property Management"],
        request={
            "application/json": PropertyCreateRequestSerializer,
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "price": {"type": "number", "format": "double"},
                    "property_type": {"type": "string"},
                    "address": {"type": "string"},
                    "beds": {"type": "integer"},
                    "baths": {"type": "integer"},
                    "area_sqft": {"type": "integer"},
                    "property_image": {"type": "string", "format": "binary"},
                },
            },
        },
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=PropertySerializer,
                description="Property created successfully. Returns a simple success object.",
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User is not an Agent or tried to set forbidden fields.",
            ),
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Creation",
                response_only=True,
                status_codes=["201"],
                value={"success": "Property created successfully."},
            ),
            OpenApiExample(
                name="Not an Agent Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to create a property."},
            ),
            OpenApiExample(
                name="Forbidden Field Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Image Size Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "image_url": ["Property image size should not exceed 2MB."]
                    }
                },
            ),
            OpenApiExample(
                name="Image Type Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"image_url": ["Property image type should be JPEG, PNG"]}
                },
            ),
            OpenApiExample(
                name="Missing Image Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"image_url": ["Property image is required."]}},
            ),
            OpenApiExample(
                name="Property Title Length Exceeded Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"title": ["property title length is more than 150."]}},
            ),
            OpenApiExample(
                name="Property Address Length Exceeded Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"title": ["property address length is more than 255."]}
                },
            ),
        ],
    )
    def create(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Create new property."""
        current_user = self.request.user

        if not current_user.is_agent:
            return Response(
                {"error": "You do not have permission to create a property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if "slug" in request.data or "agent" in request.data:  # pylint: disable=R0916
            return Response(
                {"error": "Forbidden fields cannot be updated."},
                status=status.HTTP_403_FORBIDDEN,
            )

        request_data = request.data.copy()
        property_image = request_data.pop("property_image", None)
        default_property_image = "property_images/default_image.jpg"

        request_data["agent"] = current_user
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        property_obj = serializer.instance

        if property_image:
            property_image_serializer = PropertyImageSerializer(
                property_obj, data={"image_url": property_image}
            )
            property_image_serializer.is_valid(raise_exception=True)
            property_image_serializer.save()
        else:
            property_obj.image_url = default_property_image
            property_obj.save()
        return Response(
            {"success": "Property created successfully."},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Allow only agents to update their own property.
        Patch method allowed, Put method not allowed"""

        not_allowed_method = self.http_method_not_allowed(request)

        if not_allowed_method:
            return not_allowed_method

        current_user = self.request.user
        property_instance = self.get_object()

        if "slug" in request.data or "agent" in request.data:  # pylint: disable=R0916
            return Response(
                {"error": "Forbidden fields cannot be updated."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if current_user != property_instance.agent.user:
            return Response(
                {"error": "You do not have permission to update this property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        request_data = request.data.copy()
        property_image = request_data.pop("property_image", None)
        old_image_path = None
        default_property_image = "property_images/default_image.jpg"

        if property_image:
            if (
                property_instance.image_url
                and property_instance.image_url.name != default_property_image
            ):
                old_image_path = os.path.join(
                    settings.MEDIA_ROOT, property_instance.image_url.name
                )

            property_image_serializer = PropertyImageSerializer(
                property_instance, data={"image_url": property_image}
            )
            property_image_serializer.is_valid(raise_exception=True)
            property_image_serializer.save()

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        partial = kwargs.pop("partial", False)
        serializer = self.get_serializer(
            property_instance, data=request_data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        property_instance.refresh_from_db()
        response_serializer = PropertyRetrieveSerializer(
            property_instance,
            context=self.get_serializer_context(),
        )

        return Response(
            {
                "success": "Property updated successfully.",
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # pylint: disable=R0801
    @extend_schema(
        summary="Update Property Listing (Partial)",
        description=(
            "Partially updates an existing property listing (**PATCH** method). "
            "Only the agent who created the property can update it. PUT is not allowed."
        ),
        tags=["Property Management"],
        request={
            "application/json": PropertyUpdateRequestSerializer,
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "price": {"type": "number", "format": "double"},
                    "property_type": {"type": "string"},
                    "address": {"type": "string"},
                    "beds": {"type": "integer"},
                    "baths": {"type": "integer"},
                    "area_sqft": {"type": "integer"},
                    "is_available": {"type": "boolean"},
                    "property_image": {"type": "string", "format": "binary"},
                },
            },
        },
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=PropertyRetrieveSerializer,
                description=(
                    "Property updated successfully. "
                    "Returns a success message and the updated property object.",
                ),
            ),
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Forbidden. User is not the property's agent, "
                    "or attempted to set forbidden fields ('slug' or 'agent').",
                ),
            ),
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Partial Update",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": "Property updated successfully.",
                    "data": {
                        "id": 1,
                        "agent": 1,
                        "title": "New Title",
                        "price": 500000.00,
                        "address": "123 Main St",
                        "image_url": "/media/new_image.jpg",
                    },
                },
            ),
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
            OpenApiExample(
                name="Unauthorized Update Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to update this property."},
            ),
            OpenApiExample(
                name="Forbidden Field Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Missing Image Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"image_url": ["Property image is required."]}},
            ),
            OpenApiExample(
                name="Image Size Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "image_url": ["Property image size should not exceed 2MB."]
                    }
                },
            ),
            OpenApiExample(
                name="Image Type Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"image_url": ["Property image type should be JPEG, PNG"]}
                },
            ),
            OpenApiExample(
                name="Property Title Length Exceeded Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"title": ["property title length is more than 150."]}},
            ),
            OpenApiExample(
                name="Property Address Length Exceeded Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"title": ["property address length is more than 255."]}
                },
            ),
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        """Partial update property (PATCH method)."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # pylint: enable=R0801

    @extend_schema(
        summary="Delete Property Listing",
        description=(
            "Deletes a property listing by ID. "
            "Only the agent  who created the property and Superuser can delete it.",
        ),
        tags=["Property Management"],
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response=PropertySerializer,
                description=(
                    "Property deleted successfully."
                    "Returns a success message with 204 status.",
                ),
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User is not the property's agent.",
            ),
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="The property ID does not exist or not found",
            ),
        },
        examples=[
            OpenApiExample(
                name="Successful Deletion",
                response_only=True,
                status_codes=["204"],
                value={"success": "Property Nice House deleted successfully."},
            ),
            OpenApiExample(
                name="Unauthorized Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You are not authorized to delete this property."},
            ),
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"detail": "Not found."},
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        """Allow only agents and superusers to delete their own property."""
        current_user = self.request.user
        property_instance = self.get_object()
        title = property_instance.title

        if (
            current_user != property_instance.agent.user
            and not current_user.is_superuser
        ):
            return Response(
                {"error": "You are not authorized to delete this property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        default_property_image = "property_images/default_image.jpg"
        old_property_image = None

        if (
            property_instance.image_url
            and property_instance.image_url.name != default_property_image
        ):
            old_property_image = os.path.join(
                settings.MEDIA_ROOT, property_instance.image_url.name
            )

        response = super().destroy(request, *args, **kwargs)

        if os.path.exists(old_property_image):
            os.remove(old_property_image)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": f"Property {title} deleted successfully."},
                status=status.HTTP_200_OK,
            )

        return response
