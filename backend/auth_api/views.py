"""Views for Auth API."""  # pylint: disable=C0302

import os
from datetime import timedelta
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from backend.renderers import ViewRenderer
from backend.mixins import http_method_mixin
from backend.schema_serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    ErrorResponseSerializer,
)
from core_db.models import Agent
from .paginations import UserPagination
from .filters import UserFilter
from .serializers import (
    UserSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
    AgentSerializer,
    AgentListSerializer,
    AgentRetrieveSerializer,
    AgentImageSerializer,
)


def check_create_request_data(request):
    """Check if create request data is valid."""

    current_user = request.user
    if "is_superuser" in request.data:
        return Response(
            {
                "error": "You do not have permission to create a superuser. Contact Developer."
            },
            status=status.HTTP_403_FORBIDDEN,
        )

    if "is_staff" in request.data and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to create an admin user."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if "slug" in request.data or "is_active" in request.data:
        return Response(
            {"error": "Forbidden fields cannot be updated."},
            status=status.HTTP_403_FORBIDDEN,
        )

    password = request.data.get("password")
    if not request.data.get("c_password"):
        return Response(
            {"error": "Please confirm your password."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    c_password = request.data.pop("c_password")
    if password != c_password:
        return Response(
            {"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST
        )

    return current_user


def check_update_request_data(user_instance, request):
    """Check if update request data is valid."""

    current_user = request.user

    if "email" in request.data:
        return Response(
            {"error": "You cannot update the email field."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if (
        "slug" in request.data  # pylint: disable=R0916
        or "is_active" in request.data
        or "is_staff" in request.data
        or "is_superuser" in request.data
    ):
        return Response(
            {"error": "Forbidden fields cannot be updated."},
            status=status.HTTP_403_FORBIDDEN,
        )

    if current_user.id != user_instance.id and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to update this user."},
            status=status.HTTP_403_FORBIDDEN,
        )

    return current_user


def get_user_role(user):
    """Get user role."""
    user_groups = user.groups.all()

    if user_groups.filter(name="Default").exists():
        user_role = "Default"
    elif user_groups.filter(name="Agent").exists():
        user_role = "Agent"
    elif user_groups.filter(name="Admin").exists():
        user_role = "Admin"
    elif user_groups.filter(name="Superuser").exists():
        user_role = "Superuser"
    else:
        user_role = "UnAuthorized"

    return user_role


def check_user_validity(email):
    """Check if user is valid using email."""
    user = get_user_model().objects.filter(email=email).first()

    # Check if user exists
    if not user:
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Check if user is active
    if not user.is_active:
        return Response(
            {"error": "Account is deactivated. Contact your admin"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return user


def check_user_id(user_id):
    """Check if user id is valid."""
    try:
        user_id = int(user_id)
    except Exception as e:  # pylint: disable=W0718
        print(e)
        return Response(
            {"error": "Invalid Session"}, status=status.HTTP_400_BAD_REQUEST
        )

    user = get_user_model().objects.filter(id=user_id).first()

    if not user:
        return Response(
            {"error": "Invalid Session"}, status=status.HTTP_400_BAD_REQUEST
        )

    return check_user_validity(user.email)


@extend_schema(
    # General documentation for the POST method
    summary="User Login and Token Acquisition",
    description=(
        "Authenticates the user with email and password. "
        "If valid, an OTP is sent to the registered email."
    ),
    tags=["Authentication"],
    # Define the request body schema
    request=LoginRequestSerializer,
    # Define the possible responses and link them to serializers/examples
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=LoginResponseSerializer,
            description="Successful authentication. Returns JWT tokens and user metadata.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description=(
                "Bad Request. Occurs on invalid credentials, deactivated account, "
                "missing email/password, or other pre-auth failures."
            ),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Internal Server Error.",
        ),
    },
    # Provide concrete examples for better API reference UI
    examples=[
        OpenApiExample(
            name="Successful Agent Login",
            response_only=True,
            status_codes=["200"],
            value={
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.A-VERY-LONG-JWT-TOKEN-PART-1",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.A-VERY-LONG-JWT-TOKEN-PART-2",
                "user_id": 101,
                "user_role": "Agent",
                "access_token_expiry": (now() + timedelta(hours=1)).isoformat(),
            },
        ),
        OpenApiExample(
            name="Invalid Credentials Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Invalid credentials"},
        ),
        OpenApiExample(
            name="Deactivated Account Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Account is deactivated. Contact your admin"},
        ),
        OpenApiExample(
            name="Missing Email/Password Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Email and password are required"},
        ),
    ],
)
class LoginView(TokenObtainPairView):
    """Login View."""

    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Post a request to login. Returns an OTP to the registered email."""
        try:
            email = request.data.get("email")
            password = request.data.get("password")

            if not email or not password:
                return Response(
                    {"error": "Email and password are required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            user = check_user_validity(email)

            if isinstance(user, Response):
                return user

            # Check if password is correct
            if not user.check_password(password):
                return Response(
                    {"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST
                )

            response = super().post(request, *args, **kwargs)

            response.data["access_token_expiry"] = (
                now() + timedelta(hours=1)
            ).isoformat()

            user_role = get_user_role(user)

            response.data["user_role"] = user_role
            response.data["user_id"] = user.id
            response.data["access_token"] = response.data["access"]
            response.data["refresh_token"] = response.data["refresh"]
            response.data.pop("access")
            response.data.pop("refresh")

            return response
        except Exception as e:  # pylint: disable=W0718
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class RefreshTokenView(TokenRefreshView):
    """Refresh Token View generates JWT access token using the refresh token."""

    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):
        """Post a request to RefreshTokenView. Verifies OTP and generates JWT tokens."""
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "Tokens are required"}, status=status.HTTP_400_BAD_REQUEST
                )

            response = super().post(request, *args, **kwargs)
            response.data["access_token_expiry"] = (
                now() + timedelta(minutes=5)
            ).isoformat()

            # Extract the access token and refresh token
            refresh_token = response.data.get("refresh")
            access_token = response.data.get("access")

            if not refresh_token or not access_token:
                return Response(
                    {"error": "Invalid tokens"}, status=status.HTTP_400_BAD_REQUEST
                )

            # Decode the access token to extract user details
            decoded_token = RefreshToken(refresh_token)
            user_id = decoded_token.get("user_id", None)
            if not user_id:
                raise InvalidToken("Invalid refresh token")

            # Check user validity
            user = check_user_id(user_id)

            if isinstance(user, Response):
                return user

            user_role = get_user_role(user)

            response.data["user_role"] = user_role
            response.data["user_id"] = user.id
            response.data["access_token"] = response.data["access"]
            response.data["refresh_token"] = response.data["refresh"]
            response.data.pop("access")
            response.data.pop("refresh")

            return response

        except TokenError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:  # pylint: disable=W0718
            # return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
            print(e)
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )


class UserViewSet(ModelViewSet):
    """User View Set."""

    queryset = get_user_model().objects.all()  # get all the users
    renderer_classes = [ViewRenderer]
    serializer_class = UserSerializer  # User Serializer initialized
    authentication_classes = [JWTAuthentication]  # Using jwtoken
    filter_backends = [DjangoFilterBackend]
    filterset_class = UserFilter
    pagination_class = UserPagination
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        """Assign serializer based on action."""
        if self.action == "list":
            return UserListSerializer
        if self.action == "retrieve":
            return UserRetrieveSerializer
        return super().get_serializer_class()

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):  # pylint: disable=R0911
        """Queryset for User View."""
        if self.action == "list":
            if self.request.user.is_staff:
                return get_user_model().objects.all()
            return get_user_model().objects.none()

        if self.action == "retrieve":
            if self.request.user.is_staff:
                return get_user_model().objects.all()
            if self.request.user.is_agent:
                return get_user_model().objects.filter(is_staff=False)

            allowed_user_queryset = Q(pk=self.request.user.pk) | Q(is_agent=True)
            return get_user_model().objects.filter(allowed_user_queryset)

        # create, update, partial_update, destroy
        if self.request.user.is_superuser:
            return get_user_model().objects.all()
        return get_user_model().objects.filter(pk=self.request.user.pk)

    def http_method_not_allowed(self, request, *args, **kwargs):
        return http_method_mixin(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Create new user and send email verification link."""

        check_integrity = check_create_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity

        response = super().create(request, *args, **kwargs)

        if response.status_code != status.HTTP_201_CREATED:
            return response

        # pylint: disable=R0801
        return Response(
            {"success": "User created successfully."},
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):
        """Allow only users to update their own profile. SuperUser can update any profile.
        Patch method allowed, Put method not allowed"""

        not_allowed_method = self.http_method_not_allowed(request)

        if not_allowed_method:
            return not_allowed_method

        user = self.get_object()
        # pylint: enable=R0801

        check_integrity = check_update_request_data(user, request)

        if isinstance(check_integrity, Response):
            return check_integrity

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            return Response(
                {
                    "success": "User profile updated successfully.",
                    "data": response.data,
                },
                status=status.HTTP_200_OK,
            )

        return response

    def destroy(self, request, *args, **kwargs):
        """Allow only superusers to delete normal or staff users and clean up profile image."""
        current_user = self.request.user
        user_to_delete = self.get_object()

        if not current_user.is_superuser and current_user.id != user_to_delete.id:
            return Response(
                {"error": "You are not authorized to delete this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if user_to_delete.is_superuser:
            return Response(
                {"error": "You cannot delete superusers"},
                status=status.HTTP_403_FORBIDDEN,
            )

        email = user_to_delete.email
        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": f"User {email} deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return response


class AgentViewSet(ModelViewSet):
    """Agent Viewset."""

    queryset = get_user_model().objects.all()
    serializer_class = AgentSerializer
    renderer_classes = [ViewRenderer]
    authentication_classes = [JWTAuthentication]  # Using jwtoken
    pagination_class = UserPagination
    http_method_names = ["get", "post", "patch", "delete"]

    def get_permissions(self):
        """Assign permissions based on action."""
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):  # pylint: disable=R0911
        """Queryset for User View."""
        user = self.request.user

        if self.action == "list":
            if self.request.user.is_staff:
                return Agent.objects.all().select_related("user")
            return Agent.objects.none()

        if self.action == "retrieve":
            if self.request.user.is_staff:
                return Agent.objects.all().select_related("user")
            if self.request.user.is_agent:
                return Agent.objects.filter(user__is_staff=False).select_related("user")

            allowed_user_queryset = Q(user__pk=user.pk) | Q(user__is_agent=True)
            return Agent.objects.filter(allowed_user_queryset).select_related("user")

        # create, update, partial_update, destroy
        if self.request.user.is_superuser:
            return Agent.objects.all().select_related("user")
        return Agent.objects.filter(user=user).select_related("user")

    def get_object(self):
        """
        Retrieves an Agent object by filtering its related User's ID (pk in URL).
        It also enforces the permissions defined in get_queryset for the current action.
        """
        lookup_value = self.kwargs.get(self.lookup_url_kwarg or self.lookup_field)

        if not lookup_value:
            return super().get_object()

        queryset = self.get_queryset()

        obj = get_object_or_404(queryset, user_id=lookup_value)

        self.check_object_permissions(self.request, obj)

        return obj

    def get_serializer_class(self):
        """Assign serializer based on action."""
        if self.action == "list":
            return AgentListSerializer
        if self.action == "retrieve":
            return AgentRetrieveSerializer
        return super().get_serializer_class()

    def http_method_not_allowed(self, request, *args, **kwargs):
        return http_method_mixin(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create Agent Profile"""

        check_integrity = check_create_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity

        request_data = request.data.copy()
        agent_keys = ["company_name", "bio", "profile_image"]
        user_request_data = request_data
        agent_request_data = {}

        for key in user_request_data.keys():
            if key in agent_keys:
                agent_request_data[key] = request_data[key]
                user_request_data.pop(key)

        user_serializer = UserSerializer(data=user_request_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        agent_request_data["user"] = user
        agent_serializer = self.get_serializer(data=agent_request_data)
        agent_serializer.is_valid(raise_exception=True)
        agent = agent_serializer.save()
        agent.image_url = "profile_images/default_profile.jpg"
        agent.save()

        return Response(
            {
                "success": "Agent created successfully",
            },
            status=status.HTTP_201_CREATED,
        )

    def update(self, request, *args, **kwargs):  # pylint: disable=R0914
        """Update Agent Profile"""

        not_allowed_method = self.http_method_not_allowed(request)

        if not_allowed_method:
            return not_allowed_method

        agent = self.get_object()
        user_instance = agent.user
        # pylint: enable=R0801

        check_integrity = check_update_request_data(user_instance, request)

        if isinstance(check_integrity, Response):
            return check_integrity

        request_data = request.data.copy()
        agent_keys = ["company_name", "bio", "profile_image"]
        user_request_data = request_data
        agent_request_data = {}

        for key in user_request_data.keys():
            if key in agent_keys:
                agent_request_data[key] = request_data[key]
                user_request_data.pop(key)

        user_serializer = UserSerializer(
            user_instance, data=user_request_data, partial=True
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        profile_image = request.data.pop("profile_image", None)
        old_image_path = None

        if profile_image:
            if (
                agent.image_url
                and agent.image_url.name != "profile_images/default_profile.jpg"
            ):
                old_image_path = os.path.join(settings.MEDIA_ROOT, agent.image_url.name)

            agent_image_serializer = AgentImageSerializer(
                agent, data={"image_url": profile_image}
            )
            agent_image_serializer.is_valid(raise_exception=True)
            agent_image_serializer.save()

            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        partial = kwargs.pop("partial", False)
        agent_serializer = self.get_serializer(
            agent, data=agent_request_data, partial=partial
        )
        agent_serializer.is_valid(raise_exception=True)
        self.perform_update(agent_serializer)

        updated_agent_serializer = self.get_serializer(agent)
        response_data = updated_agent_serializer.data
        user_serializer = UserSerializer(user_instance)
        response_data["user"] = user_serializer.data

        return Response(
            {
                "success": "Agent updated successfully",
                "data": response_data,
            },
            status=status.HTTP_200_OK,
        )

    def destroy(self, request, *args, **kwargs):
        """Destroy Agent Profile"""

        current_user = self.request.user
        agent_to_delete = self.get_object()

        if not current_user.is_superuser and current_user.id != agent_to_delete.user.id:
            return Response(
                {"error": "You are not authorized to delete this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        default_profile_image = "/profile_images/default_profile.jpg"
        old_agent_image = None

        if (
            agent_to_delete.image_url
            and agent_to_delete.image_url.name != default_profile_image
        ):
            old_agent_image = os.path.join(
                settings.MEDIA_ROOT, agent_to_delete.image_url.name
            )

        response = super().destroy(request, *args, **kwargs)

        if os.path.exists(old_agent_image):
            os.remove(old_agent_image)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": "Agent profile deleted successfully."},
                status=status.HTTP_204_NO_CONTENT,
            )

        return response
