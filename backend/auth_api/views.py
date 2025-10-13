"""Views for Auth API."""  # pylint: disable=C0302

from datetime import timedelta
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from backend.renderers import ViewRenderer
from backend.mixins import http_method_mixin
from .paginations import UserPagination
from .filters import UserFilter
from .serializers import (
    UserSerializer,
    UserListSerializer,
    UserRetrieveSerializer,
    AgentSerializer,
)


def check_request_data(request):
    """Check if request data is valid."""

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

        check_integrity = check_request_data(request)

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

        current_user = self.request.user
        user = self.get_object()
        # pylint: enable=R0801

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

        if current_user.id != user.id and not current_user.is_superuser:
            return Response(
                {"error": "You do not have permission to update this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            return Response(
                {"success": "User profile updated successfully."},
                status=status.HTTP_200_OK,
            )

        return response

    def destroy(self, request, *args, **kwargs):
        """Allow only superusers to delete normal or staff users and clean up profile image."""
        current_user = self.request.user
        user_to_delete = self.get_object()

        if not current_user.is_superuser or current_user.id != user_to_delete.id:
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
    filter_backends = [DjangoFilterBackend]
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

    def create(self, request, *args, **kwargs):
        """Create Agent Profile"""

        check_integrity = check_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity

        request_data = request.data.copy()
        agent_keys = ["company_name", "bio", "image_url"]
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
