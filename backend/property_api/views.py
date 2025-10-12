# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from backend.renderers import ViewRenderer
from backend.mixins import http_method_mixin
from core_db.models import Property
from .serializers import (
    PropertySerializer,
    PropertyListSerializer,
    PropertyRetrieveSerializer,
)


class PropertyViewSet(ModelViewSet):
    queryset = Property.objects.all()
    serializer_class = PropertySerializer
    renderer_classes = [ViewRenderer]
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

        # pylint: disable=R0801
        if not current_user.is_agent:
            return Response(
                {"error": "You do not have permission to create a property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        request.data["agent"] = current_user
        response = super().create(request, *args, **kwargs)

        if response.status_code != status.HTTP_201_CREATED:
            return response

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

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            return Response(
                {"success": "Property updated successfully.", "data": response.data},
                status=status.HTTP_200_OK,
            )

        return response

    def destroy(self, request, *args, **kwargs):
        current_user = self.request.user
        property_instance = self.get_object()

        if not current_user != property_instance.agent.user:
            return Response(
                {"error": "You are not authorized to delete this property."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {
                    "success": f"Property {property_instance.title} deleted successfully."
                },
                status=status.HTTP_200_OK,
            )

        return response
