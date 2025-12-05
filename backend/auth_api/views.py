"""Views for Auth API."""  # pylint: disable=C0302

import os
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)
from core_db.models import Agent
from backend.renderers import ViewRenderer
from backend.mixins import http_method_mixin
from backend.schema_serializers import (
    LoginRequestSerializer,
    LoginResponseSerializer,
    ErrorResponseSerializer,
    LogoutRequestSerializer,
    RefreshTokenRequestSerializer,
    UserCreateRequestSerializer,
    UserUpdateRequestSerializer,
    AgentCreateRequestSerializer,
    AgentUpdateRequestSerializer,
)
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

    if current_user.id != user_instance.id and not current_user.is_superuser:
        return Response(
            {"error": "You do not have permission to update this user."},
            status=status.HTTP_403_FORBIDDEN,
        )

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

    password = request.data.get("password")
    if password:
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


@extend_schema(
    summary="User Login and Token Acquisition",
    description=(
        "Authenticates the user with email and password. "
        "If valid, an access token and refresh token are returned."
    ),
    tags=["Authentication"],
    request=LoginRequestSerializer,
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
    examples=[
        OpenApiExample(
            name="Superuser Login Request Example",
            value={
                "email": "superuser@example.com",
                "password": "Django@123",
            },
        ),
        OpenApiExample(
            name="Staff Login Request Example",
            value={
                "email": "staffuser@example.com",
                "password": "Django@123",
            },
        ),
        OpenApiExample(
            name="Agent Login Request Example",
            value={
                "email": "agentuser@example.com",
                "password": "Django@123",
            },
        ),
        OpenApiExample(
            name="Default User Login Request Example",
            value={
                "email": "defaultuser@example.com",
                "password": "Django@123",
            },
        ),
        OpenApiExample(
            name="Successful Agent Login",
            response_only=True,
            status_codes=["200"],
            value={
                "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.A-VERY-LONG-JWT-TOKEN-PART-1",
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUz1NiJ9.A-VERY-LONG-JWT-TOKEN-PART-2",
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


@extend_schema(
    summary="User Logout",
    description=("Logout by blacklisting the refresh token."),
    tags=["Authentication"],
    request=LogoutRequestSerializer,
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=LoginResponseSerializer,
            description="Successful logout.",
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description=("Bad Request. Missing tokens."),
        ),
        status.HTTP_500_INTERNAL_SERVER_ERROR: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="Internal Server Error.",
        ),
    },
    examples=[
        OpenApiExample(
            name="Successful Logout",
            response_only=True,
            status_codes=["200"],
            value={"success": "Logged out successfully"},
        ),
        OpenApiExample(
            name="Missing Tokens Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Tokens are required"},
        ),
    ],
)
class LogoutView(APIView):
    """
    Logout by blacklisting the refresh token.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data.get("refresh")

            if not refresh_token:
                return Response(
                    {"error": "Tokens are required"}, status=status.HTTP_400_BAD_REQUEST
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"success": "Logged out successfully"}, status=status.HTTP_200_OK
            )

        except Exception as e:  # pylint: disable=W0718
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    # General documentation for the POST method
    summary="Refresh Access Token",
    description=(
        "Exchanges a valid refresh token for a new access token. "
        "Also returns the refresh token and updated user metadata."
    ),
    tags=["Authentication"],
    # Define the request body schema
    request=RefreshTokenRequestSerializer,
    # Define the possible responses and link them to serializers/examples
    responses={
        status.HTTP_200_OK: OpenApiResponse(
            response=LoginResponseSerializer,
            description=(
                "Successful token refresh. "
                "Returns a new access token and the same refresh token.",
            ),
        ),
        status.HTTP_400_BAD_REQUEST: OpenApiResponse(
            response=ErrorResponseSerializer,
            description=(
                "Bad Request. Occurs on a missing 'refresh' token or an invalid token format."
            ),
        ),
        status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
            response=ErrorResponseSerializer,
            description=(
                "Unauthorized. "
                "Occurs when the refresh token is expired, invalid, or blacklisted.",
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
            name="Successful Token Refresh",
            response_only=True,
            status_codes=["200"],
            value={
                "access_token": (
                    "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9."
                    "A-NEW-SHORT-LIVED-JWT-TOKEN-PART-1",
                ),
                "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUz1NiJ9.A-VERY-LONG-JWT-TOKEN-PART-2",
                "user_id": 101,
                "user_role": "Agent",
                # Note: TimeDelta is 5 minutes for refresh endpoint in your code
                "access_token_expiry": (now() + timedelta(minutes=5)).isoformat(),
            },
        ),
        OpenApiExample(
            name="Missing Refresh Token Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Tokens are required"},
        ),
        OpenApiExample(
            name="Invalid/Expired Refresh Token Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Invalid tokens"},
        ),
        OpenApiExample(
            name="Invalid Refresh Token Error",
            response_only=True,
            status_codes=["401"],
            value={"error": "Invalid Refresh Token"},
        ),
        OpenApiExample(
            name="Invalid Session Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Invalid Session"},
        ),
        OpenApiExample(
            name="Invalid Credentials Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Invalid credentials"},
        ),
        OpenApiExample(
            name="Account Deactivated Error",
            response_only=True,
            status_codes=["400"],
            value={"error": "Account is deactivated. Contact your admin"},
        ),
    ],
)
class RefreshTokenView(TokenRefreshView):
    """Refresh Token View generates JWT access token using the refresh token."""

    renderer_classes = [ViewRenderer]

    def post(self, request, *args, **kwargs):  # pylint: disable=R0911
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
                return Response(
                    {"error": "Invalid tokens"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

    @extend_schema(
        summary="List All Users",
        description=(
            "Returns a paginated list of all user accounts. "
            "Access is restricted to staff/superusers.",
        ),
        tags=["User Management"],
        request=None,
        responses={
            status.HTTP_200_OK: UserListSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User does not have staff or superuser privileges.",
            ),
        },
        examples=[
            OpenApiExample(
                name="Forbidden Access",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to perform this action."},
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        """List all users."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve Single User Details",
        description="Returns the details of a specific user by ID.",
        tags=["User Management"],
        request=None,
        responses={
            status.HTTP_200_OK: UserRetrieveSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Not Found. "
                    "The user ID does not exist "
                    "or the authenticated user does not have permission to view it.",
                ),
            ),
        },
        examples=[
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Not found."},
            ),
            OpenApiExample(
                name="Forbidden Access",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to perform this action."},
            ),
            OpenApiExample(
                name="Unauthorized Access",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific user."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create New User",
        description="Registers a new user account. Does not require authentication.",
        tags=["User Management"],
        request=UserCreateRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=UserSerializer,
                description="User created successfully. Returns a success message.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=(
                    "Bad Request. "
                    "Occurs on missing required fields, invalid data format, or duplicate email.",
                ),
            ),
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User does not have staff or superuser privileges.",
            ),
            status.HTTP_500_INTERNAL_SERVER_ERROR: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful User Creation",
                response_only=True,
                status_codes=["201"],
                value={"success": "User created successfully."},
            ),
            OpenApiExample(
                name="Creating Admin Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to create an admin user."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Username Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"username": ["User with this username already exists."]}
                },
            ),
            OpenApiExample(
                name="Username Too Short Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "username": ["Username must be at least 6 characters long."]
                    }
                },
            ),
            OpenApiExample(
                name="Email Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "User with this email already exists.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Invalid Email Address Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "Enter a valid email address.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
        ],
    )
    def create(self, request, *args, **kwargs):  # pylint: disable=R0911
        """Create new user and send email verification link."""

        check_integrity = check_create_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity

        response = super().create(request, *args, **kwargs)

        if response.status_code != status.HTTP_201_CREATED:
            return response

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

        check_integrity = check_update_request_data(user, request)

        if isinstance(check_integrity, Response):
            return check_integrity

        response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            user.refresh_from_db()
            retrieve_serializer = UserRetrieveSerializer(
                user,
                context=self.get_serializer_context(),
            )
            return Response(
                {
                    "success": "User profile updated successfully.",
                    "data": retrieve_serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return response

    @extend_schema(
        summary="Update User Profile (Partial)",
        description="Partially updates an existing user profile (PATCH method).",
        tags=["User Management"],
        request=UserUpdateRequestSerializer,
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=UserRetrieveSerializer,
                description="User profile updated successfully. Returns the updated user object.",
            ),
            status.HTTP_400_BAD_REQUEST: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Bad Request. Occurs on invalid field values or data integrity errors.",
            ),
            status.HTTP_401_UNAUTHORIZED: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Unauthorized. User is not authenticated.",
            ),
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Success",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": "User profile updated successfully.",
                    "data": {
                        "id": 1,
                        "first_name": "Updated",
                        "last_name": "User",
                        "email": "1b8Xu@example.com",
                        "username": "updateduser",
                        "slug": "updateduser",
                    },
                },
            ),
            OpenApiExample(
                name="Method Not Allowed",
                response_only=True,
                status_codes=["405"],
                value={"error": "PUT operation not allowed."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
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
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to update this user."},
            ),
            OpenApiExample(
                name="Updating Email field",
                response_only=True,
                status_codes=["403"],
                value={"error": "You cannot update the email field."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Username Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"username": ["User with this username already exists."]}
                },
            ),
            OpenApiExample(
                name="Username Too Short Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "username": ["Username must be at least 6 characters long."]
                    }
                },
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially updates an existing user profile (PATCH method)."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    @extend_schema(
        summary="Delete User Profile",
        description="Deletes a user profile by ID.",
        tags=["User Management"],
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response={
                    "type": "object",
                    "properties": {"success": {"type": "string"}},
                },
                description="User Profile Deleted Successfully.",
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("User ID Not Found or Does not exist. "),
            ),
        },
        examples=[
            OpenApiExample(
                name="Successful User Deletion",
                response_only=True,
                status_codes=["204"],
                value={"success": "User Profile Deleted Successfully."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="User ID Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "User ID Not Found or Does not exist."},
            ),
            OpenApiExample(
                name="Unauthorized User Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You are not authorized to delete this user."},
            ),
            OpenApiExample(
                name="Superuser Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You cannot delete superusers."},
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        """Allow user to delete their own profile and superuser to delete normal or staff users"""
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
                status=status.HTTP_200_OK,
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

    @extend_schema(
        summary="List All Agents",
        description=("Returns a paginated list of all Agent accounts. "),
        tags=["Agent Management"],
        request=None,
        responses={
            status.HTTP_200_OK: AgentListSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
        },
    )
    def list(self, request, *args, **kwargs):
        """List all Agents."""
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve Single Agent Details",
        description="Returns the details of a specific agent by ID.",
        tags=["Agent Management"],
        request=None,
        responses={
            status.HTTP_200_OK: AgentRetrieveSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_404_NOT_FOUND: OpenApiResponse(
                response=ErrorResponseSerializer,
                description=("Not Found. " "The agent ID does not exist "),
            ),
        },
        examples=[
            OpenApiExample(
                name="Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "Not found."},
            ),
        ],
    )
    def retrieve(self, request, *args, **kwargs):
        """Retrieve a specific agent."""
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Register New Agent",
        description="Creates a new Agent profile and related User account.",
        tags=["Agent Management"],
        request=AgentCreateRequestSerializer,
        responses={
            status.HTTP_201_CREATED: OpenApiResponse(
                response=AgentSerializer,
                description="Agent created successfully. Returns a success message.",
            ),
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Agent Creation",
                response_only=True,
                status_codes=["201"],
                value={"success": "Agent created successfully"},
            ),
            OpenApiExample(
                name="Creating Admin Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to create an admin user."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Username Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"username": ["User with this username already exists."]}
                },
            ),
            OpenApiExample(
                name="Username Too Short Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "username": ["Username must be at least 6 characters long."]
                    }
                },
            ),
            OpenApiExample(
                name="Email Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "User with this email already exists.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Invalid Email Address Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "email": [
                            "Enter a valid email address.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Company Name Exceeds Max Length Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "company_name": [
                            "Company name must be less than 255 characters.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Bio Exceeds Max Length Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "bio": [
                            "Bio must be less than 150 characters.",
                        ]
                    }
                },
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        """Create User and Agent Profile"""

        check_integrity = check_create_request_data(request)

        if isinstance(check_integrity, Response):
            return check_integrity

        request_data = request.data.copy()
        agent_keys = ["company_name", "bio", "profile_image"]
        user_request_data = {}
        agent_request_data = {}

        for key in request_data.keys():
            if key in agent_keys:
                agent_request_data[key] = request_data[key]
            else:
                user_request_data[key] = request_data[key]

        user_serializer = UserSerializer(data=user_request_data)
        user_serializer.is_valid(raise_exception=True)
        user = user_serializer.save()

        agent_request_data["user"] = user.pk
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
        """Update Agent Profile and User Profile"""

        not_allowed_method = self.http_method_not_allowed(request)

        if not_allowed_method:
            return not_allowed_method

        agent = self.get_object()
        user_instance = agent.user

        check_integrity = check_update_request_data(user_instance, request)

        if isinstance(check_integrity, Response):
            return check_integrity

        request_data = request.data.copy()
        agent_keys = ["company_name", "bio", "profile_image"]
        user_request_data = {}
        agent_request_data = {}

        for key in request_data.keys():
            if key in agent_keys:
                agent_request_data[key] = request_data[key]
            else:
                user_request_data[key] = request_data[key]

        partial = kwargs.pop("partial", False)
        user_serializer = UserSerializer(
            user_instance, data=user_request_data, partial=partial
        )
        user_serializer.is_valid(raise_exception=True)
        user_serializer.save()

        profile_image = agent_request_data.pop("profile_image", None)
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

            if old_image_path and os.path.exists(old_image_path):
                os.remove(old_image_path)

        agent_serializer = self.get_serializer(
            agent, data=agent_request_data, partial=partial
        )
        agent_serializer.is_valid(raise_exception=True)
        agent_serializer.save()

        agent.refresh_from_db()
        response_serializer = AgentRetrieveSerializer(
            agent,
            context=self.get_serializer_context(),
        )

        return Response(
            {
                "success": "Agent updated successfully",
                "data": response_serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    # pylint: disable=R0801
    @extend_schema(
        summary="Update Agent Profile (Partial)",
        description=(
            "Partially updates the Agent's profile (User data and Agent data). "
            "Only the respective user or a Superuser can update this profile."
        ),
        tags=["Agent Management"],
        request={
            "application/json": AgentUpdateRequestSerializer,
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "password": {"type": "string", "format": "password"},
                    "c_password": {"type": "string", "format": "password"},
                    "username": {"type": "string"},
                    "first_name": {"type": "string"},
                    "last_name": {"type": "string"},
                    "company_name": {"type": "string"},
                    "bio": {"type": "string"},
                    "profile_image": {"type": "string", "format": "binary"},
                },
            },
        },
        responses={
            status.HTTP_200_OK: OpenApiResponse(
                response=AgentRetrieveSerializer,
                description=(
                    "Agent updated successfully."
                    "Returns a success message and the full updated Agent data.",
                ),
            ),
            status.HTTP_400_BAD_REQUEST: ErrorResponseSerializer,
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User cannot update this profile.",
            ),
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
            status.HTTP_405_METHOD_NOT_ALLOWED: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Update",
                response_only=True,
                status_codes=["200"],
                value={
                    "success": "Agent updated successfully",
                    "data": {
                        "id": 1,
                        "company_name": "Updated Co.",
                        "bio": "Updated bio",
                        "profile_image": "profile_images/default_profile.jpg",
                        "user": {
                            "id": 1,
                            "first_name": "Updated",
                            "last_name": "User",
                            "email": "1b8Xu@example.com",
                            "username": "updateduser",
                            "slug": "updateduser",
                        },
                    },
                },
            ),
            OpenApiExample(
                name="Method Not Allowed",
                response_only=True,
                status_codes=["405"],
                value={"error": "PUT operation not allowed."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
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
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You do not have permission to update this user."},
            ),
            OpenApiExample(
                name="Updating Email field",
                response_only=True,
                status_codes=["403"],
                value={"error": "You cannot update the email field."},
            ),
            OpenApiExample(
                name="Updating Forbidden fields.",
                response_only=True,
                status_codes=["403"],
                value={"error": "Forbidden fields cannot be updated."},
            ),
            OpenApiExample(
                name="Password Confirmation Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Please confirm your password."},
            ),
            OpenApiExample(
                name="Password Matching Error",
                response_only=True,
                status_codes=["400"],
                value={"error": "Passwords do not match."},
            ),
            OpenApiExample(
                name="Username Already Exists Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"username": ["User with this username already exists."]}
                },
            ),
            OpenApiExample(
                name="Username Too Short Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "username": ["Username must be at least 6 characters long."]
                    }
                },
            ),
            OpenApiExample(
                name="Password Complexity Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "password": [
                            "Password must be at least 8 characters.",
                            "Password must contain at least one uppercase letter.",
                            "Password must contain at least one number.",
                            "Password must contain at least one special character.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Company Name Exceeds Max Length Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "company_name": [
                            "Company name must be less than 255 characters.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Bio Exceeds Max Length Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {
                        "bio": [
                            "Bio must be less than 150 characters.",
                        ]
                    }
                },
            ),
            OpenApiExample(
                name="Image Type Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"profile_image": ["Image type should be JPEG, PNG"]}},
            ),
            OpenApiExample(
                name="Image Size Error",
                response_only=True,
                status_codes=["400"],
                value={
                    "error": {"profile_image": ["Image size should not exceed 2MB."]}
                },
            ),
            OpenApiExample(
                name="Image Required Error",
                response_only=True,
                status_codes=["400"],
                value={"error": {"profile_image": ["Image is Required."]}},
            ),
        ],
    )
    def partial_update(self, request, *args, **kwargs):
        """Partially updates the Agent's profile (Use data and Agent data)."""
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    # pylint: enable=R0801

    @extend_schema(
        summary="Delete Agent Profile",
        description="Deletes an Agent profile and their related User account by User ID.",
        tags=["Agent Management"],
        request=None,
        responses={
            status.HTTP_204_NO_CONTENT: OpenApiResponse(
                response=AgentSerializer,
                description=(
                    "Agent profile deleted successfully."
                    "Returns a success message with 204 status.",
                ),
            ),
            status.HTTP_401_UNAUTHORIZED: ErrorResponseSerializer,
            status.HTTP_403_FORBIDDEN: OpenApiResponse(
                response=ErrorResponseSerializer,
                description="Forbidden. User is not authorized to delete this profile.",
            ),
            status.HTTP_404_NOT_FOUND: ErrorResponseSerializer,
        },
        examples=[
            OpenApiExample(
                name="Successful Deletion",
                response_only=True,
                status_codes=["204"],
                value={"success": "Agent profile deleted successfully."},
            ),
            OpenApiExample(
                name="Unauthorized User Update Error",
                response_only=True,
                status_codes=["401"],
                value={"error": "You are not authenticated."},
            ),
            OpenApiExample(
                name="Unauthorized Delete Error",
                response_only=True,
                status_codes=["403"],
                value={"error": "You are not authorized to delete this user."},
            ),
            OpenApiExample(
                name="User ID Not Found Error",
                response_only=True,
                status_codes=["404"],
                value={"error": "User ID Not Found or Does not exist."},
            ),
        ],
    )
    def destroy(self, request, *args, **kwargs):
        """Destroy Agent Profile"""

        current_user = self.request.user
        agent_to_delete = self.get_object()
        user_to_delete = agent_to_delete.user  # Get the User instance

        if not current_user.is_superuser and current_user.id != agent_to_delete.user.id:
            return Response(
                {"error": "You are not authorized to delete this user."},
                status=status.HTTP_403_FORBIDDEN,
            )

        default_profile_image = "profile_images/default_profile.jpg"
        old_agent_image = None

        if (
            agent_to_delete.image_url
            and agent_to_delete.image_url.name != default_profile_image
        ):
            old_agent_image = os.path.join(
                settings.MEDIA_ROOT, agent_to_delete.image_url.name
            )

        response = super().destroy(request, *args, **kwargs)
        user_to_delete.delete()

        if old_agent_image and os.path.exists(old_agent_image):
            os.remove(old_agent_image)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            return Response(
                {"success": "Agent profile deleted successfully."},
                status=status.HTTP_200_OK,
            )

        return response
