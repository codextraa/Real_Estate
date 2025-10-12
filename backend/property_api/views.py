# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from backend.renderers import ViewRenderer
from backend.mixins import http_method_mixin
from core_db.models import Property
from .paginations import PropertyPagination
from .filters import PropertyFilter
from .serializers import (
    PropertySerializer,
    PropertyImageSerializer,
    PropertyListSerializer,
    PropertyRetrieveSerializer,
)


class PropertyViewSet(ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    renderer_classes = [ViewRenderer]
    filter_backends = [DjangoFilterBackend]
    filterset_class = PropertyFilter
    pagination_class = PropertyPagination
    permission_classes = [IsAuthenticated]

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
        if self.action in ("list", "retrieve") or user.is_staff:
            return Property.objects.all()
        if user.is_agent:
            return Property.objects.filter(agent=user)
        return Property.objects.none()

    def http_method_not_allowed(self, request, *args, **kwargs):
        return http_method_mixin(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Create new property."""
        current_user = self.request.user

        if not current_user.is_agent:
            return Response(
                {"error": "You do not have permission to create a property."},
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
            image_serializer = PropertyImageSerializer(
                property_obj, data={"image_url": property_image}
            )
            image_serializer.is_valid(raise_exception=True)
            image_serializer.save()
        else:
            property_obj.image_url = default_property_image
            property_obj.save()

        # pylint: disable=R0801
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
        # pylint: enable=R0801

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

        if (
            property_image
            and property_image.name != property_instance.image_url.name.split("/")[-1]
        ):
            image_serializer = PropertyImageSerializer(
                property_instance, data={"image_url": property_image}
            )
            image_serializer.is_valid(raise_exception=True)
            image_serializer.save()

        partial = kwargs.pop("partial", True)

        serializer = self.get_serializer(
            property_instance, data=request_data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(
            {"success": "Property updated successfully.", "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        current_user = self.request.user
        property_instance = self.get_object()

        if current_user != property_instance.agent.user:
            return Response(
                {"error": "You are not authorized to delete this property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        default_property_image = "property_images/default_image.jpg"
        if (
            property_instance.image_url
            and property_instance.image_url.name != default_property_image
        ):
            property_instance.image_url.delete(save=False)

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {
                    "success": f"Property {property_instance.title} deleted successfully."
                },
                status=status.HTTP_204_NO_CONTENT,
            )

        return response
